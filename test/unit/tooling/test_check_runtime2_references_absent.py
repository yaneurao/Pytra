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

from tools import check_runtime2_references_absent as guard_mod


class CheckRuntime2ReferencesAbsentTest(unittest.TestCase):
    def test_passes_when_no_reference(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "src").mkdir(parents=True, exist_ok=True)
            (root / "tools").mkdir(parents=True, exist_ok=True)
            (root / "test").mkdir(parents=True, exist_ok=True)
            allow = root / "tools" / "runtime2_reference_allowlist.txt"
            allow.write_text("", encoding="utf-8")
            with patch.object(guard_mod, "ROOT", root), patch.object(
                guard_mod, "ALLOWLIST_FILE", allow
            ), patch.object(
                sys, "argv", ["check_runtime2_references_absent.py"]
            ), patch(
                "sys.stdout", new_callable=io.StringIO
            ) as out:
                rc = guard_mod.main()
        self.assertEqual(rc, 0)
        self.assertIn("[OK]", out.getvalue())

    def test_fails_on_reference(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "src"
            tools = root / "tools"
            test_dir = root / "test"
            src.mkdir(parents=True, exist_ok=True)
            tools.mkdir(parents=True, exist_ok=True)
            test_dir.mkdir(parents=True, exist_ok=True)
            needle = "src/" + "runtime" + "2/cpp/core/built_in/py_runtime.h"
            (src / "example.py").write_text(f"x = '{needle}'\n", encoding="utf-8")
            allow = tools / "runtime2_reference_allowlist.txt"
            allow.write_text("", encoding="utf-8")
            with patch.object(guard_mod, "ROOT", root), patch.object(
                guard_mod, "ALLOWLIST_FILE", allow
            ), patch.object(
                sys, "argv", ["check_runtime2_references_absent.py"]
            ), patch(
                "sys.stdout", new_callable=io.StringIO
            ) as out:
                rc = guard_mod.main()
        self.assertEqual(rc, 1)
        self.assertIn("src/example.py:1", out.getvalue())


if __name__ == "__main__":
    unittest.main()
