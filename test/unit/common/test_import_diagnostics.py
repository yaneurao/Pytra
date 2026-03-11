from __future__ import annotations

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

import src.toolchain.frontends.transpile_cli as transpile_cli
import src.toolchain.ir.core_entrypoints as core_entrypoints


class ImportDiagnosticsTest(unittest.TestCase):
    def test_classify_wildcard_import_error(self) -> None:
        err = transpile_cli._classify_import_user_error(
            "unsupported_syntax: from-import wildcard is not supported",
            "from helper import *\n",
            Path("main.py"),
        )
        self.assertEqual(
            err,
            (
                "input_invalid",
                "Failed to resolve imports (missing/conflict/wildcard).",
                ["kind=unresolved_wildcard file=main.py import=from helper import *"],
            ),
        )

    def test_classify_relative_import_error(self) -> None:
        err = transpile_cli._classify_import_user_error(
            "unsupported_import_form: relative import is not supported",
            "from ..helper import f\n",
            Path("pkg/main.py"),
        )
        self.assertEqual(
            err,
            (
                "input_invalid",
                "Unsupported import syntax.",
                ["kind=unsupported_import_form file=pkg/main.py import=from ..helper import f"],
            ),
        )

    def test_classify_structured_duplicate_binding_error(self) -> None:
        err_text = str(
            core_entrypoints._make_import_build_error(
                "duplicate_binding",
                "duplicate import binding: value",
                {"lineno": 1, "col": 0},
                "Rename alias to avoid duplicate imported names.",
                local_name="value",
            )
        )
        err = transpile_cli._classify_import_user_error(
            err_text,
            "from helper import value\n",
            Path("dup.py"),
        )
        self.assertEqual(
            err,
            (
                "input_invalid",
                "Duplicate import binding.",
                ["kind=duplicate_binding file=dup.py import=duplicate import binding: value"],
            ),
        )

    def test_classify_legacy_duplicate_binding_error(self) -> None:
        err = transpile_cli._classify_import_user_error(
            "unsupported_syntax: duplicate import binding: value",
            "from helper import value\n",
            Path("dup.py"),
        )
        self.assertEqual(
            err,
            (
                "input_invalid",
                "Duplicate import binding.",
                ["kind=duplicate_binding file=dup.py import=unsupported_syntax: duplicate import binding: value"],
            ),
        )

    def test_non_import_error_returns_none(self) -> None:
        err = transpile_cli._classify_import_user_error(
            "unsupported_syntax: lambda is not supported",
            "x = lambda y: y\n",
            Path("main.py"),
        )
        self.assertIsNone(err)

    def test_load_east_document_routes_duplicate_binding_through_helper(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            main_py = Path(td) / "main.py"
            main_py.write_text("from helper import value\n", encoding="utf-8")
            with patch.object(
                transpile_cli,
                "convert_path",
                side_effect=core_entrypoints._make_import_build_error(
                    "duplicate_binding",
                    "duplicate import binding: value",
                    {"lineno": 1, "col": 0},
                    "Rename alias to avoid duplicate imported names.",
                    local_name="value",
                ),
            ):
                with self.assertRaises(RuntimeError) as cm:
                    transpile_cli.load_east_document(main_py)

        parsed = transpile_cli.parse_user_error(str(cm.exception))
        self.assertEqual(parsed["category"], "input_invalid")
        self.assertEqual(parsed["summary"], "Duplicate import binding.")
        self.assertEqual(
            parsed["details"],
            [f"kind=duplicate_binding file={main_py} import=duplicate import binding: value"],
        )


if __name__ == "__main__":
    unittest.main()
