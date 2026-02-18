from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.common.language_profile import load_language_profile


class LanguageProfileTest(unittest.TestCase):
    def test_load_cpp_profile(self) -> None:
        p = load_language_profile("cpp")
        self.assertEqual(p.get("schema_version"), 1)
        self.assertEqual(p.get("language"), "cpp")

        runtime_calls = p.get("runtime_calls")
        self.assertIsInstance(runtime_calls, dict)
        module_attr_call = runtime_calls.get("module_attr_call") if isinstance(runtime_calls, dict) else None
        self.assertIsInstance(module_attr_call, dict)
        math_map = module_attr_call.get("math") if isinstance(module_attr_call, dict) else None
        self.assertIsInstance(math_map, dict)
        self.assertEqual(math_map.get("sqrt"), "py_math::sqrt")


if __name__ == "__main__":
    unittest.main()
