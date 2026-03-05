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

from tools import check_runtime_special_generators_absent as guard_mod


class CheckRuntimeSpecialGeneratorsAbsentTest(unittest.TestCase):
    def test_main_passes_when_no_legacy_generator_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tools_dir = root / "tools"
            tools_dir.mkdir(parents=True, exist_ok=True)
            with patch.object(guard_mod, "ROOT", root), patch.object(
                guard_mod, "TOOLS_DIR", tools_dir
            ), patch.object(
                sys, "argv", ["check_runtime_special_generators_absent.py"]
            ), patch(
                "sys.stdout", new_callable=io.StringIO
            ) as out:
                rc = guard_mod.main()
        self.assertEqual(rc, 0)
        self.assertIn("[OK]", out.getvalue())

    def test_main_fails_when_legacy_generator_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tools_dir = root / "tools"
            tools_dir.mkdir(parents=True, exist_ok=True)
            (tools_dir / "gen_image_runtime_from_canonical.py").write_text("# legacy\n", encoding="utf-8")
            with patch.object(guard_mod, "ROOT", root), patch.object(
                guard_mod, "TOOLS_DIR", tools_dir
            ), patch.object(
                sys, "argv", ["check_runtime_special_generators_absent.py"]
            ), patch(
                "sys.stdout", new_callable=io.StringIO
            ) as out:
                rc = guard_mod.main()
        self.assertEqual(rc, 1)
        self.assertIn("gen_image_runtime_from_canonical.py", out.getvalue())


if __name__ == "__main__":
    unittest.main()
