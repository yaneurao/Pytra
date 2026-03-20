from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.toolchain.emit.common.emitter.code_emitter import CodeEmitter


def _deep_merge(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    out = dict(dst)
    for key, value in src.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _load_language_profile(language: str) -> dict[str, Any]:
    common_core = CodeEmitter.load_profile_with_includes("src/toolchain/emit/common/profiles/core.json")
    lang_profile = CodeEmitter.load_profile_with_includes(f"src/toolchain/emit/{language}/profiles/profile.json")
    if len(lang_profile) == 0:
        raise RuntimeError(f"language profile not found: {language}")
    return _deep_merge(common_core, lang_profile)


class LanguageProfileTest(unittest.TestCase):
    def test_load_cpp_profile(self) -> None:
        p = _load_language_profile("cpp")
        self.assertEqual(p.get("schema_version"), 1)
        self.assertEqual(p.get("language"), "cpp")

        runtime_calls = p.get("runtime_calls")
        self.assertIsInstance(runtime_calls, dict)
        module_attr_call = runtime_calls.get("module_attr_call") if isinstance(runtime_calls, dict) else None
        self.assertIsInstance(module_attr_call, dict)
        self.assertNotIn("math", module_attr_call)


if __name__ == "__main__":
    unittest.main()
