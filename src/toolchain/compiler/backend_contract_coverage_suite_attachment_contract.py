"""Lock live suite family attachments into coverage bundles or explicit exclusions."""

from __future__ import annotations

from typing import Final, TypedDict

from src.toolchain.compiler import backend_contract_coverage_inventory as coverage_inventory_mod


ATTACHMENT_STATUS_ORDER: Final[tuple[str, ...]] = ("attached", "unmapped_candidate", "supporting_only")
UNMAPPED_REASON_ORDER: Final[tuple[str, ...]] = ("runtime_rule_owned_seed",)
SUPPORTING_ONLY_REASON_ORDER: Final[tuple[str, ...]] = (
    "linker_validation_sidecar",
    "selfhost_preparation_sidecar",
    "tooling_checker_sidecar",
)


class SuiteAttachmentRow(TypedDict):
    suite_id: str
    bundle_kind: str
    bundle_id: str
    status: str
    notes: str


class UnmappedSuiteCandidateRow(TypedDict):
    suite_id: str
    bundle_kind: str
    status: str
    reason_code: str
    notes: str


class SupportingOnlySuiteRow(TypedDict):
    suite_id: str
    status: str
    reason_code: str
    notes: str


SUITE_ATTACHMENT_ROWS_V1: Final[tuple[SuiteAttachmentRow, ...]] = (
    {
        "suite_id": "unit_common",
        "bundle_kind": "frontend",
        "bundle_id": "frontend_unit_contract_bundle",
        "status": "attached",
        "notes": "Shared parser/EAST/EAST3 unit tests feed the frontend bundle directly.",
    },
    {
        "suite_id": "unit_common",
        "bundle_kind": "emit",
        "bundle_id": "emit_backend_smoke_bundle",
        "status": "attached",
        "notes": "Common backend smoke helpers are part of the emit bundle surface.",
    },
    {
        "suite_id": "unit_common",
        "bundle_kind": "import_package",
        "bundle_id": "import_package_bundle",
        "status": "attached",
        "notes": "Relative-import semantics tests back the shared import/package coverage lane.",
    },
    {
        "suite_id": "unit_backends",
        "bundle_kind": "emit",
        "bundle_id": "emit_backend_smoke_bundle",
        "status": "attached",
        "notes": "Backend smoke suites are the canonical emit coverage surface.",
    },
    {
        "suite_id": "unit_backends",
        "bundle_kind": "import_package",
        "bundle_id": "import_package_bundle",
        "status": "attached",
        "notes": "Backend-specific package and relative-import smoke feeds the import/package bundle.",
    },
    {
        "suite_id": "unit_ir",
        "bundle_kind": "frontend",
        "bundle_id": "frontend_unit_contract_bundle",
        "status": "attached",
        "notes": "IR-facing frontend unit tests stay attached to the frontend bundle.",
    },
    {
        "suite_id": "ir_fixture",
        "bundle_kind": "ir2lang",
        "bundle_id": "ir2lang_smoke_bundle",
        "status": "attached",
        "notes": "Backend-only EAST3 fixture smoke owns the ir2lang bundle.",
    },
    {
        "suite_id": "integration",
        "bundle_kind": "integration",
        "bundle_id": "integration_gc_bundle",
        "status": "attached",
        "notes": "Native compile/run integration coverage currently comes from the GC integration suite.",
    },
    {
        "suite_id": "transpile_artifact",
        "bundle_kind": "runtime",
        "bundle_id": "runtime_parity_bundle",
        "status": "attached",
        "notes": "Staged runtime parity artifacts remain the canonical runtime bundle surface.",
    },
)


UNMAPPED_SUITE_CANDIDATE_ROWS_V1: Final[tuple[UnmappedSuiteCandidateRow, ...]] = (
    {
        "suite_id": "unit_backends",
        "bundle_kind": "runtime",
        "status": "unmapped_candidate",
        "reason_code": "runtime_rule_owned_seed",
        "notes": (
            "Runtime cells are still seeded as explicit case/module follow-up rules, so "
            "backend unit-runtime checks stay visible as an unmapped candidate until the "
            "runtime bundle absorbs them."
        ),
    },
)


SUPPORTING_ONLY_SUITE_ROWS_V1: Final[tuple[SupportingOnlySuiteRow, ...]] = (
    {
        "suite_id": "unit_link",
        "status": "supporting_only",
        "reason_code": "linker_validation_sidecar",
        "notes": "Linker tests validate bundle plumbing indirectly and do not own direct coverage cells.",
    },
    {
        "suite_id": "unit_selfhost",
        "status": "supporting_only",
        "reason_code": "selfhost_preparation_sidecar",
        "notes": "Selfhost preparation tests guard the pipeline but are not direct coverage-matrix inputs.",
    },
    {
        "suite_id": "unit_tooling",
        "status": "supporting_only",
        "reason_code": "tooling_checker_sidecar",
        "notes": "Tooling/checker tests police inventories and contracts rather than owning coverage cells.",
    },
)


def iter_suite_attachment_rows() -> tuple[SuiteAttachmentRow, ...]:
    return SUITE_ATTACHMENT_ROWS_V1


def iter_unmapped_suite_candidate_rows() -> tuple[UnmappedSuiteCandidateRow, ...]:
    return UNMAPPED_SUITE_CANDIDATE_ROWS_V1


def iter_supporting_only_suite_rows() -> tuple[SupportingOnlySuiteRow, ...]:
    return SUPPORTING_ONLY_SUITE_ROWS_V1


def build_backend_contract_coverage_suite_attachment_manifest() -> dict[str, object]:
    return {
        "manifest_version": 1,
        "status_order": list(ATTACHMENT_STATUS_ORDER),
        "unmapped_reason_order": list(UNMAPPED_REASON_ORDER),
        "supporting_only_reason_order": list(SUPPORTING_ONLY_REASON_ORDER),
        "bundle_order": list(coverage_inventory_mod.COVERAGE_BUNDLE_ORDER),
        "suite_family_order": list(coverage_inventory_mod.SUITE_FAMILY_ORDER),
        "attachments": list(iter_suite_attachment_rows()),
        "unmapped_candidates": list(iter_unmapped_suite_candidate_rows()),
        "supporting_only_suites": list(iter_supporting_only_suite_rows()),
    }
