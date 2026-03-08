from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import src.py2x as py2x_mod
from src.toolchain.link.program_model import LinkedProgramModule


class Py2xCliTest(unittest.TestCase):
    def test_build_linked_program_for_json_link_input_uses_loader(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            link_input = root / "link-input.json"
            link_input.write_text(json.dumps({"schema": "pytra.link_input.v1"}, ensure_ascii=False), encoding="utf-8")
            sentinel = object()
            with patch.object(py2x_mod, "load_linked_program", return_value=sentinel) as load_program:
                with patch.object(
                    py2x_mod,
                    "load_east3_document",
                    side_effect=AssertionError("raw EAST3 loader must not run for link-input restart"),
                ):
                    program = py2x_mod._build_linked_program_for_input(
                        link_input,
                        parser_backend="self_hosted",
                        object_dispatch_mode="native",
                        east3_opt_level="1",
                        east3_opt_pass="",
                        dump_east3_before_opt="",
                        dump_east3_after_opt="",
                        dump_east3_opt_trace="",
                        target_lang="cpp",
                    )
        self.assertIs(program, sentinel)
        load_program.assert_called_once_with(link_input)

    def test_missing_target_fails_fast(self) -> None:
        fixture = ROOT / "test" / "fixtures" / "core" / "add.py"
        with patch.object(py2x_mod.sys, "argv", ["py2x.py", str(fixture)]):
            with self.assertRaises(SystemExit) as cm:
                _ = py2x_mod.main()
        self.assertEqual(cm.exception.code, 2)

    def test_rejects_stage2_before_backend_pipeline(self) -> None:
        fixture = ROOT / "test" / "fixtures" / "core" / "add.py"
        with patch.object(
            py2x_mod,
            "load_east3_document",
            side_effect=AssertionError("load_east3_document must not be called for stage2"),
        ):
            with patch.object(
                py2x_mod.sys,
                "argv",
                ["py2x.py", str(fixture), "--target", "rs", "--east-stage", "2"],
            ):
                with self.assertRaises(SystemExit) as cm:
                    _ = py2x_mod.main()
        self.assertEqual(cm.exception.code, 2)

    def test_rejects_ambient_global_extern_for_unsupported_target_before_backend_dispatch(self) -> None:
        fixture = ROOT / "test" / "fixtures" / "core" / "add.py"
        ambient_module = type(
            "AmbientModule",
            (),
            {
                "east_doc": {
                    "kind": "Module",
                    "east_stage": 3,
                    "schema_version": 1,
                    "meta": {"module_id": "pkg.main"},
                    "body": [
                        {
                            "kind": "AnnAssign",
                            "target": {"kind": "Name", "id": "document"},
                            "annotation": {"kind": "Name", "id": "Any"},
                            "value": {
                                "kind": "Call",
                                "func": {"kind": "Name", "id": "extern"},
                                "args": [],
                                "keywords": [],
                            },
                            "meta": {
                                "extern_var_v1": {
                                    "schema_version": 1,
                                    "symbol": "document",
                                    "same_name": 1,
                                }
                            },
                        }
                    ],
                }
            },
        )()
        fake_program = type("AmbientProgram", (), {"modules": (ambient_module,)})()
        with patch.object(py2x_mod, "_build_linked_program_for_input", return_value=fake_program):
            with patch.object(
                py2x_mod,
                "get_backend_spec",
                side_effect=AssertionError("backend dispatch must not be called for unsupported ambient extern target"),
            ):
                with patch.object(
                    py2x_mod.sys,
                    "argv",
                    ["py2x.py", str(fixture), "--target", "rs"],
                ):
                    with self.assertRaises(RuntimeError) as cm:
                        _ = py2x_mod.main()
        self.assertIn("ambient extern variables are not supported for target rs", str(cm.exception))
        self.assertIn("pkg.main::document -> document", str(cm.exception))

    def test_dispatches_target_and_propagates_layer_options(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_py = root / "case.py"
            helper_py = root / "helper.py"
            out_rs = root / "case.rs"
            src_py.write_text("x: int = 1\nprint(x)\n", encoding="utf-8")
            helper_py.write_text("y: int = 2\n", encoding="utf-8")

            fake_spec = {
                "target_lang": "rs",
                "extension": ".rs",
                "default_options": {"lower": {}, "optimizer": {}, "emitter": {}},
                "option_schema": {"lower": {}, "optimizer": {}, "emitter": {}},
            }
            resolve_calls: list[tuple[str, dict[str, str]]] = []
            build_calls: list[dict[str, object]] = []
            lower_calls: list[dict[str, object]] = []
            optimize_calls: list[dict[str, object]] = []
            emit_calls: list[dict[str, object]] = []
            program_calls: list[dict[str, object]] = []
            writer_calls: list[dict[str, object]] = []
            runtime_calls: list[Path] = []

            main_east = {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {"dispatch_mode": "native", "module_id": "app.case"},
                "body": [{"kind": "Pass"}],
            }
            helper_east = {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {"dispatch_mode": "native", "module_id": "app.helper"},
                "body": [],
            }

            def _resolve(spec: dict[str, object], layer: str, raw: dict[str, str]) -> dict[str, object]:
                resolve_calls.append((layer, dict(raw)))
                return {"layer": layer, "raw": dict(raw)}

            def _build_module_map(
                entry_path: Path,
                load_east_fn: object,
                parser_backend: str = "self_hosted",
                east_stage: str = "3",
                object_dispatch_mode: str = "",
            ) -> dict[str, dict[str, object]]:
                build_calls.append(
                    {
                        "entry_path": entry_path,
                        "load_east_fn": load_east_fn,
                        "parser_backend": parser_backend,
                        "east_stage": east_stage,
                        "object_dispatch_mode": object_dispatch_mode,
                    }
                )
                return {
                    str(helper_py.resolve()): dict(helper_east),
                    str(src_py.resolve()): dict(main_east),
                }

            def _lower(spec: dict[str, object], east: dict[str, object], opts: dict[str, object]) -> dict[str, object]:
                lower_calls.append({"spec": spec, "east": east, "opts": opts})
                return {"kind": "LoweredModule"}

            def _optimize(spec: dict[str, object], ir: dict[str, object], opts: dict[str, object]) -> dict[str, object]:
                optimize_calls.append({"spec": spec, "ir": ir, "opts": opts})
                return {"kind": "OptimizedModule"}

            def _emit_module(
                spec: dict[str, object],
                ir: dict[str, object],
                output_path: Path,
                opts: dict[str, object],
                *,
                module_id: str = "",
                is_entry: bool = False,
            ) -> dict[str, object]:
                emit_calls.append(
                    {
                        "spec": spec,
                        "ir": ir,
                        "output_path": output_path,
                        "opts": opts,
                        "module_id": module_id,
                        "is_entry": is_entry,
                    }
                )
                return {
                    "module_id": module_id,
                    "label": "case",
                    "extension": ".rs",
                    "text": "// emitted by test\n",
                    "is_entry": is_entry,
                    "dependencies": [],
                    "metadata": {},
                }

            def _build_program(
                spec: dict[str, object],
                modules: list[dict[str, object]],
                *,
                program_id: str = "",
                entry_modules: list[str] | None = None,
                layout_mode: str = "single_file",
                link_output_schema: str = "",
                writer_options: dict[str, object] | None = None,
            ) -> dict[str, object]:
                program_calls.append(
                    {
                        "spec": spec,
                        "modules": modules,
                        "program_id": program_id,
                        "entry_modules": list(entry_modules or []),
                        "layout_mode": layout_mode,
                        "link_output_schema": link_output_schema,
                        "writer_options": dict(writer_options or {}),
                    }
                )
                return {
                    "modules": modules,
                    "program_id": program_id,
                    "entry_modules": list(entry_modules or []),
                }

            def _writer(program_artifact: dict[str, object], output_root: Path, options: dict[str, object]) -> dict[str, object]:
                writer_calls.append(
                    {
                        "program_artifact": program_artifact,
                        "output_root": output_root,
                        "options": options,
                    }
                )
                output_root.parent.mkdir(parents=True, exist_ok=True)
                modules = program_artifact.get("modules", [])
                text = modules[0].get("text", "") if isinstance(modules, list) and len(modules) > 0 else ""
                output_root.write_text(text if isinstance(text, str) else "", encoding="utf-8")
                return {"primary_output": str(output_root)}

            def _runtime(spec: dict[str, object], output_path: Path) -> None:
                _ = spec
                runtime_calls.append(output_path)

            argv = [
                "py2x.py",
                str(src_py),
                "--target",
                "rs",
                "-o",
                str(out_rs),
                "--lower-option",
                "lopt=1",
                "--optimizer-option",
                "oopt=true",
                "--emitter-option",
                "eopt=alpha",
            ]
            with patch.object(py2x_mod.sys, "argv", argv):
                with patch.object(py2x_mod, "get_backend_spec", return_value=fake_spec):
                    with patch.object(py2x_mod, "resolve_layer_options", side_effect=_resolve):
                        with patch.object(py2x_mod, "build_module_east_map", side_effect=_build_module_map):
                            with patch.object(py2x_mod, "lower_ir", side_effect=_lower):
                                with patch.object(py2x_mod, "optimize_ir", side_effect=_optimize):
                                    with patch.object(py2x_mod, "emit_module", side_effect=_emit_module):
                                        with patch.object(py2x_mod, "build_program_artifact", side_effect=_build_program):
                                            with patch.object(py2x_mod, "get_program_writer", return_value=_writer):
                                                with patch.object(py2x_mod, "apply_runtime_hook", side_effect=_runtime):
                                                    rc = py2x_mod.main()
            out_exists = out_rs.exists()
            out_text = out_rs.read_text(encoding="utf-8") if out_exists else ""

        self.assertEqual(rc, 0)
        self.assertEqual(len(build_calls), 1)
        self.assertEqual(str(build_calls[0]["entry_path"]), str(src_py))
        self.assertEqual(build_calls[0]["east_stage"], "3")
        self.assertEqual(build_calls[0]["object_dispatch_mode"], "native")
        self.assertEqual(
            resolve_calls,
            [
                ("lower", {"lopt": "1"}),
                ("optimizer", {"oopt": "true"}),
                ("emitter", {"eopt": "alpha"}),
            ],
        )
        self.assertEqual(len(lower_calls), 1)
        self.assertEqual(len(optimize_calls), 1)
        self.assertEqual(len(emit_calls), 1)
        self.assertEqual(len(program_calls), 1)
        self.assertEqual(len(writer_calls), 1)
        self.assertEqual(len(runtime_calls), 1)
        self.assertEqual(lower_calls[0]["east"]["meta"]["module_id"], "app.case")
        self.assertEqual(lower_calls[0]["opts"], {"layer": "lower", "raw": {"lopt": "1"}})
        self.assertEqual(optimize_calls[0]["opts"], {"layer": "optimizer", "raw": {"oopt": "true"}})
        self.assertEqual(emit_calls[0]["opts"], {"layer": "emitter", "raw": {"eopt": "alpha"}})
        self.assertEqual(emit_calls[0]["module_id"], "app.case")
        self.assertTrue(emit_calls[0]["is_entry"])
        self.assertEqual(program_calls[0]["program_id"], "app.case")
        self.assertEqual(program_calls[0]["entry_modules"], ["app.case"])
        self.assertEqual(str(writer_calls[0]["output_root"]), str(out_rs))
        self.assertEqual(str(runtime_calls[0]), str(out_rs))
        self.assertTrue(out_exists)
        self.assertIn("emitted by test", out_text)

    def test_cpp_target_uses_py2cpp_compat_path(self) -> None:
        fixture = ROOT / "test" / "fixtures" / "core" / "add.py"
        with patch.object(py2x_mod.sys, "argv", ["py2x.py", str(fixture), "--target", "cpp", "--multi-file"]):
            with patch.object(py2x_mod, "_invoke_py2cpp_main", return_value=0) as invoke:
                rc = py2x_mod.main()
        self.assertEqual(rc, 0)
        self.assertEqual(invoke.call_count, 1)
        forwarded = invoke.call_args[0][0]
        self.assertIn(str(fixture), forwarded)
        self.assertIn("--multi-file", forwarded)
        self.assertNotIn("--target", forwarded)

    def test_py2x_flattens_helper_modules_into_program_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_py = root / "main.py"
            src_py.write_text("print(1)\n", encoding="utf-8")
            out_rs = root / "out.rs"

            fake_spec = {
                "target_lang": "rs",
                "extension": ".rs",
                "default_options": {"lower": {}, "optimizer": {}, "emitter": {}},
                "option_schema": {"lower": {}, "optimizer": {}, "emitter": {}},
            }
            writer_calls: list[dict[str, object]] = []

            def _writer(program_artifact: dict[str, object], output_root: Path, _options: dict[str, object]) -> dict[str, object]:
                writer_calls.append({"program_artifact": program_artifact, "output_root": output_root})
                output_root.write_text("// main\n", encoding="utf-8")
                return {"primary_output": str(output_root)}

            with patch.object(py2x_mod.sys, "argv", ["py2x.py", str(src_py), "--target", "rs", "-o", str(out_rs)]):
                with patch.object(py2x_mod, "get_backend_spec", return_value=fake_spec):
                    with patch.object(py2x_mod, "resolve_layer_options", side_effect=lambda *_args, **_kw: {}):
                        with patch.object(
                            py2x_mod,
                            "_build_linked_program_for_input",
                            return_value=py2x_mod.LinkedProgram(
                                schema="pytra.link_input.v1",
                                manifest_path=None,
                                target="rs",
                                dispatch_mode="native",
                                entry_modules=("pkg.main",),
                                modules=(
                                    LinkedProgramModule(
                                        module_id="pkg.main",
                                        source_path=str(src_py),
                                        is_entry=True,
                                        east_doc={
                                            "kind": "Module",
                                            "east_stage": 3,
                                            "schema_version": 1,
                                            "meta": {"module_id": "pkg.main"},
                                            "body": [],
                                        },
                                    ),
                                ),
                                options={},
                            ),
                        ):
                            with patch.object(py2x_mod, "lower_ir", return_value={"kind": "LoweredModule"}):
                                with patch.object(py2x_mod, "optimize_ir", return_value={"kind": "OptimizedModule"}):
                                    with patch.object(
                                        py2x_mod,
                                        "emit_module",
                                        return_value={
                                            "module_id": "pkg.main",
                                            "kind": "user",
                                            "label": "main",
                                            "extension": ".rs",
                                            "text": "// main\n",
                                            "is_entry": True,
                                            "dependencies": [],
                                            "metadata": {},
                                            "helper_modules": [
                                                {
                                                    "module_id": "__pytra_helper__.rs.demo",
                                                    "label": "demo_helper",
                                                    "extension": ".rs",
                                                    "text": "// helper\n",
                                                    "is_entry": False,
                                                    "dependencies": [],
                                                    "metadata": {"helper_id": "rs.demo", "owner_module_id": "pkg.main"},
                                                }
                                            ],
                                        },
                                    ):
                                        with patch.object(py2x_mod, "get_program_writer", return_value=_writer):
                                            with patch.object(py2x_mod, "apply_runtime_hook", return_value=None):
                                                rc = py2x_mod.main()

        self.assertEqual(rc, 0)
        self.assertEqual(len(writer_calls), 1)
        modules = writer_calls[0]["program_artifact"]["modules"]
        self.assertEqual(len(modules), 2)
        self.assertEqual(modules[0]["kind"], "user")
        self.assertEqual(modules[1]["kind"], "helper")
        self.assertEqual(modules[1]["metadata"]["owner_module_id"], "pkg.main")

    def test_cpp_target_maps_layer_options_to_cpp_flags(self) -> None:
        fixture = ROOT / "test" / "fixtures" / "core" / "add.py"
        argv = [
            "py2x.py",
            str(fixture),
            "--target",
            "cpp",
            "--optimizer-option",
            "cpp_opt_level=2",
            "--emitter-option",
            "mod_mode=python",
            "--emitter-option",
            "negative_index_mode=always",
        ]
        with patch.object(py2x_mod.sys, "argv", argv):
            with patch.object(py2x_mod, "_invoke_py2cpp_main", return_value=0) as invoke:
                rc = py2x_mod.main()
        self.assertEqual(rc, 0)
        forwarded = invoke.call_args[0][0]
        self.assertIn("--cpp-opt-level", forwarded)
        self.assertIn("2", forwarded)
        self.assertIn("--mod-mode", forwarded)
        self.assertIn("python", forwarded)
        self.assertIn("--negative-index-mode", forwarded)
        self.assertIn("always", forwarded)
        self.assertNotIn("--optimizer-option", forwarded)
        self.assertNotIn("--emitter-option", forwarded)

    def test_json_input_skips_module_map_builder(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_json = root / "case.east3.json"
            out_rs = root / "case.rs"
            src_json.write_text("{}", encoding="utf-8")

            fake_spec = {
                "target_lang": "rs",
                "extension": ".rs",
                "default_options": {"lower": {}, "optimizer": {}, "emitter": {}},
                "option_schema": {"lower": {}, "optimizer": {}, "emitter": {}},
            }

            argv = ["py2x.py", str(src_json), "--target", "rs", "-o", str(out_rs)]
            east_doc = {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {"dispatch_mode": "native", "module_id": "app.case"},
                "body": [],
            }

            def _writer(program_artifact: dict[str, object], output_root: Path, options: dict[str, object]) -> dict[str, object]:
                _ = options
                output_root.parent.mkdir(parents=True, exist_ok=True)
                modules = program_artifact.get("modules", [])
                text = modules[0].get("text", "") if isinstance(modules, list) and len(modules) > 0 else ""
                output_root.write_text(text if isinstance(text, str) else "", encoding="utf-8")
                return {"primary_output": str(output_root)}

            with patch.object(py2x_mod.sys, "argv", argv):
                with patch.object(py2x_mod, "get_backend_spec", return_value=fake_spec):
                    with patch.object(py2x_mod, "build_module_east_map", side_effect=AssertionError("unexpected module-map build")):
                        with patch.object(py2x_mod, "load_east3_document", return_value=east_doc):
                            with patch.object(py2x_mod, "lower_ir", return_value={"kind": "LoweredModule"}) as lower:
                                with patch.object(py2x_mod, "optimize_ir", return_value={"kind": "OptimizedModule"}):
                                    with patch.object(
                                        py2x_mod,
                                        "emit_module",
                                        return_value={
                                            "module_id": "app.case",
                                            "label": "case",
                                            "extension": ".rs",
                                            "text": "// json route\n",
                                            "is_entry": True,
                                            "dependencies": [],
                                            "metadata": {},
                                        },
                                    ):
                                        with patch.object(py2x_mod, "build_program_artifact", return_value={"modules": [{"text": "// json route\n"}]}):
                                            with patch.object(py2x_mod, "get_program_writer", return_value=_writer):
                                                with patch.object(py2x_mod, "apply_runtime_hook"):
                                                    rc = py2x_mod.main()

        self.assertEqual(rc, 0)
        self.assertEqual(lower.call_args[0][1]["meta"]["module_id"], "app.case")

    def test_dump_east3_dir_writes_link_input_bundle_without_backend_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            dump_dir = root / "dump"
            main_py.write_text("import helper\nprint(1)\n", encoding="utf-8")
            helper_py.write_text("x: int = 1\n", encoding="utf-8")

            main_east = {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {"dispatch_mode": "native", "module_id": "app.main"},
                "body": [],
            }
            helper_east = {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {"dispatch_mode": "native", "module_id": "app.helper"},
                "body": [],
            }

            argv = [
                "py2x.py",
                str(main_py),
                "--target",
                "cpp",
                "--dump-east3-dir",
                str(dump_dir),
            ]
            with patch.object(py2x_mod.sys, "argv", argv):
                with patch.object(
                    py2x_mod,
                    "build_module_east_map",
                    return_value={
                        str(helper_py.resolve()): dict(helper_east),
                        str(main_py.resolve()): dict(main_east),
                    },
                ):
                    with patch.object(py2x_mod, "_invoke_py2cpp_main", side_effect=AssertionError("unexpected compat route")):
                        with patch.object(py2x_mod, "get_backend_spec", side_effect=AssertionError("unexpected backend dispatch")):
                            rc = py2x_mod.main()

            self.assertEqual(rc, 0)
            link_input = dump_dir / "link-input.json"
            self.assertTrue(link_input.exists())
            self.assertTrue((dump_dir / "raw" / "app" / "main.east3.json").exists())
            self.assertTrue((dump_dir / "raw" / "app" / "helper.east3.json").exists())

    def test_link_only_writes_link_output_bundle_without_backend_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            main_py = root / "main.py"
            helper_py = root / "helper.py"
            out_dir = root / "linked"
            main_py.write_text("import helper\nprint(1)\n", encoding="utf-8")
            helper_py.write_text("x: int = 1\n", encoding="utf-8")

            main_east = {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {"dispatch_mode": "native", "module_id": "app.main"},
                "body": [],
            }
            helper_east = {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {"dispatch_mode": "native", "module_id": "app.helper"},
                "body": [],
            }

            argv = [
                "py2x.py",
                str(main_py),
                "--target",
                "cpp",
                "--link-only",
                "--output-dir",
                str(out_dir),
            ]
            with patch.object(py2x_mod.sys, "argv", argv):
                with patch.object(
                    py2x_mod,
                    "build_module_east_map",
                    return_value={
                        str(helper_py.resolve()): dict(helper_east),
                        str(main_py.resolve()): dict(main_east),
                    },
                ):
                    with patch.object(py2x_mod, "_invoke_py2cpp_main", side_effect=AssertionError("unexpected compat route")):
                        with patch.object(py2x_mod, "get_backend_spec", side_effect=AssertionError("unexpected backend dispatch")):
                            rc = py2x_mod.main()

            self.assertEqual(rc, 0)
            self.assertTrue((out_dir / "link-output.json").exists())
            self.assertTrue((out_dir / "linked" / "app" / "main.east3.json").exists())
            self.assertTrue((out_dir / "linked" / "app" / "helper.east3.json").exists())

    def test_from_link_output_delegates_to_ir2lang_restart_route(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            link_output = root / "link-output.json"
            out_dir = root / "out"
            link_output.write_text("{}", encoding="utf-8")
            argv = [
                "py2x.py",
                str(link_output),
                "--target",
                "cpp",
                "--from-link-output",
                "--output-dir",
                str(out_dir),
                "--optimizer-option",
                "pass=1",
            ]
            with patch.object(py2x_mod.sys, "argv", argv):
                with patch.object(py2x_mod, "_invoke_ir2lang_main", return_value=0) as invoke:
                    rc = py2x_mod.main()

        self.assertEqual(rc, 0)
        forwarded = invoke.call_args[0][0]
        self.assertEqual(forwarded[0], str(link_output))
        self.assertIn("--target", forwarded)
        self.assertIn("cpp", forwarded)
        self.assertIn("--output-dir", forwarded)
        self.assertIn(str(out_dir), forwarded)
        self.assertIn("--optimizer-option", forwarded)
        self.assertIn("pass=1", forwarded)


if __name__ == "__main__":
    unittest.main()
