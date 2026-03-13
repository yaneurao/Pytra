from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import multilang_extern_runtime_realign_inventory as inventory_mod


def _load_manifest_by_id() -> dict[str, dict[str, object]]:
    manifest = json.loads((ROOT / "tools/runtime_generation_manifest.json").read_text(encoding="utf-8"))
    return {item["id"]: item for item in manifest["items"]}


def _collect_inventory_issues() -> list[str]:
    issues: list[str] = []
    rows = inventory_mod.iter_multilang_extern_runtime_realign_inventory()
    if tuple(row["module_id"] for row in rows) != inventory_mod.MODULE_ORDER:
        issues.append("module order drifted from fixed inventory order")
    seen: set[str] = set()
    buckets: set[str] = set()
    for row in rows:
        module_id = row["module_id"]
        if module_id in seen:
            issues.append(f"duplicate module id: {module_id}")
        seen.add(module_id)
        bucket = row["bucket"]
        if bucket not in inventory_mod.BUCKET_ORDER:
            issues.append(f"unknown bucket: {module_id}: {bucket}")
        buckets.add(bucket)
        if not (ROOT / row["source_rel"]).exists():
            issues.append(f"missing source path: {module_id}: {row['source_rel']}")
    if buckets != set(inventory_mod.BUCKET_ORDER):
        issues.append("bucket coverage drifted from fixed taxonomy")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest_by_id = _load_manifest_by_id()
    for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory():
        module_id = row["module_id"]
        item = manifest_by_id.get(module_id)
        if item is None:
            issues.append(f"manifest item missing: {module_id}")
            continue
        if item.get("source") != row["source_rel"]:
            issues.append(f"manifest source drifted: {module_id}")
        actual_postprocess = tuple(
            f"{target['target']}:{target['postprocess']}"
            for target in item["targets"]
            if "postprocess" in target
        )
        if actual_postprocess != row["manifest_postprocess_targets"]:
            issues.append(f"manifest postprocess targets drifted: {module_id}")
    return issues


def _collect_native_owner_issues() -> list[str]:
    issues: list[str] = []
    for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory():
        module_id = row["module_id"]
        if not row["cpp_native_owner_paths"]:
            issues.append(f"cpp native owner missing from inventory: {module_id}")
        for rel in row["cpp_native_owner_paths"] + row["noncpp_native_owner_paths"]:
            if not (ROOT / rel).exists():
                issues.append(f"missing native owner path: {module_id}: {rel}")
    return issues


def _collect_emitter_hardcode_issues() -> list[str]:
    issues: list[str] = []
    for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory():
        module_id = row["module_id"]
        for rel, needle in row["emitter_hardcode_needles"]:
            path = ROOT / rel
            if not path.exists():
                issues.append(f"missing emitter hardcode path: {module_id}: {rel}")
                continue
            text = path.read_text(encoding="utf-8")
            if needle not in text:
                issues.append(f"missing emitter hardcode needle: {module_id}: {rel}: {needle}")
    return issues


def _collect_generated_drift_issues() -> list[str]:
    issues: list[str] = []
    for row in inventory_mod.iter_multilang_extern_runtime_realign_inventory():
        module_id = row["module_id"]
        for rel, needle in row["generated_drift_needles"]:
            path = ROOT / rel
            if not path.exists():
                issues.append(f"missing generated drift path: {module_id}: {rel}")
                continue
            text = path.read_text(encoding="utf-8")
            if needle not in text:
                issues.append(f"missing generated drift needle: {module_id}: {rel}: {needle}")
    return issues


def main() -> int:
    issues = (
        _collect_inventory_issues()
        + _collect_manifest_issues()
        + _collect_native_owner_issues()
        + _collect_emitter_hardcode_issues()
        + _collect_generated_drift_issues()
    )
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] multilang extern runtime realign inventory is locked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
