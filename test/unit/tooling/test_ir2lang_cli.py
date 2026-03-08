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

import src.ir2lang as ir2lang_mod


class Ir2langCliTest(unittest.TestCase):
    def _write_east_json(self, root: Path, payload: dict[str, object], name: str = "input.json") -> Path:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def _write_linked_east_json(self, root: Path, module_id: str, *, name: str) -> Path:
        return self._write_east_json(
            root,
            {
                "kind": "Module",
                "east_stage": 3,
                "schema_version": 1,
                "meta": {
                    "dispatch_mode": "native",
                    "module_id": module_id,
                    "linked_program_v1": {
                        "program_id": "app.main",
                        "module_id": module_id,
                        "entry_modules": ["app.main"],
                        "type_id_resolved_v1": {},
                        "non_escape_summary": {},
                        "container_ownership_hints_v1": {},
                    },
                },
                "body": [],
            },
            name=name,
        )

    def test_missing_target_fails_fast(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_json = self._write_east_json(
                root,
                {"kind": "Module", "east_stage": 3, "schema_version": 1, "body": [], "meta": {}},
            )
            with patch.object(ir2lang_mod.sys, "argv", ["ir2lang.py", str(src_json)]):
                with self.assertRaises(SystemExit) as cm:
                    _ = ir2lang_mod.main()
        self.assertEqual(cm.exception.code, 2)

    def test_rejects_stage2_before_backend_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_json = self._write_east_json(
                root,
                {"kind": "Module", "east_stage": 2, "schema_version": 1, "body": [], "meta": {}},
            )
            with patch.object(
                ir2lang_mod,
                "get_backend_spec",
                side_effect=AssertionError("backend dispatch must not be called for EAST2 input"),
            ):
                with patch.object(
                    ir2lang_mod.sys,
                    "argv",
                    ["ir2lang.py", str(src_json), "--target", "rs"],
                ):
                    with self.assertRaises(SystemExit) as cm:
                        _ = ir2lang_mod.main()
        self.assertEqual(cm.exception.code, 2)

    def test_rejects_value_mutation_before_backend_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_json = self._write_east_json(
                root,
                {
                    "kind": "Module",
                    "east_stage": 3,
                    "schema_version": 1,
                    "meta": {"module_id": "pkg.main"},
                    "body": [
                        {
                            "kind": "FunctionDef",
                            "name": "py_join",
                            "arg_order": ["parts"],
                            "body": [
                                {
                                    "kind": "Expr",
                                    "value": {
                                        "kind": "Call",
                                        "func": {
                                            "kind": "Attribute",
                                            "value": {"kind": "Name", "id": "parts"},
                                            "attr": "append",
                                        },
                                        "args": [{"kind": "Constant", "value": "x"}],
                                        "keywords": [],
                                    },
                                }
                            ],
                            "meta": {
                                "runtime_abi_v1": {
                                    "schema_version": 1,
                                    "args": {"parts": "value_readonly"},
                                    "ret": "default",
                                }
                            },
                        }
                    ],
                },
            )
            with patch.object(
                ir2lang_mod,
                "get_backend_spec",
                side_effect=AssertionError("backend dispatch must not be called for invalid runtime_abi input"),
            ):
                with patch.object(
                    ir2lang_mod.sys,
                    "argv",
                    ["ir2lang.py", str(src_json), "--target", "rs"],
                ):
                    with self.assertRaises(RuntimeError) as cm:
                        _ = ir2lang_mod.main()
        self.assertIn("value parameter mutated", str(cm.exception))

    def test_rejects_runtime_abi_for_unsupported_target_before_backend_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_json = self._write_east_json(
                root,
                {
                    "kind": "Module",
                    "east_stage": 3,
                    "schema_version": 1,
                    "meta": {"module_id": "pkg.main"},
                    "body": [
                        {
                            "kind": "FunctionDef",
                            "name": "py_join",
                            "arg_order": ["parts"],
                            "body": [{"kind": "Return", "value": {"kind": "Constant", "value": ""}}],
                            "meta": {
                                "runtime_abi_v1": {
                                    "schema_version": 1,
                                    "args": {"parts": "value_readonly"},
                                    "ret": "value",
                                }
                            },
                        }
                    ],
                },
            )
            with patch.object(
                ir2lang_mod,
                "lower_ir",
                side_effect=AssertionError("backend dispatch must not be called for unsupported runtime_abi target"),
            ):
                with patch.object(
                    ir2lang_mod.sys,
                    "argv",
                    ["ir2lang.py", str(src_json), "--target", "rs"],
                ):
                    with self.assertRaises(RuntimeError) as cm:
                        _ = ir2lang_mod.main()
        self.assertIn("@abi is not supported for target rs", str(cm.exception))
        self.assertIn("pkg.main::py_join", str(cm.exception))

    def test_rejects_ambient_global_extern_for_unsupported_target_before_backend_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_json = self._write_east_json(
                root,
                {
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
                },
            )
            with patch.object(
                ir2lang_mod,
                "get_backend_spec",
                side_effect=AssertionError("backend dispatch must not be called for unsupported ambient extern target"),
            ):
                with patch.object(
                    ir2lang_mod.sys,
                    "argv",
                    ["ir2lang.py", str(src_json), "--target", "rs"],
                ):
                    with self.assertRaises(RuntimeError) as cm:
                        _ = ir2lang_mod.main()
        self.assertIn("ambient extern variables are not supported for target rs", str(cm.exception))
        self.assertIn("pkg.main::document -> document", str(cm.exception))

    def test_rejects_link_output_ambient_global_extern_for_unsupported_target_before_backend_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            main_src = root / "main.py"
            main_src.write_text("print(1)\n", encoding="utf-8")
            linked_main = self._write_east_json(
                root,
                {
                    "kind": "Module",
                    "east_stage": 3,
                    "schema_version": 1,
                    "meta": {
                        "dispatch_mode": "native",
                        "module_id": "app.main",
                        "linked_program_v1": {
                            "program_id": "app.main",
                            "module_id": "app.main",
                            "entry_modules": ["app.main"],
                            "type_id_resolved_v1": {},
                            "non_escape_summary": {},
                            "container_ownership_hints_v1": {},
                        },
                    },
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
                },
                name="linked/app/main.east3.json",
            )
            link_output = self._write_east_json(
                root,
                {
                    "schema": "pytra.link_output.v1",
                    "target": "rs",
                    "dispatch_mode": "native",
                    "entry_modules": ["app.main"],
                    "modules": [
                        {
                            "module_id": "app.main",
                            "input": "raw/app/main.east3.json",
                            "output": str(linked_main.relative_to(root)).replace("\\", "/"),
                            "source_path": str(main_src),
                            "is_entry": True,
                        }
                    ],
                    "global": {
                        "type_id_table": {},
                        "call_graph": {},
                        "sccs": [],
                        "non_escape_summary": {},
                        "container_ownership_hints_v1": {},
                    },
                    "diagnostics": {"warnings": [], "errors": []},
                },
                name="link-output.json",
            )
            with patch.object(
                ir2lang_mod,
                "get_backend_spec",
                side_effect=AssertionError("backend dispatch must not be called for unsupported ambient extern target"),
            ):
                with patch.object(
                    ir2lang_mod.sys,
                    "argv",
                    ["ir2lang.py", str(link_output), "--target", "rs"],
                ):
                    with self.assertRaises(RuntimeError) as cm:
                        _ = ir2lang_mod.main()
        self.assertIn("ambient extern variables are not supported for target rs", str(cm.exception))
        self.assertIn("app.main::document -> document", str(cm.exception))

    def test_accepts_wrapped_east_json_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_json = self._write_east_json(
                root,
                {
                    "ok": True,
                    "east": {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"module_id": "pkg.main"},
                        "body": [],
                    },
                },
            )
            out_rs = root / "out.rs"

            fake_spec = {
                "target_lang": "rs",
                "extension": ".rs",
                "default_options": {"lower": {}, "optimizer": {}, "emitter": {}},
                "option_schema": {"lower": {}, "optimizer": {}, "emitter": {}},
            }
            lower_calls: list[dict[str, object]] = []

            def _lower(spec: dict[str, object], east: dict[str, object], opts: dict[str, object]) -> dict[str, object]:
                lower_calls.append({"spec": spec, "east": east, "opts": opts})
                return {"kind": "LoweredModule"}

            with patch.object(ir2lang_mod.sys, "argv", ["ir2lang.py", str(src_json), "--target", "rs", "-o", str(out_rs)]):
                with patch.object(ir2lang_mod, "get_backend_spec", return_value=fake_spec):
                    with patch.object(ir2lang_mod, "resolve_layer_options", side_effect=lambda *_args, **_kw: {}):
                        with patch.object(ir2lang_mod, "lower_ir", side_effect=_lower):
                            with patch.object(ir2lang_mod, "optimize_ir", return_value={"kind": "OptimizedModule"}):
                                with patch.object(
                                    ir2lang_mod,
                                    "emit_module",
                                    return_value={
                                        "module_id": "pkg.main",
                                        "label": "out",
                                        "extension": ".rs",
                                        "text": "// wrapped east\n",
                                        "is_entry": True,
                                        "dependencies": [],
                                        "metadata": {},
                                    },
                                ):
                                    with patch.object(
                                        ir2lang_mod,
                                        "get_program_writer",
                                        return_value=lambda program_artifact, output_root, _options: (
                                            output_root.write_text(
                                                program_artifact["modules"][0]["text"],
                                                encoding="utf-8",
                                            ),
                                            {"primary_output": str(output_root)},
                                        )[1],
                                    ):
                                        with patch.object(ir2lang_mod, "apply_runtime_hook", return_value=None):
                                            rc = ir2lang_mod.main()

        self.assertEqual(rc, 0)
        self.assertEqual(len(lower_calls), 1)
        self.assertEqual(lower_calls[0]["east"]["kind"], "Module")
        self.assertEqual(lower_calls[0]["east"]["meta"]["module_id"], "pkg.main")

    def test_dispatches_target_and_layer_options(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_json = self._write_east_json(
                root,
                {"kind": "Module", "east_stage": 3, "schema_version": 1, "body": [], "meta": {}},
            )
            out_rs = root / "out.rs"

            fake_spec = {
                "target_lang": "rs",
                "extension": ".rs",
                "default_options": {"lower": {}, "optimizer": {}, "emitter": {}},
                "option_schema": {"lower": {}, "optimizer": {}, "emitter": {}},
            }

            resolve_calls: list[tuple[str, dict[str, str]]] = []
            lower_calls: list[dict[str, object]] = []
            optimize_calls: list[dict[str, object]] = []
            emit_calls: list[dict[str, object]] = []
            writer_calls: list[dict[str, object]] = []
            runtime_calls: list[Path] = []

            def _resolve(spec: dict[str, object], layer: str, raw: dict[str, str]) -> dict[str, object]:
                _ = spec
                resolve_calls.append((layer, dict(raw)))
                return {"layer": layer, "raw": dict(raw)}

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
                    "label": "out",
                    "extension": ".rs",
                    "text": "// emitted by ir2lang test\n",
                    "is_entry": is_entry,
                    "dependencies": [],
                    "metadata": {},
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
                "ir2lang.py",
                str(src_json),
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
            with patch.object(ir2lang_mod.sys, "argv", argv):
                with patch.object(ir2lang_mod, "get_backend_spec", return_value=fake_spec):
                        with patch.object(ir2lang_mod, "resolve_layer_options", side_effect=_resolve):
                            with patch.object(ir2lang_mod, "lower_ir", side_effect=_lower):
                                with patch.object(ir2lang_mod, "optimize_ir", side_effect=_optimize):
                                    with patch.object(ir2lang_mod, "emit_module", side_effect=_emit_module):
                                        with patch.object(ir2lang_mod, "get_program_writer", return_value=_writer):
                                            with patch.object(ir2lang_mod, "apply_runtime_hook", side_effect=_runtime):
                                                rc = ir2lang_mod.main()

            self.assertEqual(rc, 0)
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
            self.assertEqual(len(writer_calls), 1)
            self.assertEqual(len(runtime_calls), 1)
            self.assertEqual(str(runtime_calls[0]), str(out_rs))
            self.assertEqual(out_rs.read_text(encoding="utf-8"), "// emitted by ir2lang test\n")

    def test_no_runtime_hook_skips_runtime_copy(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_json = self._write_east_json(
                root,
                {"kind": "Module", "east_stage": 3, "schema_version": 1, "body": [], "meta": {}},
            )
            out_rs = root / "out.rs"

            fake_spec = {
                "target_lang": "rs",
                "extension": ".rs",
                "default_options": {"lower": {}, "optimizer": {}, "emitter": {}},
                "option_schema": {"lower": {}, "optimizer": {}, "emitter": {}},
            }

            runtime_calls: list[Path] = []
            writer_calls: list[Path] = []
            with patch.object(
                ir2lang_mod.sys,
                "argv",
                [
                    "ir2lang.py",
                    str(src_json),
                    "--target",
                    "rs",
                    "-o",
                    str(out_rs),
                    "--no-runtime-hook",
                ],
            ):
                with patch.object(ir2lang_mod, "get_backend_spec", return_value=fake_spec):
                    with patch.object(ir2lang_mod, "resolve_layer_options", side_effect=lambda *_args, **_kw: {}):
                        with patch.object(ir2lang_mod, "lower_ir", return_value={"kind": "LoweredModule"}):
                            with patch.object(ir2lang_mod, "optimize_ir", return_value={"kind": "OptimizedModule"}):
                                with patch.object(
                                    ir2lang_mod,
                                    "emit_module",
                                    return_value={
                                        "module_id": "out",
                                        "label": "out",
                                        "extension": ".rs",
                                        "text": "// no runtime\n",
                                        "is_entry": True,
                                        "dependencies": [],
                                        "metadata": {},
                                    },
                                ):
                                    with patch.object(
                                        ir2lang_mod,
                                        "get_program_writer",
                                        return_value=lambda program_artifact, output_root, _options: (
                                            writer_calls.append(output_root),
                                            output_root.write_text(
                                                program_artifact["modules"][0]["text"],
                                                encoding="utf-8",
                                            ),
                                            {"primary_output": str(output_root)},
                                        )[2],
                                    ):
                                        with patch.object(
                                            ir2lang_mod,
                                            "apply_runtime_hook",
                                            side_effect=lambda _spec, output_path: runtime_calls.append(output_path),
                                        ):
                                            rc = ir2lang_mod.main()

            self.assertEqual(rc, 0)
            self.assertEqual(runtime_calls, [])
            self.assertEqual([str(item) for item in writer_calls], [str(out_rs)])
            self.assertEqual(out_rs.read_text(encoding="utf-8"), "// no runtime\n")

    def test_link_output_input_uses_entry_module_for_single_file_backend(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            helper_src = root / "helper.py"
            main_src = root / "main.py"
            helper_src.write_text("x = 1\n", encoding="utf-8")
            main_src.write_text("print(1)\n", encoding="utf-8")
            linked_helper = self._write_linked_east_json(root, "app.helper", name="linked/app/helper.east3.json")
            linked_main = self._write_linked_east_json(root, "app.main", name="linked/app/main.east3.json")
            link_output = self._write_east_json(
                root,
                {
                    "schema": "pytra.link_output.v1",
                    "target": "rs",
                    "dispatch_mode": "native",
                    "entry_modules": ["app.main"],
                    "modules": [
                        {
                            "module_id": "app.helper",
                            "input": "raw/app/helper.east3.json",
                            "output": str(linked_helper.relative_to(root)).replace("\\", "/"),
                            "source_path": str(helper_src),
                            "is_entry": False,
                        },
                        {
                            "module_id": "app.main",
                            "input": "raw/app/main.east3.json",
                            "output": str(linked_main.relative_to(root)).replace("\\", "/"),
                            "source_path": str(main_src),
                            "is_entry": True,
                        },
                    ],
                    "global": {
                        "type_id_table": {},
                        "call_graph": {},
                        "sccs": [],
                        "non_escape_summary": {},
                        "container_ownership_hints_v1": {},
                    },
                    "diagnostics": {"warnings": [], "errors": []},
                },
                name="link-output.json",
            )
            out_rs = root / "out.rs"

            fake_spec = {
                "target_lang": "rs",
                "extension": ".rs",
                "default_options": {"lower": {}, "optimizer": {}, "emitter": {}},
                "option_schema": {"lower": {}, "optimizer": {}, "emitter": {}},
            }
            lower_calls: list[dict[str, object]] = []
            runtime_calls: list[Path] = []

            def _lower(spec: dict[str, object], east: dict[str, object], opts: dict[str, object]) -> dict[str, object]:
                lower_calls.append({"spec": spec, "east": east, "opts": opts})
                return {"kind": "LoweredModule"}

            with patch.object(
                ir2lang_mod.sys,
                "argv",
                ["ir2lang.py", str(link_output), "--target", "rs", "-o", str(out_rs)],
            ):
                with patch.object(ir2lang_mod, "get_backend_spec", return_value=fake_spec):
                    with patch.object(ir2lang_mod, "resolve_layer_options", side_effect=lambda *_args, **_kw: {}):
                        with patch.object(ir2lang_mod, "lower_ir", side_effect=_lower):
                            with patch.object(ir2lang_mod, "optimize_ir", return_value={"kind": "OptimizedModule"}):
                                with patch.object(
                                    ir2lang_mod,
                                    "emit_module",
                                    return_value={
                                        "module_id": "app.main",
                                        "label": "out",
                                        "extension": ".rs",
                                        "text": "// linked program\n",
                                        "is_entry": True,
                                        "dependencies": [],
                                        "metadata": {},
                                    },
                                ):
                                    with patch.object(
                                        ir2lang_mod,
                                        "get_program_writer",
                                        return_value=lambda program_artifact, output_root, _options: (
                                            output_root.write_text(
                                                program_artifact["modules"][0]["text"],
                                                encoding="utf-8",
                                            ),
                                            {"primary_output": str(output_root)},
                                        )[1],
                                    ):
                                        with patch.object(
                                            ir2lang_mod,
                                            "apply_runtime_hook",
                                            side_effect=lambda _spec, output_path: runtime_calls.append(output_path),
                                        ):
                                            rc = ir2lang_mod.main()

            self.assertEqual(rc, 0)
            self.assertEqual(len(lower_calls), 1)
            self.assertEqual(lower_calls[0]["east"]["meta"]["linked_program_v1"]["module_id"], "app.main")
            self.assertEqual([str(item) for item in runtime_calls], [str(out_rs)])
            self.assertEqual(out_rs.read_text(encoding="utf-8"), "// linked program\n")

    def test_link_output_input_for_cpp_uses_multi_file_writer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            helper_src = root / "helper.py"
            main_src = root / "main.py"
            helper_src.write_text("x = 1\n", encoding="utf-8")
            main_src.write_text("print(1)\n", encoding="utf-8")
            linked_helper = self._write_linked_east_json(root, "app.helper", name="linked/app/helper.east3.json")
            linked_main = self._write_linked_east_json(root, "app.main", name="linked/app/main.east3.json")
            link_output = self._write_east_json(
                root,
                {
                    "schema": "pytra.link_output.v1",
                    "target": "cpp",
                    "dispatch_mode": "native",
                    "entry_modules": ["app.main"],
                    "modules": [
                        {
                            "module_id": "app.helper",
                            "input": "raw/app/helper.east3.json",
                            "output": str(linked_helper.relative_to(root)).replace("\\", "/"),
                            "source_path": str(helper_src),
                            "is_entry": False,
                        },
                        {
                            "module_id": "app.main",
                            "input": "raw/app/main.east3.json",
                            "output": str(linked_main.relative_to(root)).replace("\\", "/"),
                            "source_path": str(main_src),
                            "is_entry": True,
                        },
                    ],
                    "global": {
                        "type_id_table": {},
                        "call_graph": {},
                        "sccs": [],
                        "non_escape_summary": {},
                        "container_ownership_hints_v1": {},
                    },
                    "diagnostics": {"warnings": [], "errors": []},
                },
                name="link-output.json",
            )
            out_dir = root / "cpp-out"
            fake_spec = {
                "target_lang": "cpp",
                "extension": ".cpp",
                "default_options": {"lower": {}, "optimizer": {}, "emitter": {}},
                "option_schema": {"lower": {}, "optimizer": {}, "emitter": {}},
            }

            with patch.object(
                ir2lang_mod.sys,
                "argv",
                ["ir2lang.py", str(link_output), "--target", "cpp", "--output-dir", str(out_dir)],
            ):
                with patch.object(ir2lang_mod, "get_backend_spec", return_value=fake_spec):
                    with patch.object(ir2lang_mod, "resolve_layer_options", side_effect=lambda *_args, **_kw: {}):
                        with patch.object(ir2lang_mod, "lower_ir", side_effect=AssertionError("unexpected lower_ir")):
                            with patch.object(ir2lang_mod, "optimize_ir", side_effect=AssertionError("unexpected optimize_ir")):
                                with patch.object(ir2lang_mod, "apply_runtime_hook", side_effect=AssertionError("unexpected runtime hook")):
                                    with patch.object(ir2lang_mod, "write_multi_file_cpp", return_value={"manifest": str(out_dir / "manifest.json")}) as writer:
                                        rc = ir2lang_mod.main()

            self.assertEqual(rc, 0)
            self.assertEqual(writer.call_count, 1)
            call_args = writer.call_args
            self.assertEqual(str(call_args.args[0]), str(main_src))
            self.assertEqual(str(call_args.args[2]), str(out_dir))
            module_map = call_args.args[1]
            self.assertEqual(set(module_map.keys()), {str(helper_src), str(main_src)})

    def test_link_output_input_for_cpp_preserves_helper_module_lane(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            main_src = root / "main.py"
            main_src.write_text("print(1)\n", encoding="utf-8")
            linked_helper = self._write_east_json(
                root,
                {
                    "kind": "Module",
                    "east_stage": 3,
                    "schema_version": 1,
                    "meta": {
                        "dispatch_mode": "native",
                        "module_id": "__pytra_helper__.cpp.demo",
                        "linked_program_v1": {
                            "program_id": "app.main",
                            "module_id": "__pytra_helper__.cpp.demo",
                            "entry_modules": ["app.main"],
                            "type_id_resolved_v1": {},
                            "non_escape_summary": {},
                            "container_ownership_hints_v1": {},
                        },
                        "synthetic_helper_v1": {
                            "helper_id": "cpp.demo",
                            "owner_module_id": "app.main",
                            "generated_by": "linked_optimizer",
                        },
                    },
                    "body": [],
                },
                name="linked/__pytra_helper__/cpp/demo.east3.json",
            )
            linked_main = self._write_linked_east_json(root, "app.main", name="linked/app/main.east3.json")
            link_output = self._write_east_json(
                root,
                {
                    "schema": "pytra.link_output.v1",
                    "target": "cpp",
                    "dispatch_mode": "native",
                    "entry_modules": ["app.main"],
                    "modules": [
                        {
                            "module_id": "__pytra_helper__.cpp.demo",
                            "input": "generated://cpp.demo",
                            "output": str(linked_helper.relative_to(root)).replace("\\", "/"),
                            "source_path": "",
                            "is_entry": False,
                            "module_kind": "helper",
                            "helper_id": "cpp.demo",
                            "owner_module_id": "app.main",
                            "generated_by": "linked_optimizer",
                        },
                        {
                            "module_id": "app.main",
                            "input": "raw/app/main.east3.json",
                            "output": str(linked_main.relative_to(root)).replace("\\", "/"),
                            "source_path": str(main_src),
                            "is_entry": True,
                        },
                    ],
                    "global": {
                        "type_id_table": {},
                        "call_graph": {},
                        "sccs": [],
                        "non_escape_summary": {},
                        "container_ownership_hints_v1": {},
                    },
                    "diagnostics": {"warnings": [], "errors": []},
                },
                name="link-output.json",
            )
            out_dir = root / "cpp-out"
            fake_spec = {
                "target_lang": "cpp",
                "extension": ".cpp",
                "default_options": {"lower": {}, "optimizer": {}, "emitter": {}},
                "option_schema": {"lower": {}, "optimizer": {}, "emitter": {}},
            }

            with patch.object(
                ir2lang_mod.sys,
                "argv",
                ["ir2lang.py", str(link_output), "--target", "cpp", "--output-dir", str(out_dir)],
            ):
                with patch.object(ir2lang_mod, "get_backend_spec", return_value=fake_spec):
                    with patch.object(ir2lang_mod, "resolve_layer_options", side_effect=lambda *_args, **_kw: {}):
                        with patch.object(ir2lang_mod, "lower_ir", side_effect=AssertionError("unexpected lower_ir")):
                            with patch.object(ir2lang_mod, "optimize_ir", side_effect=AssertionError("unexpected optimize_ir")):
                                with patch.object(ir2lang_mod, "apply_runtime_hook", side_effect=AssertionError("unexpected runtime hook")):
                                    with patch.object(ir2lang_mod, "write_multi_file_cpp", return_value={"manifest": str(out_dir / "manifest.json")}) as writer:
                                        rc = ir2lang_mod.main()

            self.assertEqual(rc, 0)
            self.assertEqual(writer.call_count, 1)
            call_args = writer.call_args
            self.assertEqual(str(call_args.args[0]), str(main_src))
            module_map = call_args.args[1]
            self.assertIn(str(main_src), module_map)
            self.assertIn("__pytra_helper__.cpp.demo.py", module_map)
            self.assertEqual(module_map["__pytra_helper__.cpp.demo.py"]["meta"]["synthetic_helper_v1"]["helper_id"], "cpp.demo")

    def test_ir2lang_flattens_helper_modules_into_program_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_json = self._write_east_json(
                root,
                {
                    "kind": "Module",
                    "east_stage": 3,
                    "schema_version": 1,
                    "body": [],
                    "meta": {"module_id": "pkg.main"},
                },
            )
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

            with patch.object(ir2lang_mod.sys, "argv", ["ir2lang.py", str(src_json), "--target", "rs", "-o", str(out_rs)]):
                with patch.object(ir2lang_mod, "get_backend_spec", return_value=fake_spec):
                    with patch.object(ir2lang_mod, "resolve_layer_options", side_effect=lambda *_args, **_kw: {}):
                        with patch.object(ir2lang_mod, "lower_ir", return_value={"kind": "LoweredModule"}):
                            with patch.object(ir2lang_mod, "optimize_ir", return_value={"kind": "OptimizedModule"}):
                                with patch.object(
                                    ir2lang_mod,
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
                                    with patch.object(ir2lang_mod, "get_program_writer", return_value=_writer):
                                        with patch.object(ir2lang_mod, "apply_runtime_hook", return_value=None):
                                            rc = ir2lang_mod.main()

        self.assertEqual(rc, 0)
        self.assertEqual(len(writer_calls), 1)
        modules = writer_calls[0]["program_artifact"]["modules"]
        self.assertEqual(len(modules), 2)
        self.assertEqual(modules[0]["kind"], "user")
        self.assertEqual(modules[1]["kind"], "helper")
        self.assertEqual(modules[1]["metadata"]["helper_id"], "rs.demo")


if __name__ == "__main__":
    unittest.main()
