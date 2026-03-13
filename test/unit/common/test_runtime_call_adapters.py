from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from src.toolchain.frontends.runtime_call_adapters import normalize_rendered_runtime_args


class RuntimeCallAdaptersTest(unittest.TestCase):
    def test_math_float_args_adapter_passes_positional_args_through(self) -> None:
        self.assertEqual(
            normalize_rendered_runtime_args(
                "math.float_args",
                ["x", "y"],
                [],
                error_prefix="test",
            ),
            ["x", "y"],
        )

    def test_math_value_getter_adapter_rejects_keywords(self) -> None:
        with self.assertRaises(RuntimeError) as cm:
            normalize_rendered_runtime_args(
                "math.value_getter",
                [],
                [("unused", "1")],
                error_prefix="test",
            )
        self.assertIn("unsupported runtime keywords for adapter", str(cm.exception))

    def test_save_gif_adapter_applies_defaults_and_keyword_order(self) -> None:
        self.assertEqual(
            normalize_rendered_runtime_args(
                "image.save_gif.keyword_defaults",
                ["out", "w", "h", "frames", "palette"],
                [("loop", "0"), ("delay_cs", "4")],
                default_values={"delay_cs": "8", "loop": "1"},
                error_prefix="test",
            ),
            ["out", "w", "h", "frames", "palette", "4", "0"],
        )

    def test_save_gif_adapter_rejects_duplicate_keyword_and_positional(self) -> None:
        with self.assertRaises(RuntimeError) as cm:
            normalize_rendered_runtime_args(
                "image.save_gif.keyword_defaults",
                ["out", "w", "h", "frames", "palette", "4"],
                [("delay_cs", "5")],
                default_values={"delay_cs": "8", "loop": "1"},
                error_prefix="test",
            )
        self.assertIn("duplicate delay_cs", str(cm.exception))

    def test_save_gif_adapter_rejects_unknown_keyword(self) -> None:
        with self.assertRaises(RuntimeError) as cm:
            normalize_rendered_runtime_args(
                "image.save_gif.keyword_defaults",
                ["out", "w", "h", "frames", "palette"],
                [("fps", "12")],
                default_values={"delay_cs": "8", "loop": "1"},
                error_prefix="test",
            )
        self.assertIn("unsupported save_gif keyword", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
