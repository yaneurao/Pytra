from __future__ import annotations

import importlib.util
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

MODULE_PATH = ROOT / "src" / "toolchain" / "emit" / "go" / "cli.py"


def _work_tmp_dir() -> tempfile.TemporaryDirectory[str]:
    base = ROOT / "work" / "tmp" / "unittest"
    base.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=base)


def _load_module():
    spec = importlib.util.spec_from_file_location("toolchain_emit_go_cli", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load Go emitter CLI module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GoEmitterCliSelfhostTest(unittest.TestCase):
    def test_parse_args_accepts_pytra_cli_emit_shape(self) -> None:
        mod = _load_module()

        self.assertEqual(
            mod._parse_args(["-emit", "linked", "-o", "out", "--target", "go"]),
            ("linked", "out", "", "go"),
        )

    def test_main_rejects_non_go_emit_target(self) -> None:
        mod = _load_module()

        self.assertEqual(mod.main(["-emit", "linked", "--target", "cpp"]), 1)

    def test_main_reads_single_east3_json_and_writes_go_file(self) -> None:
        mod = _load_module()
        with _work_tmp_dir() as td:
            root = Path(td)
            east_path = root / "app.main.east3.json"
            out_dir = root / "out"
            east_path.write_text(
                json.dumps(
                    {
                        "kind": "Module",
                        "east_stage": 3,
                        "schema_version": 1,
                        "meta": {"module_id": "app.main"},
                        "body": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.object(mod, "emit_go_module", return_value="// emitted\n") as emit, \
                patch.object(mod, "_copy_go_runtime_files", return_value=0):
                rc = mod.main([str(east_path), "-o", str(out_dir)])

            self.assertEqual(rc, 0)
            self.assertEqual((out_dir / "app_main.go").read_text(encoding="utf-8"), "// emitted\n")
            emit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
