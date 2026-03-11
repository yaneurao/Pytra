from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_conformance_inventory as inventory_mod
from src.toolchain.compiler import backend_conformance_runtime_parity_contract as contract_mod


def _collect_runtime_strategy_issues() -> list[str]:
    issues: list[str] = []
    stdlib_entries = [
        entry for entry in inventory_mod.iter_representative_conformance_fixture_inventory() if entry["fixture_class"] == "pytra_std"
    ]
    if tuple(entry["feature_id"] for entry in contract_mod.iter_representative_stdlib_runtime_parity()) != tuple(
        entry["feature_id"] for entry in stdlib_entries
    ):
        issues.append("stdlib runtime parity feature order drifted from the representative conformance inventory")
    for entry in contract_mod.iter_representative_stdlib_runtime_parity():
        fixture_rel = entry["representative_fixture"]
        feature_id = entry["feature_id"]
        if entry["strategy_kind"] != contract_mod.STDLIB_RUNTIME_PARITY_STRATEGY_KIND:
            issues.append(f"stdlib runtime strategy kind drifted: {feature_id}")
        if entry["case_root"] != contract_mod.STDLIB_RUNTIME_CASE_ROOT:
            issues.append(f"stdlib runtime case root drifted: {feature_id}")
        if entry["runner_lane"] != contract_mod.STDLIB_RUNTIME_RUNNER_LANE:
            issues.append(f"stdlib runtime lane drifted: {feature_id}")
        if entry["runner_entrypoint"] != contract_mod.STDLIB_RUNTIME_RUNNER_ENTRYPOINT:
            issues.append(f"stdlib runtime runner entrypoint drifted: {feature_id}")
        if entry["compare_unit"] != contract_mod.STDLIB_RUNTIME_COMPARE_UNIT:
            issues.append(f"stdlib runtime compare unit drifted: {feature_id}")
        if entry["representative_backends"] != contract_mod.STDLIB_RUNTIME_BACKEND_ORDER:
            issues.append(f"stdlib runtime backend order drifted: {feature_id}")
        if entry["case_stem"] != Path(fixture_rel).stem:
            issues.append(f"stdlib runtime case stem drifted from fixture stem: {feature_id}")
        if entry["module_name"] != feature_id.split(".", 2)[1]:
            issues.append(f"stdlib runtime module name drifted from feature id: {feature_id}")
        if not (ROOT / fixture_rel).exists():
            issues.append(f"stdlib runtime representative fixture is missing: {feature_id}: {fixture_rel}")
    pytra_std_runtime_policy = next(
        entry["lane_policy"]["runtime"]
        for entry in inventory_mod.iter_conformance_fixture_lane_policy()
        if entry["fixture_class"] == "pytra_std"
    )
    if pytra_std_runtime_policy != "module_runtime_strategy":
        issues.append("pytra_std runtime lane policy must stay on module_runtime_strategy")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_conformance_runtime_parity_manifest()
    if set(manifest.keys()) != {
        "inventory_version",
        "strategy_kind",
        "case_root",
        "runner_lane",
        "runner_entrypoint",
        "compare_unit",
        "backend_order",
        "stdlib_runtime_modules",
    }:
        issues.append("stdlib runtime parity manifest keys drifted from the fixed set")
    if manifest.get("inventory_version") != 1:
        issues.append("stdlib runtime parity manifest inventory_version must stay at 1")
    if manifest["strategy_kind"] != contract_mod.STDLIB_RUNTIME_PARITY_STRATEGY_KIND:
        issues.append("stdlib runtime parity manifest strategy kind drifted from the fixed set")
    if manifest["case_root"] != contract_mod.STDLIB_RUNTIME_CASE_ROOT:
        issues.append("stdlib runtime parity manifest case root drifted from the fixed set")
    if manifest["runner_lane"] != contract_mod.STDLIB_RUNTIME_RUNNER_LANE:
        issues.append("stdlib runtime parity manifest runner lane drifted from the fixed set")
    if manifest["runner_entrypoint"] != contract_mod.STDLIB_RUNTIME_RUNNER_ENTRYPOINT:
        issues.append("stdlib runtime parity manifest runner entrypoint drifted from the fixed set")
    if manifest["compare_unit"] != contract_mod.STDLIB_RUNTIME_COMPARE_UNIT:
        issues.append("stdlib runtime parity manifest compare unit drifted from the fixed set")
    if manifest["backend_order"] != list(contract_mod.STDLIB_RUNTIME_BACKEND_ORDER):
        issues.append("stdlib runtime parity manifest backend order drifted from the fixed set")
    if manifest["stdlib_runtime_modules"] != [
        {
            "feature_id": entry["feature_id"],
            "module_name": entry["module_name"],
            "case_stem": entry["case_stem"],
            "representative_fixture": entry["representative_fixture"],
            "strategy_kind": entry["strategy_kind"],
            "case_root": entry["case_root"],
            "runner_lane": entry["runner_lane"],
            "runner_entrypoint": entry["runner_entrypoint"],
            "compare_unit": entry["compare_unit"],
            "representative_backends": list(entry["representative_backends"]),
        }
        for entry in contract_mod.iter_representative_stdlib_runtime_parity()
    ]:
        issues.append("stdlib runtime parity manifest module inventory drifted from the fixed set")
    return issues


def main() -> int:
    issues = _collect_runtime_strategy_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend conformance stdlib runtime parity contract is classified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
