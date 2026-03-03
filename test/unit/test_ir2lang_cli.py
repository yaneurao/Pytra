from __future__ import annotations

import json
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

import src.ir2lang as ir2lang_mod


class Ir2langCliTest(unittest.TestCase):
    def _write_east_json(self, root: Path, payload: dict[str, object], name: str = "input.json") -> Path:
        path = root / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

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

            def _emit(
                spec: dict[str, object],
                ir: dict[str, object],
                output_path: Path,
                opts: dict[str, object],
            ) -> str:
                emit_calls.append({"spec": spec, "ir": ir, "output_path": output_path, "opts": opts})
                return "// emitted by ir2lang test\n"

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
                                with patch.object(ir2lang_mod, "emit_source", side_effect=_emit):
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
                                with patch.object(ir2lang_mod, "emit_source", return_value="// no runtime\n"):
                                    with patch.object(
                                        ir2lang_mod,
                                        "apply_runtime_hook",
                                        side_effect=lambda _spec, output_path: runtime_calls.append(output_path),
                                    ):
                                        rc = ir2lang_mod.main()

            self.assertEqual(rc, 0)
            self.assertEqual(runtime_calls, [])
            self.assertEqual(out_rs.read_text(encoding="utf-8"), "// no runtime\n")


if __name__ == "__main__":
    unittest.main()
