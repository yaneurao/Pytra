"""Contract that separates backend support claims from coverage claims."""

from __future__ import annotations

from typing import Final

from src.toolchain.compiler import backend_contract_coverage_inventory as coverage_inventory_mod


BACKEND_CONTRACT_COVERAGE_DOC_TARGETS: Final[dict[str, str]] = {
    "support_matrix_ja": "docs/ja/language/backend-parity-matrix.md",
    "support_matrix_en": "docs/en/language/backend-parity-matrix.md",
    "backend_test_matrix_ja": "docs/ja/language/backend-test-matrix.md",
    "backend_test_matrix_en": "docs/en/language/backend-test-matrix.md",
    "plan_ja": "docs/ja/plans/p2-backend-contract-coverage-100.md",
    "plan_en": "docs/en/plans/p2-backend-contract-coverage-100.md",
    "todo_ja": "docs/ja/todo/index.md",
    "todo_en": "docs/en/todo/index.md",
}

BACKEND_CONTRACT_COVERAGE_ROLE_SPLIT: Final[dict[str, str]] = {
    "support_matrix": "Canonical feature x backend support-state publication surface.",
    "coverage_matrix": "Separate bundle-based publication surface for feature x required_lane x backend contract coverage.",
    "backend_test_matrix": "Backend-owned suite-health publication surface that must stay distinct from contract coverage.",
}

BACKEND_CONTRACT_COVERAGE_MATRIX_STATUS: Final[str] = "planned_separate_surface"
BACKEND_CONTRACT_COVERAGE_REQUIREMENT_KEYS: Final[tuple[str, ...]] = (
    "feature_id",
    "required_lane",
    "backend",
    "bundle_id_or_rule",
)
BACKEND_CONTRACT_COVERAGE_100_RULES: Final[dict[str, str]] = {
    "contract_not_line": "100% means contract coverage for feature x required_lane x backend, not line or branch coverage.",
    "bundle_or_rule_required": "Each cell must map to a coverage bundle or an explicit backend-specific/non-applicable rule.",
    "suite_status_not_enough": "Suite PASS/FAIL status alone does not satisfy contract coverage without bundle ownership metadata.",
}
BACKEND_CONTRACT_COVERAGE_SUITE_ATTACHMENT_RULES: Final[dict[str, str]] = {
    "direct_matrix_input": "Direct matrix-input suite families must declare bundle attachments or explicit unmapped bundle-candidate rows.",
    "supporting_only": "Supporting-only suite families must declare explicit exclusion reasons and may not silently own coverage cells.",
}

BACKEND_CONTRACT_COVERAGE_REQUIRED_DOC_NEEDLES: Final[dict[str, tuple[str, ...]]] = {
    "docs/ja/language/backend-parity-matrix.md": (
        "このページは support matrix の canonical publish target であり、bundle-based coverage matrix そのものではありません。",
        "将来の coverage matrix は `feature x required_lane x backend` の contract coverage を別 surface として公開し、`backend-test-matrix.md` は backend-owned suite health の publish target に留めます。",
    ),
    "docs/en/language/backend-parity-matrix.md": (
        "This page is the canonical support-matrix publish target, not the bundle-based coverage matrix itself.",
        "The future coverage matrix will publish `feature x required_lane x backend` contract coverage on a separate surface, while `backend-test-matrix.md` remains the backend-owned suite-health publish target.",
    ),
    "docs/ja/language/backend-test-matrix.md": (
        "このページは backend-owned suite health の publish target であり、将来の bundle-based coverage matrix の代替ではありません。",
    ),
    "docs/en/language/backend-test-matrix.md": (
        "This page is the publish target for backend-owned suite health and is not a substitute for the future bundle-based coverage matrix.",
    ),
    "docs/ja/plans/p2-backend-contract-coverage-100.md": (
        "- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S1-02] support matrix と coverage matrix の役割分担、および contract coverage 100% の定義を docs / tooling contract に固定する。",
        "`backend_contract_coverage_contract.py` / checker / unit test を追加し、support matrix / future coverage matrix / backend test matrix の役割分担と `feature x required_lane x backend` contract coverage 100% の定義を tooling contract に固定した。",
    ),
    "docs/en/plans/p2-backend-contract-coverage-100.md": (
        "- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S1-02] Freeze the role split between the support matrix and the coverage matrix, together with the definition of 100% contract coverage, in docs/tooling contracts.",
        "Added `backend_contract_coverage_contract.py`, its checker, and a unit test to lock the role split between the support matrix, the future coverage matrix, and the backend test matrix, together with the definition of 100% contract coverage for `feature x required_lane x backend`.",
    ),
    "docs/ja/todo/index.md": (
        "`S2-03` までで unpublished multi-backend fixture の `support_matrix` 昇格候補 / `coverage_matrix_only` 維持を machine-readable seed と invariant へ固定し、`property_method_call` を promotion candidate、`list_bool_index` を coverage-only representative として分類した。",
    ),
    "docs/en/todo/index.md": (
        "Through `S2-03`, locked unpublished multi-backend fixture classification into machine-readable seeds and invariants, with `property_method_call` marked as the next `support_matrix` promotion candidate and `list_bool_index` retained as a `coverage_matrix_only` representative.",
    ),
}


def build_backend_contract_coverage_contract_manifest() -> dict[str, object]:
    return {
        "contract_version": 1,
        "doc_targets": dict(BACKEND_CONTRACT_COVERAGE_DOC_TARGETS),
        "role_split": dict(BACKEND_CONTRACT_COVERAGE_ROLE_SPLIT),
        "coverage_matrix_status": BACKEND_CONTRACT_COVERAGE_MATRIX_STATUS,
        "coverage_requirement_keys": list(BACKEND_CONTRACT_COVERAGE_REQUIREMENT_KEYS),
        "coverage_100_rules": dict(BACKEND_CONTRACT_COVERAGE_100_RULES),
        "suite_attachment_rules": dict(BACKEND_CONTRACT_COVERAGE_SUITE_ATTACHMENT_RULES),
        "bundle_order": list(coverage_inventory_mod.COVERAGE_BUNDLE_ORDER),
        "required_doc_needles": {
            path: list(needles)
            for path, needles in BACKEND_CONTRACT_COVERAGE_REQUIRED_DOC_NEEDLES.items()
        },
    }
