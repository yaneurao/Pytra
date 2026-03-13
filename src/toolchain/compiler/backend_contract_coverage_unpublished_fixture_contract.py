"""Lock unpublished multi-backend fixture classification for coverage rollout."""

from __future__ import annotations

from typing import Final

from src.toolchain.compiler import backend_contract_coverage_inventory as coverage_inventory_mod


UNPUBLISHED_FIXTURE_DOC_TARGETS: Final[dict[str, str]] = {
    "plan_ja": "docs/ja/plans/p2-backend-contract-coverage-100.md",
    "plan_en": "docs/en/plans/p2-backend-contract-coverage-100.md",
    "todo_ja": "docs/ja/todo/index.md",
    "todo_en": "docs/en/todo/index.md",
}

UNPUBLISHED_FIXTURE_STATUS_TO_TARGET: Final[dict[str, str]] = {
    "support_matrix_promotion_candidate": "support_matrix",
    "coverage_only_representative": "coverage_matrix_only",
}

UNPUBLISHED_FIXTURE_CLASSIFICATION_RULES: Final[dict[str, str]] = {
    "promotion_candidate": "Support-matrix promotion candidates must stay unpublished until representative inventory promotion lands, but their multi-backend evidence must remain visible.",
    "coverage_only": "Coverage-only representatives stay out of the support matrix while remaining attached to coverage-only evidence and the future coverage matrix.",
}

UNPUBLISHED_FIXTURE_REQUIRED_DOC_NEEDLES: Final[dict[str, tuple[str, ...]]] = {
    "docs/ja/plans/p2-backend-contract-coverage-100.md": (
        "- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S2-03] multi-backend で既に使われている未掲載 fixture を、support-matrix 昇格候補と coverage-only representative に仕分ける。",
        "unpublished multi-backend fixture inventory に `target_surface` と `status -> target_surface` invariant を追加し、`property_method_call` は `support_matrix_promotion_candidate`、`list_bool_index` は `coverage_matrix_only` 維持の `coverage_only_representative` として固定した。",
    ),
    "docs/en/plans/p2-backend-contract-coverage-100.md": (
        "- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S2-03] Classify already-used multi-backend fixtures that are missing from the support matrix into promotion candidates versus coverage-only representatives.",
        "Added `target_surface` plus a `status -> target_surface` invariant to the unpublished multi-backend fixture inventory. `property_method_call` is fixed as the next `support_matrix_promotion_candidate`, while `list_bool_index` stays a `coverage_only_representative` tied to the `coverage_matrix_only` surface so promotion candidates and regression-only fixtures are distinguishable in machine-readable seeds.",
    ),
    "docs/ja/todo/index.md": (
        "`S2-03` までで unpublished multi-backend fixture の `support_matrix` 昇格候補 / `coverage_matrix_only` 維持を machine-readable seed と invariant へ固定し、`property_method_call` を promotion candidate、`list_bool_index` を coverage-only representative として分類した。",
    ),
    "docs/en/todo/index.md": (
        "Through `S2-03`, locked unpublished multi-backend fixture classification into machine-readable seeds and invariants, with `property_method_call` marked as the next `support_matrix` promotion candidate and `list_bool_index` retained as a `coverage_matrix_only` representative.",
    ),
}


def expected_unpublished_fixture_rows() -> tuple[dict[str, object], ...]:
    return (
        {
            "fixture_rel": "test/fixtures/typing/property_method_call.py",
            "fixture_stem": "property_method_call",
            "status": "support_matrix_promotion_candidate",
            "target_surface": "support_matrix",
        },
        {
            "fixture_rel": "test/fixtures/typing/list_bool_index.py",
            "fixture_stem": "list_bool_index",
            "status": "coverage_only_representative",
            "target_surface": "coverage_matrix_only",
        },
    )


def build_backend_contract_coverage_unpublished_fixture_manifest() -> dict[str, object]:
    return {
        "contract_version": 1,
        "status_order": list(coverage_inventory_mod.UNPUBLISHED_FIXTURE_STATUS_ORDER),
        "target_order": list(coverage_inventory_mod.UNPUBLISHED_FIXTURE_TARGET_ORDER),
        "status_to_target": dict(UNPUBLISHED_FIXTURE_STATUS_TO_TARGET),
        "classification_rules": dict(UNPUBLISHED_FIXTURE_CLASSIFICATION_RULES),
        "expected_rows": list(expected_unpublished_fixture_rows()),
        "required_doc_needles": {
            path: list(needles)
            for path, needles in UNPUBLISHED_FIXTURE_REQUIRED_DOC_NEEDLES.items()
        },
    }
