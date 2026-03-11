from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import backend_conformance_harness_contract as harness_mod
from src.toolchain.compiler import backend_conformance_runner_contract as contract_mod
from src.toolchain.compiler import backend_feature_contract_inventory as feature_contract_mod


def _collect_runner_inventory_issues() -> list[str]:
    issues: list[str] = []
    seen_backends: set[str] = set()
    if contract_mod.REPRESENTATIVE_CONFORMANCE_RUNNER_BACKENDS != feature_contract_mod.FIRST_CONFORMANCE_BACKEND_ORDER:
        issues.append("representative conformance runner backend order drifted from the fixed set")
    if contract_mod.BACKEND_SELECTABLE_RUNNER_LANES != harness_mod.BACKEND_SELECTABLE_CONFORMANCE_LANES:
        issues.append("backend-selectable runner lanes drifted from the shared harness contract")
    if set(contract_mod.RUNNER_LANE_ENTRYPOINTS.keys()) != set(contract_mod.BACKEND_SELECTABLE_RUNNER_LANES):
        issues.append("runner lane entrypoints drifted from the selectable lane set")
    if set(contract_mod.RUNNER_SMOKE_FILES.keys()) != set(contract_mod.REPRESENTATIVE_CONFORMANCE_RUNNER_BACKENDS):
        issues.append("runner smoke files drifted from the representative backend set")
    for lane, entrypoint in sorted(contract_mod.RUNNER_LANE_ENTRYPOINTS.items()):
        if entrypoint.strip() == "":
            issues.append(f"runner lane entrypoint is empty: {lane}")
        elif not (ROOT / entrypoint).exists():
            issues.append(f"runner lane entrypoint is missing: {lane}: {entrypoint}")
    for backend, smoke_file in sorted(contract_mod.RUNNER_SMOKE_FILES.items()):
        if smoke_file.strip() == "":
            issues.append(f"runner smoke file is empty: {backend}")
        elif not (ROOT / smoke_file).exists():
            issues.append(f"runner smoke file is missing: {backend}: {smoke_file}")
    for entry in contract_mod.iter_representative_conformance_runner_inventory():
        backend = entry["backend"]
        if backend in seen_backends:
            issues.append(f"duplicate runner backend: {backend}")
        else:
            seen_backends.add(backend)
        if backend not in contract_mod.REPRESENTATIVE_CONFORMANCE_RUNNER_BACKENDS:
            issues.append(f"unknown runner backend: {backend}")
            continue
        if entry["selectable_lanes"] != contract_mod.BACKEND_SELECTABLE_RUNNER_LANES:
            issues.append(f"runner selectable lanes drifted: {backend}")
        if entry["emit_target"] != backend:
            issues.append(f"runner emit target drifted: {backend}")
        if entry["runtime_target"] != backend:
            issues.append(f"runner runtime target drifted: {backend}")
        if entry["emit_entrypoint"] != contract_mod.RUNNER_LANE_ENTRYPOINTS["emit"]:
            issues.append(f"runner emit entrypoint drifted: {backend}")
        if entry["runtime_entrypoint"] != contract_mod.RUNNER_LANE_ENTRYPOINTS["runtime"]:
            issues.append(f"runner runtime entrypoint drifted: {backend}")
        if entry["smoke_file"] != contract_mod.RUNNER_SMOKE_FILES[backend]:
            issues.append(f"runner smoke file drifted: {backend}")
    if seen_backends != set(contract_mod.REPRESENTATIVE_CONFORMANCE_RUNNER_BACKENDS):
        issues.append("representative conformance runner inventory drifted from the fixed backend set")
    return issues


def _collect_manifest_issues() -> list[str]:
    issues: list[str] = []
    manifest = contract_mod.build_backend_conformance_runner_manifest()
    if set(manifest.keys()) != {
        "inventory_version",
        "backend_order",
        "selectable_lanes",
        "lane_entrypoints",
        "runner_inventory",
    }:
        issues.append("conformance runner manifest keys drifted from the fixed set")
    if manifest.get("inventory_version") != 1:
        issues.append("conformance runner manifest inventory_version must stay at 1")
    if manifest["backend_order"] != list(contract_mod.REPRESENTATIVE_CONFORMANCE_RUNNER_BACKENDS):
        issues.append("conformance runner backend order drifted from the fixed set")
    if manifest["selectable_lanes"] != list(contract_mod.BACKEND_SELECTABLE_RUNNER_LANES):
        issues.append("conformance runner selectable lanes drifted from the fixed set")
    if manifest["lane_entrypoints"] != dict(contract_mod.RUNNER_LANE_ENTRYPOINTS):
        issues.append("conformance runner lane entrypoints drifted from the fixed set")
    if manifest["runner_inventory"] != [
        {
            "backend": entry["backend"],
            "selectable_lanes": list(entry["selectable_lanes"]),
            "emit_target": entry["emit_target"],
            "runtime_target": entry["runtime_target"],
            "emit_entrypoint": entry["emit_entrypoint"],
            "runtime_entrypoint": entry["runtime_entrypoint"],
            "smoke_file": entry["smoke_file"],
        }
        for entry in contract_mod.iter_representative_conformance_runner_inventory()
    ]:
        issues.append("conformance runner inventory drifted from the fixed set")
    return issues


def main() -> int:
    issues = _collect_runner_inventory_issues() + _collect_manifest_issues()
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] backend conformance runner contract is classified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
