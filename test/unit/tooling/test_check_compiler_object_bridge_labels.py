from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import check_compiler_object_bridge_labels as bridge_mod


class CheckCompilerObjectBridgeLabelsTest(unittest.TestCase):
    def test_repo_targets_have_no_unlabeled_bridge_usage(self) -> None:
        self.assertEqual(bridge_mod._collect_all_issues(), [])

    def test_repo_targets_have_expected_labeled_bridge_inventory(self) -> None:
        self.assertEqual(
            bridge_mod._collect_all_labeled_usages(),
            [
                (
                    "src/runtime/cpp/native/compiler/transpile_cli.cpp",
                    137,
                    "legacy_migration_adapter",
                ),
                (
                    "src/runtime/cpp/native/compiler/transpile_cli.cpp",
                    162,
                    "legacy_migration_adapter",
                ),
                (
                    "src/runtime/cpp/native/compiler/transpile_cli.cpp",
                    181,
                    "legacy_migration_adapter",
                ),
            ],
        )

    def test_collect_file_issues_rejects_unlabeled_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.cpp"
            path.write_text("return obj_to_int64(value);\n", encoding="utf-8")
            self.assertEqual(
                bridge_mod._collect_file_issues(path),
                ["sample.cpp:1: unlabeled compiler object bridge usage"],
            )

    def test_collect_file_issues_accepts_supported_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.cpp"
            path.write_text(
                "// P2-object-bridge: legacy_migration_adapter\n"
                "return obj_to_int64(value);\n",
                encoding="utf-8",
            )
            self.assertEqual(bridge_mod._collect_file_issues(path), [])
            self.assertEqual(
                bridge_mod._collect_file_labeled_usages(path),
                [("sample.cpp", 2, "legacy_migration_adapter")],
            )

    def test_collect_file_issues_rejects_orphan_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.cpp"
            path.write_text("// P2-object-bridge: legacy_migration_adapter\nint x = 0;\n", encoding="utf-8")
            self.assertEqual(
                bridge_mod._collect_file_issues(path),
                ["sample.cpp:1: bridge label is not attached to a bridge usage"],
            )


if __name__ == "__main__":
    unittest.main()
