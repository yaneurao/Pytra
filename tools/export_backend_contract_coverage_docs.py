#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_contract_coverage_inventory as inventory_mod
from src.toolchain.compiler import (
    backend_contract_coverage_matrix_contract as matrix_mod,
)
from src.toolchain.compiler import (
    backend_contract_coverage_suite_attachment_contract as suite_mod,
)


DOC_JA = ROOT / "docs" / "ja" / "language" / "backend-coverage-matrix.md"
DOC_EN = ROOT / "docs" / "en" / "language" / "backend-coverage-matrix.md"

TAXONOMY_BEGIN = "<!-- BEGIN BACKEND COVERAGE TAXONOMY TABLE -->"
TAXONOMY_END = "<!-- END BACKEND COVERAGE TAXONOMY TABLE -->"
ATTACHMENT_BEGIN = "<!-- BEGIN BACKEND COVERAGE SUITE ATTACHMENT TABLE -->"
ATTACHMENT_END = "<!-- END BACKEND COVERAGE SUITE ATTACHMENT TABLE -->"
OWNERSHIP_BEGIN = "<!-- BEGIN BACKEND COVERAGE OWNERSHIP TABLE -->"
OWNERSHIP_END = "<!-- END BACKEND COVERAGE OWNERSHIP TABLE -->"
UNPUBLISHED_BEGIN = "<!-- BEGIN BACKEND COVERAGE UNPUBLISHED FIXTURE TABLE -->"
UNPUBLISHED_END = "<!-- END BACKEND COVERAGE UNPUBLISHED FIXTURE TABLE -->"


def _replace_block(text: str, begin: str, end: str, replacement: str) -> str:
    start = text.index(begin) + len(begin)
    finish = text.index(end)
    return text[:start] + "\n\n" + replacement.rstrip() + "\n\n" + text[finish:]


def _render_markdown_table(headers: tuple[str, ...], rows: tuple[tuple[str, ...], ...]) -> str:
    table_rows = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    table_rows.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(table_rows)


def _render_taxonomy_table() -> str:
    rows = tuple(
        (
            entry["bundle_id"],
            ", ".join(entry["suite_ids"]),
            ", ".join(entry["harness_kinds"]),
            "<br>".join(entry["source_roots"]),
        )
        for entry in inventory_mod.iter_coverage_bundle_taxonomy()
    )
    return _render_markdown_table(
        ("bundle", "suite_ids", "harness_kinds", "source_roots"),
        rows,
    )


def _render_suite_attachment_table() -> str:
    rows = list[tuple[str, str, str, str, str]]()
    rows.extend(
        (
            row["suite_id"],
            row["status"],
            row["bundle_kind"],
            row["bundle_id"],
            row["notes"],
        )
        for row in suite_mod.iter_suite_attachment_rows()
    )
    rows.extend(
        (
            row["suite_id"],
            row["status"],
            row["bundle_kind"],
            row["reason_code"],
            row["notes"],
        )
        for row in suite_mod.iter_unmapped_suite_candidate_rows()
    )
    rows.extend(
        (
            row["suite_id"],
            row["status"],
            "-",
            row["reason_code"],
            row["notes"],
        )
        for row in suite_mod.iter_supporting_only_suite_rows()
    )
    return _render_markdown_table(
        ("suite_id", "status", "bundle_kind", "bundle_id_or_reason", "notes"),
        tuple(rows),
    )


def _render_ownership_table() -> str:
    runtime_rule_by_category = matrix_mod.RUNTIME_RULE_BY_CATEGORY
    rows = tuple(
        (
            category,
            matrix_mod.BUNDLE_OWNER_BY_LANE["parse"],
            matrix_mod.BUNDLE_OWNER_BY_LANE["east"],
            matrix_mod.BUNDLE_OWNER_BY_LANE["east3_lowering"],
            matrix_mod.BUNDLE_OWNER_BY_LANE["emit"],
            runtime_rule_by_category[category],
        )
        for category in ("syntax", "builtin", "stdlib")
    )
    return _render_markdown_table(
        ("category", "parse", "east", "east3_lowering", "emit", "runtime"),
        rows,
    )


def _render_unpublished_fixture_table() -> str:
    rows = tuple(
        (
            row["fixture_stem"],
            row["status"],
            row["target_surface"],
            row["proposed_feature_id"] or "-",
            row["notes"],
        )
        for row in inventory_mod.iter_unpublished_multi_backend_fixture_inventory()
    )
    return _render_markdown_table(
        ("fixture", "status", "target_surface", "proposed_feature_id", "notes"),
        rows,
    )


def render_updated_doc_text(doc_text: str) -> str:
    doc_text = _replace_block(doc_text, TAXONOMY_BEGIN, TAXONOMY_END, _render_taxonomy_table())
    doc_text = _replace_block(
        doc_text,
        ATTACHMENT_BEGIN,
        ATTACHMENT_END,
        _render_suite_attachment_table(),
    )
    doc_text = _replace_block(
        doc_text,
        OWNERSHIP_BEGIN,
        OWNERSHIP_END,
        _render_ownership_table(),
    )
    doc_text = _replace_block(
        doc_text,
        UNPUBLISHED_BEGIN,
        UNPUBLISHED_END,
        _render_unpublished_fixture_table(),
    )
    return doc_text


def _update_doc(path: Path) -> bool:
    before = path.read_text(encoding="utf-8")
    after = render_updated_doc_text(before)
    if after == before:
        return False
    path.write_text(after, encoding="utf-8")
    return True


def main(argv: list[str] | None = None) -> int:
    check_mode = argv == ["--check"]
    paths = (DOC_JA, DOC_EN)
    changed = False
    for path in paths:
        before = path.read_text(encoding="utf-8")
        after = render_updated_doc_text(before)
        if after != before:
            if check_mode:
                print(f"[FAIL] stale backend coverage docs: {path.relative_to(ROOT)}")
                return 1
            path.write_text(after, encoding="utf-8")
            changed = True
    if check_mode:
        print("[OK] backend coverage docs are synchronized")
        return 0
    if changed:
        print("[OK] updated backend coverage docs")
    else:
        print("[OK] backend coverage docs already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
