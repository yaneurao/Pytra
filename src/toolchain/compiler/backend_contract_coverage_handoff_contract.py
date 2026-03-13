"""Docs/export/checker handoff for backend contract coverage publication."""

from __future__ import annotations

from typing import Final


BACKEND_CONTRACT_COVERAGE_HANDOFF_DOC_TARGETS: Final[dict[str, str]] = {
    "coverage_matrix_ja": "docs/ja/language/backend-coverage-matrix.md",
    "coverage_matrix_en": "docs/en/language/backend-coverage-matrix.md",
    "support_matrix_ja": "docs/ja/language/backend-parity-matrix.md",
    "support_matrix_en": "docs/en/language/backend-parity-matrix.md",
    "backend_test_matrix_ja": "docs/ja/language/backend-test-matrix.md",
    "backend_test_matrix_en": "docs/en/language/backend-test-matrix.md",
    "plan_ja": "docs/ja/plans/p2-backend-contract-coverage-100.md",
    "plan_en": "docs/en/plans/p2-backend-contract-coverage-100.md",
}

BACKEND_CONTRACT_COVERAGE_HANDOFF_EXPORTS: Final[dict[str, str]] = {
    "exporter": "tools/export_backend_contract_coverage_docs.py",
    "checker": "tools/check_backend_contract_coverage_handoff_contract.py",
}

BACKEND_CONTRACT_COVERAGE_HANDOFF_SOURCES: Final[dict[str, str]] = {
    "inventory": "src/toolchain/compiler/backend_contract_coverage_inventory.py",
    "matrix_contract": "src/toolchain/compiler/backend_contract_coverage_matrix_contract.py",
    "suite_attachment_contract": "src/toolchain/compiler/backend_contract_coverage_suite_attachment_contract.py",
    "unpublished_fixture_contract": "src/toolchain/compiler/backend_contract_coverage_unpublished_fixture_contract.py",
}

BACKEND_CONTRACT_COVERAGE_HANDOFF_REQUIRED_DOC_NEEDLES: Final[dict[str, tuple[str, ...]]] = {
    "docs/ja/language/backend-coverage-matrix.md": (
        "このページは、bundle-based verification coverage を公開する canonical publish target です。",
        "- exporter: [export_backend_contract_coverage_docs.py](/workspace/Pytra/tools/export_backend_contract_coverage_docs.py)",
    ),
    "docs/en/language/backend-coverage-matrix.md": (
        "This page is the canonical publish target for bundle-based verification coverage.",
        "- exporter: [export_backend_contract_coverage_docs.py](/workspace/Pytra/tools/export_backend_contract_coverage_docs.py)",
    ),
    "docs/ja/language/backend-parity-matrix.md": (
        "- bundle-based coverage の live surface は [backend-coverage-matrix.md](./backend-coverage-matrix.md) を使います。",
    ),
    "docs/en/language/backend-parity-matrix.md": (
        "- The live bundle-based coverage surface is [backend-coverage-matrix.md](./backend-coverage-matrix.md).",
    ),
    "docs/ja/language/backend-test-matrix.md": (
        "- bundle-based coverage seed と ownership は [backend-coverage-matrix.md](./backend-coverage-matrix.md) を参照する。",
    ),
    "docs/en/language/backend-test-matrix.md": (
        "- For bundle-based coverage seed and ownership, use [backend-coverage-matrix.md](./backend-coverage-matrix.md).",
    ),
    "docs/ja/plans/p2-backend-contract-coverage-100.md": (
        "- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S3-01] docs/export/checker/English mirror を同期し、新規 feature/suite の coverage 漏れを fail-fast にする。",
    ),
    "docs/en/plans/p2-backend-contract-coverage-100.md": (
        "- [x] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S3-01] Sync docs, exports, checkers, and the English mirror so new features/suites fail fast when coverage mapping is missing.",
    ),
}


def build_backend_contract_coverage_handoff_manifest() -> dict[str, object]:
    return {
        "contract_version": 1,
        "doc_targets": dict(BACKEND_CONTRACT_COVERAGE_HANDOFF_DOC_TARGETS),
        "exports": dict(BACKEND_CONTRACT_COVERAGE_HANDOFF_EXPORTS),
        "sources": dict(BACKEND_CONTRACT_COVERAGE_HANDOFF_SOURCES),
        "required_doc_needles": {
            path: list(needles)
            for path, needles in BACKEND_CONTRACT_COVERAGE_HANDOFF_REQUIRED_DOC_NEEDLES.items()
        },
    }
