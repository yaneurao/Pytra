"""Suite-family attachment rows for bundle-based backend contract coverage."""

from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_contract_coverage_inventory as inventory_mod


ATTACHMENT_KIND_ORDER: Final[tuple[str, ...]] = ("bundle_attachment", "explicit_exclusion")
EXCLUSION_REASON_ORDER: Final[tuple[str, ...]] = (
    "supporting_only_link_validation",
    "supporting_only_selfhost_build",
    "supporting_only_tooling_checker",
)

EXCLUSION_REASON_BY_SUITE_ID: Final[dict[str, str]] = {
    "unit_link": "supporting_only_link_validation",
    "unit_selfhost": "supporting_only_selfhost_build",
    "unit_tooling": "supporting_only_tooling_checker",
}

BUNDLE_ATTACHMENTS_BY_SUITE_ID: Final[dict[str, tuple[str, ...]]] = {
    "unit_common": ("frontend", "emit", "import_package"),
    "unit_backends": ("emit", "import_package"),
    "unit_ir": ("frontend",),
    "ir_fixture": ("ir2lang",),
    "integration": ("integration",),
    "transpile_artifact": ("runtime",),
}


class CoverageSuiteAttachmentRow(TypedDict):
    suite_id: str
    suite_kind: str
    coverage_role: str
    attachment_kind: str
    bundle_ids: tuple[str, ...]
    exclusion_reason: str


def _build_suite_attachment_rows() -> tuple[CoverageSuiteAttachmentRow, ...]:
    rows: list[CoverageSuiteAttachmentRow] = []
    for suite_row in inventory_mod.iter_live_suite_family_inventory():
        suite_id = suite_row["suite_id"]
        if suite_row["coverage_role"] == "direct_matrix_input":
            rows.append(
                {
                    "suite_id": suite_id,
                    "suite_kind": suite_row["suite_kind"],
                    "coverage_role": suite_row["coverage_role"],
                    "attachment_kind": "bundle_attachment",
                    "bundle_ids": BUNDLE_ATTACHMENTS_BY_SUITE_ID[suite_id],
                    "exclusion_reason": "",
                }
            )
            continue
        rows.append(
            {
                "suite_id": suite_id,
                "suite_kind": suite_row["suite_kind"],
                "coverage_role": suite_row["coverage_role"],
                "attachment_kind": "explicit_exclusion",
                "bundle_ids": (),
                "exclusion_reason": EXCLUSION_REASON_BY_SUITE_ID[suite_id],
            }
        )
    return tuple(rows)


SUITE_ATTACHMENT_ROWS_V1: Final[tuple[CoverageSuiteAttachmentRow, ...]] = _build_suite_attachment_rows()


def iter_backend_contract_coverage_suite_attachments() -> tuple[CoverageSuiteAttachmentRow, ...]:
    return SUITE_ATTACHMENT_ROWS_V1


def known_bundle_ids() -> tuple[str, ...]:
    return tuple(bundle["bundle_id"] for bundle in inventory_mod.iter_coverage_bundle_taxonomy())


def expected_suite_ids() -> tuple[str, ...]:
    return tuple(row["suite_id"] for row in inventory_mod.iter_live_suite_family_inventory())


def build_backend_contract_coverage_suite_attachment_manifest() -> dict[str, object]:
    return {
        "manifest_version": 1,
        "attachment_kind_order": list(ATTACHMENT_KIND_ORDER),
        "exclusion_reason_order": list(EXCLUSION_REASON_ORDER),
        "coverage_role_order": list(inventory_mod.LIVE_SUITE_ROLE_ORDER),
        "suite_family_order": list(inventory_mod.SUITE_FAMILY_ORDER),
        "known_bundle_ids": list(known_bundle_ids()),
        "rows": list(iter_backend_contract_coverage_suite_attachments()),
    }
