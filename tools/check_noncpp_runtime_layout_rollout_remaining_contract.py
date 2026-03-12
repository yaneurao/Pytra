#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC_ROOT = ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from src.toolchain.compiler import backend_registry_metadata
from src.toolchain.compiler import noncpp_runtime_layout_rollout_remaining_contract as contract_mod


_VALID_OWNERSHIP = ("native", "generated", "compat")
_VALID_TARGET_ROOTS = ("generated", "native", "pytra")


def _runtime_hook_key_for_backend(backend: str) -> str:
    descriptor = backend_registry_metadata.get_backend_descriptor(backend)
    runtime_hook_key = descriptor.get("runtime_hook_key")
    return runtime_hook_key if isinstance(runtime_hook_key, str) else ""


def _runtime_root_path(backend: str, root_name: str) -> Path:
    return ROOT / "src" / "runtime" / backend / root_name


def _collect_relative_files(base: Path) -> tuple[str, ...]:
    if not base.exists():
        return ()
    return tuple(
        sorted(
            str(path.relative_to(base)).replace("\\", "/")
            for path in base.rglob("*")
            if path.is_file()
        )
    )


def _collect_contract_issues() -> list[str]:
    issues: list[str] = []
    entries = contract_mod.iter_remaining_noncpp_runtime_layout()
    backend_order = tuple(entry["backend"] for entry in entries)
    if backend_order != contract_mod.iter_remaining_noncpp_backend_order():
        issues.append("remaining non-c++ backend order drifted")

    seen_backends: set[str] = set()
    for entry in entries:
        backend = entry["backend"]
        if backend in seen_backends:
            issues.append(f"duplicate backend entry: {backend}")
            continue
        seen_backends.add(backend)

        runtime_hook_key = entry["runtime_hook_key"]
        if runtime_hook_key != _runtime_hook_key_for_backend(backend):
            issues.append(f"runtime hook key drifted: {backend}: {runtime_hook_key}")

        current_roots = entry["current_roots"]
        actual_current_roots = tuple(
            sorted(
                path.name
                for path in (ROOT / "src" / "runtime" / backend).iterdir()
                if path.is_dir()
            )
        )
        if tuple(sorted(current_roots)) != actual_current_roots:
            issues.append(f"current roots drifted: {backend}")

        if entry["target_roots"] != _VALID_TARGET_ROOTS:
            issues.append(f"target roots drifted: {backend}")

        seen_current_prefixes: set[str] = set()
        for lane in entry["lane_mappings"]:
            current_prefix = lane["current_prefix"]
            target_prefix = lane["target_prefix"]
            ownership = lane["ownership"]

            if ownership not in _VALID_OWNERSHIP:
                issues.append(f"unknown ownership: {backend}: {current_prefix}: {ownership}")
                continue

            if current_prefix in seen_current_prefixes:
                issues.append(f"duplicate current prefix: {backend}: {current_prefix}")
            seen_current_prefixes.add(current_prefix)

            current_prefix_path = ROOT / current_prefix
            if not current_prefix_path.exists():
                issues.append(f"missing current prefix: {backend}: {current_prefix}")

            if not current_prefix.startswith(f"src/runtime/{backend}/"):
                issues.append(f"current prefix escaped backend root: {backend}: {current_prefix}")
            if not target_prefix.startswith(f"src/runtime/{backend}/"):
                issues.append(f"target prefix escaped backend root: {backend}: {target_prefix}")

            current_root = current_prefix.removeprefix(f"src/runtime/{backend}/").split("/", 1)[0]
            target_root = target_prefix.removeprefix(f"src/runtime/{backend}/").split("/", 1)[0]
            if current_root not in current_roots:
                issues.append(f"current prefix root drifted: {backend}: {current_prefix}")
            if target_root not in _VALID_TARGET_ROOTS:
                issues.append(f"target prefix root drifted: {backend}: {target_prefix}")

            if ownership == "generated" and target_root != "generated":
                issues.append(f"generated lane target drifted: {backend}: {target_prefix}")
            if ownership == "native" and target_root != "native":
                issues.append(f"native lane target drifted: {backend}: {target_prefix}")
            if ownership == "compat" and target_root != "pytra":
                issues.append(f"compat lane target drifted: {backend}: {target_prefix}")

            rationale = lane["rationale"].strip()
            if not rationale:
                issues.append(f"empty rationale: {backend}: {current_prefix}")

    if seen_backends != set(contract_mod.iter_remaining_noncpp_backend_order()):
        issues.append("remaining non-c++ backend set drifted")
    return issues


def _collect_current_inventory_issues() -> list[str]:
    issues: list[str] = []
    inventory_entries = contract_mod.iter_remaining_noncpp_runtime_current_inventory()
    inventory_order = tuple(entry["backend"] for entry in inventory_entries)
    if inventory_order != contract_mod.iter_remaining_noncpp_backend_order():
        issues.append("remaining runtime current inventory order drifted")

    layout_backends = {
        entry["backend"] for entry in contract_mod.iter_remaining_noncpp_runtime_layout()
    }
    inventory_backends = {entry["backend"] for entry in inventory_entries}
    if inventory_backends != layout_backends:
        issues.append("remaining runtime current inventory backend set drifted")

    for entry in inventory_entries:
        backend = entry["backend"]
        runtime_root = ROOT / "src" / "runtime" / backend
        if _collect_relative_files(runtime_root / "pytra-core") != entry["pytra_core_files"]:
            issues.append(f"pytra-core inventory drifted: {backend}")
        if _collect_relative_files(runtime_root / "pytra-gen") != entry["pytra_gen_files"]:
            issues.append(f"pytra-gen inventory drifted: {backend}")
        if _collect_relative_files(runtime_root / "pytra") != entry["pytra_files"]:
            issues.append(f"pytra inventory drifted: {backend}")
    return issues


def main() -> int:
    issues = _collect_contract_issues()
    issues.extend(_collect_current_inventory_issues())
    if issues:
        print("non-c++ runtime layout rollout remaining contract check failed:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    print("non-c++ runtime layout rollout remaining contract check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
