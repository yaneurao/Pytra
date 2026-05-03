from __future__ import annotations

import json
import unittest

from tools.gen import gen_top100_language_coverage as mod


class Top100LanguageCoverageGeneratorTest(unittest.TestCase):
    def test_catalog_has_exactly_100_rows(self) -> None:
        rows = mod.build_rows()
        self.assertEqual(len(rows), 100)
        self.assertEqual(len({row.language for row in rows}), 100)

    def test_categories_are_constrained(self) -> None:
        allowed = {"backend", "host", "interop", "syntax", "defer"}
        self.assertEqual({row.category for row in mod.build_rows()} - allowed, set())

    def test_top50_syntax_rows_have_backend_plan(self) -> None:
        missing = [
            row.language
            for row in mod.build_rows()
            if isinstance(row.rank, int) and row.rank <= 50 and row.category == "syntax" and not row.backend_plan_tier
        ]
        self.assertEqual(missing, [])

    def test_defer_rows_have_conditions(self) -> None:
        missing = [row.language for row in mod.build_rows() if row.category == "defer" and not row.defer_condition]
        self.assertEqual(missing, [])

    def test_json_doc_is_machine_readable(self) -> None:
        doc = mod.build_json_doc()
        encoded = json.dumps(doc, ensure_ascii=False)
        decoded = json.loads(encoded)
        self.assertEqual(decoded["schema_version"], 1)
        self.assertEqual(decoded["source_snapshot"]["stored_at"], "docs/ja/progress/top100-language-coverage.json")
        self.assertEqual(len(decoded["rows"]), 100)

    def test_markdown_mentions_standard_gate_and_todo_ids(self) -> None:
        rendered = mod.render_ja_markdown()
        self.assertIn("Docker/devcontainer 標準ゲート", rendered)
        self.assertIn("Top50 未対応候補 backend plan", rendered)
        self.assertIn("defer 条件", rendered)


if __name__ == "__main__":
    unittest.main()
