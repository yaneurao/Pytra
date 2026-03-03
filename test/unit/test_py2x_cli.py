from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import src.py2x as py2x_mod


class Py2xCliTest(unittest.TestCase):
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

    def test_dispatches_target_and_propagates_layer_options(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src_py = root / "case.py"
            out_rs = root / "case.rs"
            src_py.write_text("x: int = 1\nprint(x)\n", encoding="utf-8")

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
            runtime_calls: list[Path] = []

            def _resolve(spec: dict[str, object], layer: str, raw: dict[str, str]) -> dict[str, object]:
                resolve_calls.append((layer, dict(raw)))
                return {"layer": layer, "raw": dict(raw)}

            def _lower(spec: dict[str, object], east: dict[str, object], opts: dict[str, object]) -> dict[str, object]:
                lower_calls.append({"spec": spec, "east": east, "opts": opts})
                return {"kind": "LoweredModule"}

            def _optimize(spec: dict[str, object], ir: dict[str, object], opts: dict[str, object]) -> dict[str, object]:
                optimize_calls.append({"spec": spec, "ir": ir, "opts": opts})
                return {"kind": "OptimizedModule"}

            def _emit(
                spec: dict[str, object],
                ir: dict[str, object],
                output_path: Path,
                opts: dict[str, object],
            ) -> str:
                emit_calls.append({"spec": spec, "ir": ir, "output_path": output_path, "opts": opts})
                return "// emitted by test\n"

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
                        with patch.object(py2x_mod, "load_east3_document", return_value={"kind": "Module", "east_stage": 3}):
                            with patch.object(py2x_mod, "lower_ir", side_effect=_lower):
                                with patch.object(py2x_mod, "optimize_ir", side_effect=_optimize):
                                    with patch.object(py2x_mod, "emit_source", side_effect=_emit):
                                        with patch.object(py2x_mod, "apply_runtime_hook", side_effect=_runtime):
                                            rc = py2x_mod.main()
            out_exists = out_rs.exists()
            out_text = out_rs.read_text(encoding="utf-8") if out_exists else ""

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
        self.assertEqual(len(runtime_calls), 1)
        self.assertEqual(lower_calls[0]["opts"], {"layer": "lower", "raw": {"lopt": "1"}})
        self.assertEqual(optimize_calls[0]["opts"], {"layer": "optimizer", "raw": {"oopt": "true"}})
        self.assertEqual(emit_calls[0]["opts"], {"layer": "emitter", "raw": {"eopt": "alpha"}})
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


if __name__ == "__main__":
    unittest.main()
