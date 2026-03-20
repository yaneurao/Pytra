from __future__ import annotations

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_jsonvalue_decode_boundaries as guard_mod


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class JsonValueDecodeBoundaryGuardTest(unittest.TestCase):
    def test_target_files_cover_compiler_internal_json_loaders(self) -> None:
        self.assertIn("src/toolchain/frontends/transpile_cli.py", guard_mod.TARGET_FILES)
        self.assertIn("src/toolchain/frontends/runtime_symbol_index.py", guard_mod.TARGET_FILES)
        self.assertIn("src/toolchain/emit/common/emitter/code_emitter.py", guard_mod.TARGET_FILES)
        self.assertIn("src/toolchain/emit/js/emitter/js_emitter.py", guard_mod.TARGET_FILES)

    def test_collect_passes_when_targets_use_loads_obj(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            targets = ["src/a.py", "src/b.py"]
            for rel in targets:
                _write(root / rel, "from pytra.std import json\npayload = json.loads_obj(text)\n")
            with patch.object(guard_mod, "TARGET_FILES", targets):
                findings = guard_mod._collect_findings(root)
        self.assertEqual(findings, [])

    def test_collect_detects_raw_json_loads(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            targets = ["src/a.py"]
            _write(root / "src/a.py", "from pytra.std import json\npayload = json.loads(text)\n")
            with patch.object(guard_mod, "TARGET_FILES", targets):
                findings = guard_mod._collect_findings(root)
        self.assertEqual([item.key for item in findings], ["src/a.py:missing_loads_obj", "src/a.py:raw_json_loads"])

    def test_main_passes_for_allowable_tree(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            targets = ["src/a.py"]
            _write(root / "src/a.py", "from pytra.std import json\npayload = json.loads_obj(text)\n")
            with patch.object(guard_mod, "ROOT", root), patch.object(guard_mod, "TARGET_FILES", targets), patch.object(
                sys, "argv", ["check_jsonvalue_decode_boundaries.py"]
            ), patch("sys.stdout", new_callable=io.StringIO) as buf:
                rc = guard_mod.main()
        self.assertEqual(rc, 0)
        self.assertIn("[OK] jsonvalue decode boundary guard passed", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
