from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import src.toolchain.compiler.backend_registry_diagnostics as registry_diagnostics


class BackendRegistryDiagnosticsTest(unittest.TestCase):
    def test_normalize_known_block_detail(self) -> None:
        self.assertEqual(
            registry_diagnostics.normalize_top_level_category("unsupported_by_design"),
            "known_block",
        )

    def test_infer_unsupported_target_detail(self) -> None:
        self.assertEqual(
            registry_diagnostics.infer_diagnostic_detail_from_text("RuntimeError: unsupported target: scala"),
            "unsupported_by_design",
        )

    def test_infer_preview_only_detail(self) -> None:
        self.assertEqual(
            registry_diagnostics.infer_diagnostic_detail_from_text("preview backend: intentionally disabled"),
            "preview_only",
        )

    def test_infer_toolchain_missing_detail(self) -> None:
        self.assertEqual(
            registry_diagnostics.infer_diagnostic_detail_from_text("clang++ not found"),
            "toolchain_missing",
        )

    def test_classify_registry_diagnostic_for_unsupported_target(self) -> None:
        self.assertEqual(
            registry_diagnostics.classify_registry_diagnostic("unsupported target: missing-target"),
            ("known_block", "unsupported_by_design"),
        )

    def test_classify_registry_diagnostic_for_preview_backend(self) -> None:
        self.assertEqual(
            registry_diagnostics.classify_registry_diagnostic("preview backend: scala emitter is gated"),
            ("known_block", "preview_only"),
        )

    def test_classify_registry_diagnostic_for_toolchain_missing(self) -> None:
        self.assertEqual(
            registry_diagnostics.classify_registry_diagnostic("clang++ not found"),
            ("toolchain_missing", "toolchain_missing"),
        )

    def test_classify_registry_diagnostic_for_broken_emit_kind(self) -> None:
        self.assertEqual(
            registry_diagnostics.classify_registry_diagnostic("unsupported emit kind: broken"),
            ("regression", "regression"),
        )


if __name__ == "__main__":
    unittest.main()
