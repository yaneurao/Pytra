"""Contract that separates backend support claims from coverage claims."""

from __future__ import annotations

from typing import Final

from src.toolchain.compiler import backend_contract_coverage_inventory as coverage_inventory_mod


BACKEND_CONTRACT_COVERAGE_DOC_TARGETS: Final[dict[str, str]] = {
    "coverage_matrix_ja": "docs/ja/language/backend-coverage-matrix.md",
    "coverage_matrix_en": "docs/en/language/backend-coverage-matrix.md",
    "language_index_ja": "docs/ja/language/index.md",
    "language_index_en": "docs/en/language/index.md",
    "support_matrix_ja": "docs/ja/language/backend-parity-matrix.md",
    "support_matrix_en": "docs/en/language/backend-parity-matrix.md",
    "backend_test_matrix_ja": "docs/ja/language/backend-test-matrix.md",
    "backend_test_matrix_en": "docs/en/language/backend-test-matrix.md",
    "plan_ja": "docs/ja/plans/archive/20260314-p2-backend-contract-coverage-100.md",
    "plan_en": "docs/en/plans/archive/20260314-p2-backend-contract-coverage-100.md",
    "todo_ja": "docs/ja/todo/archive/20260314.md",
    "todo_en": "docs/en/todo/archive/20260314.md",
}

BACKEND_CONTRACT_COVERAGE_ROLE_SPLIT: Final[dict[str, str]] = {
    "support_matrix": "Canonical feature x backend support-state publication surface.",
    "coverage_matrix": "Separate bundle-based publication surface for feature x required_lane x backend contract coverage.",
    "backend_test_matrix": "Backend-owned suite-health publication surface that must stay distinct from contract coverage.",
}

BACKEND_CONTRACT_COVERAGE_MATRIX_STATUS: Final[str] = "published_seed_surface"
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
    "docs/ja/language/backend-coverage-matrix.md": (
        "このページは、bundle-based verification coverage を公開する canonical publish target です。",
        "- このページは `feature x required_lane x backend` の contract coverage seed と、その bundle/rule ownership を公開する。",
    ),
    "docs/en/language/backend-coverage-matrix.md": (
        "This page is the canonical publish target for bundle-based verification coverage.",
        "- This page publishes the `feature x required_lane x backend` contract-coverage seed together with its bundle/rule ownership.",
    ),
    "docs/ja/language/index.md": (
        "- feature × required_lane × backend の bundle-based coverage seed と ownership: [Backend Coverage Matrix](./backend-coverage-matrix.md)",
    ),
    "docs/en/language/index.md": (
        "- Bundle-based coverage seed and ownership for feature × required_lane × backend: [Backend Coverage Matrix](./backend-coverage-matrix.md)",
    ),
    "docs/ja/language/backend-parity-matrix.md": (
        "このページは support matrix の canonical publish target であり、bundle-based coverage matrix そのものではありません。",
        "`feature x required_lane x backend` の contract coverage seed と ownership は [backend-coverage-matrix.md](./backend-coverage-matrix.md) を別 surface として公開し、`backend-test-matrix.md` は backend-owned suite health の publish target に留めます。",
    ),
    "docs/en/language/backend-parity-matrix.md": (
        "This page is the canonical support-matrix publish target, not the bundle-based coverage matrix itself.",
        "[backend-coverage-matrix.md](./backend-coverage-matrix.md) publishes the `feature x required_lane x backend` contract-coverage seed and ownership on the separate coverage surface, while `backend-test-matrix.md` remains the backend-owned suite-health publish target.",
    ),
    "docs/ja/language/backend-test-matrix.md": (
        "このページは backend-owned suite health の publish target であり、[backend-coverage-matrix.md](./backend-coverage-matrix.md) の代替ではありません。",
    ),
    "docs/en/language/backend-test-matrix.md": (
        "This page is the publish target for backend-owned suite health and is not a substitute for [backend-coverage-matrix.md](./backend-coverage-matrix.md).",
    ),
    "docs/ja/plans/archive/20260314-p2-backend-contract-coverage-100.md": (
        "- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S1-02] support matrix と coverage matrix の役割分担、および contract coverage 100% の定義を docs / tooling contract に固定する。",
        "`backend_contract_coverage_contract.py` / checker / unit test を追加し、support matrix / future coverage matrix / backend test matrix の役割分担と `feature x required_lane x backend` contract coverage 100% の定義を tooling contract に固定した。",
    ),
    "docs/en/plans/archive/20260314-p2-backend-contract-coverage-100.md": (
        "- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S1-02] Freeze the role split between the support matrix and the coverage matrix, together with the definition of 100% contract coverage, in docs/tooling contracts.",
        "Added `backend_contract_coverage_contract.py`, its checker, and a unit test to lock the role split between the support matrix, the future coverage matrix, and the backend test matrix, together with the definition of 100% contract coverage for `feature x required_lane x backend`.",
    ),
    "docs/ja/todo/archive/20260314.md": (
        "- 進捗メモ: end state は `backend-coverage-matrix.md` が bundle taxonomy / suite attachment / required-lane seed ownership / unpublished fixture classification を公開する canonical coverage surface になり、support matrix / backend test matrix からも cross-link され、exporter/checker で drift が fail-fast する状態。",
    ),
    "docs/en/todo/archive/20260314.md": (
        "- Progress memo: the end state is that `backend-coverage-matrix.md` publishes bundle taxonomy, suite attachments, required-lane seed ownership, and unpublished fixture classification as the canonical coverage surface, is cross-linked from the support matrix and backend test matrix, and fails fast on doc drift through the exporter/checker pair.",
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
