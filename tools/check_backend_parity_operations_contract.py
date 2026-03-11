from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod
from src.toolchain.compiler import backend_parity_handoff_contract as handoff_mod
from src.toolchain.compiler import backend_parity_operations_contract as contract_mod


def _collect_contract_issues() -> list[str]:
    issues: list[str] = []
    if contract_mod.PARITY_OPERATIONS_MAINTENANCE_ORDER != (
        "contract_seed",
        "docs_publish",
        "docs_entrypoints",
        "release_note_link",
        "tooling_export",
        "archive_handoff",
    ):
        issues.append("operations maintenance order drifted")
    if tuple(contract_mod.PARITY_OPERATIONS_DOC_LINK_PATHS[path_id] for path_id in contract_mod.PARITY_OPERATIONS_DOC_LINK_TARGETS) != (
        "docs/ja/index.md",
        "docs/en/index.md",
        "docs/ja/language/index.md",
        "docs/en/language/index.md",
        "docs/ja/README.md",
        "README.md",
        "docs/ja/news/index.md",
        "docs/en/news/index.md",
    ):
        issues.append("operations doc-link paths drifted")
    if contract_mod.PARITY_OPERATIONS_TOOLING_EXPORTS != (
        "tools/export_backend_parity_matrix_manifest.py",
        "tools/export_backend_parity_handoff_manifest.py",
    ):
        issues.append("operations tooling exports drifted")
    if contract_mod.PARITY_OPERATIONS_ARCHIVE_TARGETS != (
        "docs/ja/todo/archive/index.md",
        "docs/en/todo/archive/index.md",
        "docs/ja/plans/archive",
        "docs/en/plans/archive",
    ):
        issues.append("operations archive targets drifted")
    if contract_mod.PARITY_OPERATIONS_DOWNSTREAM_TASK != feature_contract_mod.HANDOFF_TASK_IDS["support_matrix"]:
        issues.append("operations downstream task drifted")
    if contract_mod.PARITY_OPERATIONS_DOWNSTREAM_PLAN != feature_contract_mod.HANDOFF_PLAN_PATHS["support_matrix"]:
        issues.append("operations downstream plan drifted")
    if tuple(entry["path"] for entry in contract_mod.iter_representative_backend_parity_operations_targets()) != tuple(contract_mod.PARITY_OPERATIONS_DOC_LINK_PATHS[path_id] for path_id in contract_mod.PARITY_OPERATIONS_DOC_LINK_TARGETS):
        issues.append("operations target paths drifted from doc-link path map")
    return issues


def _collect_filesystem_issues() -> list[str]:
    issues: list[str] = []
    root = ROOT
    for target_id, relpath in contract_mod.PARITY_OPERATIONS_DOC_LINK_PATHS.items():
        abspath = root / relpath
        if not abspath.exists():
            issues.append(f"missing operations target file: {relpath}")
            continue
        content = abspath.read_text(encoding="utf-8")
        required_link = contract_mod.PARITY_OPERATIONS_DOC_LINK_TARGETS[target_id]
        if required_link not in content:
            issues.append(f"missing parity matrix link in operations target: {relpath}")
    for relpath in contract_mod.PARITY_OPERATIONS_ARCHIVE_TARGETS:
        if not (root / relpath).exists():
            issues.append(f"missing archive target path: {relpath}")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_parity_operations_manifest()
    if set(manifest.keys()) != {
        "inventory_version",
        "maintenance_order",
        "doc_link_targets",
        "doc_link_paths",
        "tooling_exports",
        "archive_targets",
        "rules",
        "handoff_doc_targets",
        "handoff_release_note_targets",
        "downstream_task",
        "downstream_plan",
        "operations_targets",
    }:
        issues.append("operations manifest keys drifted")
    if manifest["maintenance_order"] != list(contract_mod.PARITY_OPERATIONS_MAINTENANCE_ORDER):
        issues.append("operations manifest maintenance_order drifted")
    if manifest["doc_link_targets"] != contract_mod.PARITY_OPERATIONS_DOC_LINK_TARGETS:
        issues.append("operations manifest doc_link_targets drifted")
    if manifest["doc_link_paths"] != contract_mod.PARITY_OPERATIONS_DOC_LINK_PATHS:
        issues.append("operations manifest doc_link_paths drifted")
    if manifest["tooling_exports"] != list(contract_mod.PARITY_OPERATIONS_TOOLING_EXPORTS):
        issues.append("operations manifest tooling_exports drifted")
    if manifest["archive_targets"] != list(contract_mod.PARITY_OPERATIONS_ARCHIVE_TARGETS):
        issues.append("operations manifest archive_targets drifted")
    if manifest["rules"] != contract_mod.PARITY_OPERATIONS_RULES:
        issues.append("operations manifest rules drifted")
    if manifest["handoff_doc_targets"] != list(handoff_mod.PARITY_HANDOFF_DOC_TARGETS):
        issues.append("operations manifest handoff_doc_targets drifted")
    if manifest["handoff_release_note_targets"] != list(handoff_mod.PARITY_HANDOFF_RELEASE_NOTE_TARGETS):
        issues.append("operations manifest handoff_release_note_targets drifted")
    if manifest["downstream_task"] != contract_mod.PARITY_OPERATIONS_DOWNSTREAM_TASK:
        issues.append("operations manifest downstream_task drifted")
    if manifest["downstream_plan"] != contract_mod.PARITY_OPERATIONS_DOWNSTREAM_PLAN:
        issues.append("operations manifest downstream_plan drifted")
    if len(manifest["operations_targets"]) != len(contract_mod.iter_representative_backend_parity_operations_targets()):
        issues.append("operations manifest target length drifted")
    return issues


def main() -> int:
    issues = _collect_contract_issues()
    issues.extend(_collect_filesystem_issues())
    issues.extend(_collect_manifest_issues())
    if issues:
        print("[NG] backend parity operations contract drift detected")
        for issue in issues:
            print(f" - {issue}")
        return 1
    print("[OK] backend parity operations contract is fixed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
