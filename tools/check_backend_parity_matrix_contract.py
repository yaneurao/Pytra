from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_conformance_summary_handoff_contract as conformance_summary_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod
from src.toolchain.compiler import backend_parity_matrix_contract as contract_mod

DOC_TARGETS = (
    ROOT / "docs/ja/language/backend-parity-matrix.md",
    ROOT / "docs/en/language/backend-parity-matrix.md",
)


def _collect_contract_issues() -> list[str]:
    issues: list[str] = []
    if contract_mod.PARITY_MATRIX_BACKEND_ORDER != feature_contract_mod.SUPPORT_MATRIX_BACKEND_ORDER:
        issues.append("backend order drifted away from feature contract support matrix order")
    if contract_mod.PARITY_MATRIX_SUPPORT_STATE_ORDER != feature_contract_mod.SUPPORT_STATE_ORDER:
        issues.append("support state order drifted away from feature contract")
    if contract_mod.PARITY_MATRIX_SOURCE_DESTINATION != "support_matrix":
        issues.append("matrix source destination must stay fixed to support_matrix")
    if contract_mod.PARITY_MATRIX_IMPLEMENTATION_PHASE != "cell_seed_manifest":
        issues.append("matrix implementation phase drifted away from cell_seed_manifest baseline")
    if contract_mod.PARITY_MATRIX_CELL_SCHEMA_STATUS != "seed_populated":
        issues.append("matrix cell schema status drifted away from seed_populated baseline")
    if contract_mod.PARITY_MATRIX_CELL_SCHEMA_VERSION != 1:
        issues.append("matrix cell schema version drifted")
    if contract_mod.PARITY_MATRIX_CELL_COLLECTION_KEY != "backend_cells":
        issues.append("matrix cell collection key drifted")
    if contract_mod.PARITY_MATRIX_CELL_REQUIRED_KEYS != ("backend", "support_state", "evidence_kind"):
        issues.append("matrix cell required keys drifted")
    if contract_mod.PARITY_MATRIX_CELL_OPTIONAL_KEYS != ("details", "evidence_ref", "diagnostic_kind"):
        issues.append("matrix cell optional keys drifted")
    if contract_mod.PARITY_MATRIX_CELL_EVIDENCE_KIND_ORDER != (
        "build_run_smoke",
        "transpile_smoke",
        "contract_guard",
        "diagnostic_guard",
        "not_started_placeholder",
        "preview_guard",
    ):
        issues.append("matrix cell evidence kind order drifted")
    if contract_mod.PARITY_MATRIX_ALLOWED_EVIDENCE_KINDS_BY_STATE != {
        "supported": ("build_run_smoke", "transpile_smoke"),
        "fail_closed": ("contract_guard", "diagnostic_guard"),
        "not_started": ("not_started_placeholder",),
        "experimental": ("preview_guard", "transpile_smoke", "build_run_smoke"),
    }:
        issues.append("matrix state/evidence compatibility drifted")
    if contract_mod.PARITY_MATRIX_CELL_GAP_SUMMARY != {
        "seed_state_is_conservative": "Current backend cell seeds use conservative placeholder states outside cpp until reviewed backend-by-backend evidence is filled.",
        "docs_table_is_seed_only": "The docs page now renders the seeded 2D support table, but the published cells are still placeholders outside the reviewed cpp lane.",
        "cell_details_are_sparse": "Per-cell details/evidence_ref/diagnostic_kind remain sparse until follow-up row fill bundles land.",
    }:
        issues.append("matrix cell gap summary drifted")
    support_matrix_summary_entry = next(
        entry
        for entry in conformance_summary_mod.iter_representative_conformance_summary_handoff()
        if entry["summary_kind"] == conformance_summary_mod.CONFORMANCE_SUMMARY_KIND
    )
    if contract_mod.PARITY_MATRIX_SUMMARY_SOURCE != "conformance_summary_handoff.representative_summary_entries":
        issues.append("matrix summary source drifted away from conformance summary handoff")
    if contract_mod.PARITY_MATRIX_SUMMARY_KEYS != (
        "feature_id",
        "category",
        "fixture_class",
        "representative_fixture",
        "summary_kind",
        "shared_lanes",
        "backend_selectable_lanes",
        "backend_order",
        "runtime_lane_policy",
        "runtime_summary_source",
        "support_state_order",
        "downstream_task",
    ):
        issues.append("matrix summary keys drifted away from conformance summary handoff")
    if contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK != feature_contract_mod.HANDOFF_TASK_IDS["support_matrix"]:
        issues.append("matrix downstream task drifted away from feature contract handoff")
    if contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN != feature_contract_mod.HANDOFF_PLAN_PATHS["support_matrix"]:
        issues.append("matrix downstream plan drifted away from feature contract handoff")
    if set(contract_mod.PARITY_MATRIX_PUBLISH_PATHS.keys()) != {"docs_ja", "docs_en", "tool_manifest"}:
        issues.append("matrix publish paths must stay fixed to docs_ja/docs_en/tool_manifest")
    feature_ids = {entry["feature_id"] for entry in feature_contract_mod.iter_representative_support_matrix_handoff()}
    matrix_ids = {entry["feature_id"] for entry in contract_mod.iter_representative_parity_matrix_rows()}
    if matrix_ids != feature_ids:
        issues.append("matrix rows must cover exactly the representative support-matrix handoff inventory")
    for entry in contract_mod.iter_representative_parity_matrix_rows():
        if entry["backend_order"] != contract_mod.PARITY_MATRIX_BACKEND_ORDER:
            issues.append(f"{entry['feature_id']}: backend order drifted")
        if entry["support_state_order"] != contract_mod.PARITY_MATRIX_SUPPORT_STATE_ORDER:
            issues.append(f"{entry['feature_id']}: support state order drifted")
        if tuple(cell["backend"] for cell in entry["backend_cells"]) != contract_mod.PARITY_MATRIX_BACKEND_ORDER:
            issues.append(f"{entry['feature_id']}: backend cell order drifted")
        for cell in entry["backend_cells"]:
            allowed_kinds = contract_mod.PARITY_MATRIX_ALLOWED_EVIDENCE_KINDS_BY_STATE[cell["support_state"]]
            if cell["evidence_kind"] not in allowed_kinds:
                issues.append(
                    f"{entry['feature_id']}:{cell['backend']}: evidence kind {cell['evidence_kind']} is not allowed for {cell['support_state']}"
                )
        if entry["summary_source"] != contract_mod.PARITY_MATRIX_SUMMARY_SOURCE:
            issues.append(f"{entry['feature_id']}: summary source drifted")
        if entry["summary_keys"] != contract_mod.PARITY_MATRIX_SUMMARY_KEYS:
            issues.append(f"{entry['feature_id']}: summary keys drifted")
        if entry["downstream_task"] != contract_mod.PARITY_MATRIX_DOWNSTREAM_TASK:
            issues.append(f"{entry['feature_id']}: downstream task drifted")
        if entry["downstream_plan"] != contract_mod.PARITY_MATRIX_DOWNSTREAM_PLAN:
            issues.append(f"{entry['feature_id']}: downstream plan drifted")
    return issues


def _collect_docs_issues() -> list[str]:
    issues: list[str] = []
    expected_table = contract_mod.build_backend_parity_matrix_markdown_table()
    for path in DOC_TARGETS:
        text = path.read_text(encoding="utf-8")
        if contract_mod.PARITY_MATRIX_DOC_TABLE_BEGIN_MARKER not in text:
            issues.append(f"missing table begin marker in {path.relative_to(ROOT)}")
            continue
        if contract_mod.PARITY_MATRIX_DOC_TABLE_END_MARKER not in text:
            issues.append(f"missing table end marker in {path.relative_to(ROOT)}")
            continue
        rendered = text.split(contract_mod.PARITY_MATRIX_DOC_TABLE_BEGIN_MARKER, 1)[1]
        rendered = rendered.split(contract_mod.PARITY_MATRIX_DOC_TABLE_END_MARKER, 1)[0].strip()
        if rendered != expected_table:
            issues.append(f"backend parity matrix table drifted in {path.relative_to(ROOT)}")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_parity_matrix_manifest()
    if set(manifest.keys()) != {
        "inventory_version",
        "source_manifests",
        "source_destination",
        "implementation_phase",
        "cell_schema_status",
        "cell_schema",
        "cell_gap_summary",
        "backend_order",
        "support_state_order",
        "publish_paths",
        "summary_source",
        "summary_keys",
        "row_keys",
        "matrix_rows",
    }:
        issues.append("manifest keys drifted")
    if manifest["source_manifests"] != contract_mod.PARITY_MATRIX_SOURCE_MANIFESTS:
        issues.append("manifest source_manifests drifted")
    if manifest["source_destination"] != contract_mod.PARITY_MATRIX_SOURCE_DESTINATION:
        issues.append("manifest source_destination drifted")
    if manifest["implementation_phase"] != contract_mod.PARITY_MATRIX_IMPLEMENTATION_PHASE:
        issues.append("manifest implementation_phase drifted")
    if manifest["cell_schema_status"] != contract_mod.PARITY_MATRIX_CELL_SCHEMA_STATUS:
        issues.append("manifest cell_schema_status drifted")
    if manifest["cell_schema"] != {
        "schema_version": contract_mod.PARITY_MATRIX_CELL_SCHEMA_VERSION,
        "collection_key": contract_mod.PARITY_MATRIX_CELL_COLLECTION_KEY,
        "required_keys": list(contract_mod.PARITY_MATRIX_CELL_REQUIRED_KEYS),
        "optional_keys": list(contract_mod.PARITY_MATRIX_CELL_OPTIONAL_KEYS),
        "support_state_order": list(contract_mod.PARITY_MATRIX_SUPPORT_STATE_ORDER),
        "evidence_kind_order": list(contract_mod.PARITY_MATRIX_CELL_EVIDENCE_KIND_ORDER),
        "allowed_evidence_kinds_by_state": {
            state: list(kinds)
            for state, kinds in contract_mod.PARITY_MATRIX_ALLOWED_EVIDENCE_KINDS_BY_STATE.items()
        },
    }:
        issues.append("manifest cell_schema drifted")
    if manifest["cell_gap_summary"] != contract_mod.PARITY_MATRIX_CELL_GAP_SUMMARY:
        issues.append("manifest cell_gap_summary drifted")
    if manifest["backend_order"] != list(contract_mod.PARITY_MATRIX_BACKEND_ORDER):
        issues.append("manifest backend_order drifted")
    if manifest["support_state_order"] != list(contract_mod.PARITY_MATRIX_SUPPORT_STATE_ORDER):
        issues.append("manifest support_state_order drifted")
    if manifest["publish_paths"] != contract_mod.PARITY_MATRIX_PUBLISH_PATHS:
        issues.append("manifest publish_paths drifted")
    if manifest["summary_source"] != contract_mod.PARITY_MATRIX_SUMMARY_SOURCE:
        issues.append("manifest summary_source drifted")
    if manifest["summary_keys"] != list(contract_mod.PARITY_MATRIX_SUMMARY_KEYS):
        issues.append("manifest summary_keys drifted")
    if manifest["row_keys"] != list(contract_mod.PARITY_MATRIX_ROW_KEYS):
        issues.append("manifest row_keys drifted")
    if len(manifest["matrix_rows"]) != len(contract_mod.iter_representative_parity_matrix_rows()):
        issues.append("manifest matrix_rows length drifted")
    for entry in manifest["matrix_rows"]:
        if [cell["backend"] for cell in entry["backend_cells"]] != list(contract_mod.PARITY_MATRIX_BACKEND_ORDER):
            issues.append(f"{entry['feature_id']}: manifest backend_cells order drifted")
    return issues


def main() -> int:
    issues = _collect_contract_issues()
    issues.extend(_collect_manifest_issues())
    issues.extend(_collect_docs_issues())
    if issues:
        print("[NG] backend parity matrix contract drift detected")
        for issue in issues:
            print(f" - {issue}")
        return 1
    print("[OK] backend parity matrix contract is fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
