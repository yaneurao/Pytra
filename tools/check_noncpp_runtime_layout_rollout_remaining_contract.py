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


def _inventory_root_by_key(backend: str) -> dict[str, str]:
    layout_entry = next(
        entry for entry in contract_mod.iter_remaining_noncpp_runtime_layout() if entry["backend"] == backend
    )
    current_roots = set(layout_entry["current_roots"])
    if {"generated", "native", "pytra"}.issubset(current_roots):
        return {
            "pytra_core_files": "native",
            "pytra_gen_files": "generated",
            "pytra_files": "pytra",
        }
    return {
        "pytra_core_files": "pytra-core",
        "pytra_gen_files": "pytra-gen",
        "pytra_files": "pytra",
    }


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
        if not set(current_roots).issubset(actual_current_roots):
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
            target_prefix_path = ROOT / target_prefix
            if not current_prefix_path.exists() and not target_prefix_path.exists():
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
        root_by_key = _inventory_root_by_key(backend)
        current_core = _collect_relative_files(runtime_root / root_by_key["pytra_core_files"])
        current_gen = _collect_relative_files(runtime_root / root_by_key["pytra_gen_files"])
        current_pytra = _collect_relative_files(runtime_root / root_by_key["pytra_files"])
        if (
            current_core == entry["pytra_core_files"]
            and current_gen == entry["pytra_gen_files"]
            and current_pytra == entry["pytra_files"]
        ):
            continue

        expanded = _expand_target_inventory_for_backend(backend)
        actual_generated = _collect_relative_files(runtime_root / "generated")
        actual_native = _collect_relative_files(runtime_root / "native")
        actual_compat = _collect_relative_files(runtime_root / "pytra")
        expected_generated = tuple(
            path.removeprefix("generated/") for path in expanded["generated"]
        )
        expected_native = tuple(
            path.removeprefix("native/") for path in expanded["native"]
        )
        expected_compat = tuple(
            path.removeprefix("pytra/") for path in expanded["compat"]
        )
        if (
            expected_generated == actual_generated
            and expected_native == actual_native
            and expected_compat == actual_compat
        ):
            continue

        if current_core != entry["pytra_core_files"]:
            issues.append(f"{root_by_key['pytra_core_files']} inventory drifted: {backend}")
        if current_gen != entry["pytra_gen_files"]:
            issues.append(f"{root_by_key['pytra_gen_files']} inventory drifted: {backend}")
        if current_pytra != entry["pytra_files"]:
            issues.append(f"pytra inventory drifted: {backend}")
    return issues


def _expand_target_inventory_for_backend(backend: str) -> dict[str, tuple[str, ...]]:
    layout_entry = next(
        entry for entry in contract_mod.iter_remaining_noncpp_runtime_layout() if entry["backend"] == backend
    )
    inventory_entry = next(
        entry for entry in contract_mod.iter_remaining_noncpp_runtime_current_inventory() if entry["backend"] == backend
    )
    lane_root_by_key = _inventory_root_by_key(backend)
    expanded: dict[str, list[str]] = {"generated": [], "native": [], "compat": []}
    lane_mappings = tuple(
        sorted(layout_entry["lane_mappings"], key=lambda lane: len(lane["current_prefix"]), reverse=True)
    )
    for inventory_key, root_name in lane_root_by_key.items():
        for rel_path in inventory_entry[inventory_key]:
            current_path = f"src/runtime/{backend}/{root_name}/{rel_path}"
            matched_lane = None
            for lane in lane_mappings:
                if current_path.startswith(lane["current_prefix"]):
                    matched_lane = lane
                    break
            if matched_lane is None:
                raise AssertionError(f"unmatched current runtime path: {current_path}")
            target_path = current_path.replace(
                matched_lane["current_prefix"],
                matched_lane["target_prefix"],
                1,
            ).removeprefix(f"src/runtime/{backend}/")
            expanded[matched_lane["ownership"]].append(target_path)
    return {
        ownership: tuple(sorted(paths))
        for ownership, paths in expanded.items()
    }


def _normalize_target_module_label(rel_path: str) -> str | None:
    if rel_path.endswith("README.md"):
        return None
    parts = rel_path.split("/")
    if not parts:
        return None
    root = parts[0]
    if root in ("generated", "native") and len(parts) >= 3:
        bucket = parts[1]
        stem = Path(parts[2]).stem
    elif root == "pytra":
        if len(parts) == 2:
            stem = Path(parts[1]).stem
            if stem == "py_runtime":
                return "built_in/py_runtime"
            if stem in ("math", "pathlib", "time"):
                return f"std/{stem}"
            if stem in ("gif", "png"):
                return f"utils/{stem}"
            return None
        if len(parts) >= 3:
            bucket = parts[1]
            stem = Path(parts[2]).stem
        else:
            return None
    else:
        return None
    if stem == "PyRuntime":
        stem = "py_runtime"
    if stem.endswith("_impl"):
        stem = stem[:-5]
    return f"{bucket}/{stem}"


def _collect_target_module_buckets_for_backend(backend: str) -> dict[str, tuple[str, ...]]:
    target_inventory = next(
        entry for entry in contract_mod.iter_remaining_noncpp_runtime_target_inventory() if entry["backend"] == backend
    )
    buckets: dict[str, set[str]] = {"generated": set(), "native": set(), "compat": set()}
    for ownership, inventory_key in (
        ("generated", "generated_files"),
        ("native", "native_files"),
        ("compat", "compat_files"),
    ):
        for rel_path in target_inventory[inventory_key]:
            label = _normalize_target_module_label(rel_path)
            if label is not None:
                buckets[ownership].add(label)
    return {
        ownership: tuple(sorted(labels))
        for ownership, labels in buckets.items()
    }


def _collect_target_inventory_issues() -> list[str]:
    issues: list[str] = []
    inventory_entries = contract_mod.iter_remaining_noncpp_runtime_target_inventory()
    inventory_order = tuple(entry["backend"] for entry in inventory_entries)
    if inventory_order != contract_mod.iter_remaining_noncpp_backend_order():
        issues.append("remaining runtime target inventory order drifted")
    for entry in inventory_entries:
        backend = entry["backend"]
        expanded = _expand_target_inventory_for_backend(backend)
        if expanded["generated"] != entry["generated_files"]:
            issues.append(f"generated target inventory drifted: {backend}")
        if expanded["native"] != entry["native_files"]:
            issues.append(f"native target inventory drifted: {backend}")
        if expanded["compat"] != entry["compat_files"]:
            issues.append(f"compat target inventory drifted: {backend}")
    return issues


def _collect_wave_a_runtime_hook_issues() -> list[str]:
    issues: list[str] = []
    for entry in contract_mod.iter_remaining_noncpp_runtime_wave_a_hook_sources():
        backend = entry["backend"]
        descriptor = backend_registry_metadata.get_runtime_hook_descriptor(
            _runtime_hook_key_for_backend(backend)
        )
        if descriptor.get("kind") != "copy_files":
            issues.append(f"wave-a runtime hook kind drifted: {backend}")
            continue
        actual_sources: list[str] = []
        files = descriptor.get("files")
        if isinstance(files, list):
            for item in files:
                if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str):
                    actual_sources.append(item[0])
                if isinstance(item, list) and len(item) == 2 and isinstance(item[0], str):
                    actual_sources.append(item[0])
        if tuple(actual_sources) != entry["runtime_hook_files"]:
            issues.append(f"wave-a runtime hook files drifted: {backend}")
    return issues


def _collect_module_bucket_issues() -> list[str]:
    issues: list[str] = []
    compare_baseline = set(contract_mod.iter_remaining_noncpp_runtime_generated_compare_baseline())
    entries = contract_mod.iter_remaining_noncpp_runtime_module_buckets()
    bucket_order = tuple(entry["backend"] for entry in entries)
    if bucket_order != contract_mod.iter_remaining_noncpp_backend_order():
        issues.append("remaining runtime module bucket order drifted")
    for entry in entries:
        backend = entry["backend"]
        actual = _collect_target_module_buckets_for_backend(backend)
        if actual["generated"] != entry["generated_modules"]:
            issues.append(f"generated module bucket drifted: {backend}")
        if actual["native"] != entry["native_modules"]:
            issues.append(f"native module bucket drifted: {backend}")
        if actual["compat"] != entry["compat_modules"]:
            issues.append(f"compat module bucket drifted: {backend}")
        blocked = set(entry["blocked_modules"])
        if not blocked.issubset(compare_baseline):
            issues.append(f"blocked compare module escaped baseline: {backend}")
        if blocked & set(entry["generated_modules"]):
            issues.append(f"blocked/generated overlap drifted: {backend}")
        covered = set(entry["generated_modules"]).intersection(compare_baseline)
        if covered.union(blocked) != compare_baseline:
            issues.append(f"generated compare baseline coverage drifted: {backend}")
    return issues


def _collect_wave_b_blocked_reason_issues() -> list[str]:
    issues: list[str] = []
    module_buckets = {
        entry["backend"]: entry
        for entry in contract_mod.iter_remaining_noncpp_runtime_module_buckets()
    }
    entries = contract_mod.iter_remaining_noncpp_runtime_wave_b_blocked_reasons()
    if tuple(entry["backend"] for entry in entries) != ("js", "ts", "lua", "ruby", "php"):
        issues.append("wave-b blocked reason order drifted")
    for entry in entries:
        backend = entry["backend"]
        bucket = module_buckets.get(backend)
        if bucket is None:
            issues.append(f"wave-b blocked reason backend drifted: {backend}")
            continue
        missing_modules = set(entry["missing_compare_lane_modules"])
        native_residual_modules = set(entry["native_compare_residual_modules"])
        helper_gap_modules = set(entry["helper_shaped_compare_gap_modules"])
        if missing_modules & native_residual_modules:
            issues.append(f"wave-b blocked reason overlap drifted: {backend}: missing/native")
        if missing_modules & helper_gap_modules:
            issues.append(f"wave-b blocked reason overlap drifted: {backend}: missing/helper")
        if native_residual_modules & helper_gap_modules:
            issues.append(f"wave-b blocked reason overlap drifted: {backend}: native/helper")

        blocked_modules = set(bucket["blocked_modules"])
        reason_union = missing_modules.union(native_residual_modules).union(helper_gap_modules)
        if reason_union != blocked_modules:
            issues.append(f"wave-b blocked reason coverage drifted: {backend}")

        native_modules = set(bucket["native_modules"])
        generated_modules = set(bucket["generated_modules"])
        if not native_residual_modules.issubset(native_modules):
            issues.append(f"wave-b native residual reason escaped native bucket: {backend}")
        if missing_modules & native_modules:
            issues.append(f"wave-b missing reason overlaps native bucket: {backend}")
        if missing_modules & generated_modules:
            issues.append(f"wave-b missing reason overlaps generated bucket: {backend}")
        if helper_gap_modules & native_modules:
            issues.append(f"wave-b helper-gap reason overlaps native bucket: {backend}")
        if helper_gap_modules & generated_modules:
            issues.append(f"wave-b helper-gap reason overlaps generated bucket: {backend}")
    return issues


def _collect_wave_b_generated_compare_issues() -> list[str]:
    issues: list[str] = []
    module_buckets = {
        entry["backend"]: entry
        for entry in contract_mod.iter_remaining_noncpp_runtime_module_buckets()
    }
    entries = contract_mod.iter_remaining_noncpp_runtime_wave_b_generated_compare()
    if tuple(entry["backend"] for entry in entries) != ("js", "ts", "lua", "ruby", "php"):
        issues.append("wave-b generated compare order drifted")
    compare_baseline = set(contract_mod.iter_remaining_noncpp_runtime_generated_compare_baseline())
    for entry in entries:
        backend = entry["backend"]
        bucket = module_buckets.get(backend)
        if bucket is None:
            issues.append(f"wave-b generated compare backend drifted: {backend}")
            continue
        generated_modules = set(bucket["generated_modules"])
        blocked_modules = set(bucket["blocked_modules"])
        native_modules = set(bucket["native_modules"])
        materialized_modules = set(entry["materialized_compare_modules"])
        helper_artifact_modules = set(entry["helper_artifact_modules"])
        if materialized_modules & helper_artifact_modules:
            issues.append(f"wave-b generated compare overlap drifted: {backend}")
        expected_materialized = generated_modules.intersection(compare_baseline)
        if materialized_modules != expected_materialized:
            issues.append(f"wave-b materialized compare modules drifted: {backend}")
        expected_helper_artifacts = generated_modules.difference(compare_baseline)
        if helper_artifact_modules != expected_helper_artifacts:
            issues.append(f"wave-b helper artifact modules drifted: {backend}")
        if materialized_modules & blocked_modules:
            issues.append(f"wave-b materialized compare overlaps blocked bucket: {backend}")
        if helper_artifact_modules & blocked_modules:
            issues.append(f"wave-b helper artifact overlaps blocked bucket: {backend}")
        if helper_artifact_modules & native_modules:
            issues.append(f"wave-b helper artifact overlaps native bucket: {backend}")
    return issues


def _collect_wave_b_native_residual_issues() -> list[str]:
    issues: list[str] = []
    module_buckets = {
        entry["backend"]: entry
        for entry in contract_mod.iter_remaining_noncpp_runtime_module_buckets()
    }
    entries = contract_mod.iter_remaining_noncpp_runtime_wave_b_native_residuals()
    if tuple(entry["backend"] for entry in entries) != ("js", "ts", "lua", "ruby", "php"):
        issues.append("wave-b native residual order drifted")
    for entry in entries:
        backend = entry["backend"]
        bucket = module_buckets.get(backend)
        if bucket is None:
            issues.append(f"wave-b native residual backend drifted: {backend}")
            continue
        native_modules = set(bucket["native_modules"])
        substrate = set(entry["substrate_modules"])
        compare_residual = set(entry["compare_residual_modules"])
        if not substrate.issubset(native_modules):
            issues.append(f"wave-b substrate escaped native bucket: {backend}")
        if not compare_residual.issubset(native_modules):
            issues.append(f"wave-b compare residual escaped native bucket: {backend}")
        if substrate & compare_residual:
            issues.append(f"wave-b native residual overlap drifted: {backend}")
    return issues


def _collect_wave_b_native_residual_file_issues() -> list[str]:
    issues: list[str] = []
    entries = contract_mod.iter_remaining_noncpp_runtime_wave_b_native_residual_files()
    if tuple(entry["backend"] for entry in entries) != ("js", "ts", "lua", "ruby", "php"):
        issues.append("wave-b native residual file order drifted")
    for entry in entries:
        backend = entry["backend"]
        native_root = ROOT / "src" / "runtime" / backend / "native"
        actual_files = tuple(
            sorted(
                str(path.relative_to(native_root)).replace("\\", "/")
                for path in native_root.rglob("*")
                if path.is_file()
            )
        )
        substrate_files = set(entry["substrate_files"])
        compare_residual_files = set(entry["compare_residual_files"])
        if substrate_files & compare_residual_files:
            issues.append(f"wave-b native residual file overlap drifted: {backend}")
        expected_files = tuple(sorted(substrate_files.union(compare_residual_files)))
        if actual_files != expected_files:
            issues.append(f"wave-b native residual file inventory drifted: {backend}")
    return issues


def _collect_wave_b_compat_issues() -> list[str]:
    issues: list[str] = []
    module_buckets = {
        entry["backend"]: entry
        for entry in contract_mod.iter_remaining_noncpp_runtime_module_buckets()
    }
    generated_compare = {
        entry["backend"]: entry
        for entry in contract_mod.iter_remaining_noncpp_runtime_wave_b_generated_compare()
    }
    native_residuals = {
        entry["backend"]: entry
        for entry in contract_mod.iter_remaining_noncpp_runtime_wave_b_native_residuals()
    }
    entries = contract_mod.iter_remaining_noncpp_runtime_wave_b_compat()
    if tuple(entry["backend"] for entry in entries) != ("js", "ts", "lua", "ruby", "php"):
        issues.append("wave-b compat order drifted")
    for entry in entries:
        backend = entry["backend"]
        bucket = module_buckets.get(backend)
        if bucket is None or backend not in generated_compare or backend not in native_residuals:
            issues.append(f"wave-b compat backend drifted: {backend}")
            continue
        substrate = set(entry["substrate_shim_modules"])
        compare_shims = set(entry["generated_compare_shim_modules"])
        if substrate & compare_shims:
            issues.append(f"wave-b compat overlap drifted: {backend}")
        if substrate | compare_shims != set(bucket["compat_modules"]):
            issues.append(f"wave-b compat coverage drifted: {backend}")
        if not compare_shims.issubset(set(generated_compare[backend]["materialized_compare_modules"])):
            issues.append(f"wave-b compat compare shim escaped generated compare set: {backend}")
        if not substrate.issubset(set(native_residuals[backend]["substrate_modules"])):
            issues.append(f"wave-b compat substrate escaped native residuals: {backend}")
    return issues


def _collect_wave_b_compat_file_issues() -> list[str]:
    issues: list[str] = []
    target_inventory = {
        entry["backend"]: entry
        for entry in contract_mod.iter_remaining_noncpp_runtime_target_inventory()
    }
    entries = contract_mod.iter_remaining_noncpp_runtime_wave_b_compat_files()
    if tuple(entry["backend"] for entry in entries) != ("js", "ts", "lua", "ruby", "php"):
        issues.append("wave-b compat file order drifted")
    for entry in entries:
        backend = entry["backend"]
        substrate = set(entry["substrate_shim_files"])
        compare_shims = set(entry["generated_compare_shim_files"])
        ancillary = set(entry["ancillary_files"])
        if substrate & compare_shims:
            issues.append(f"wave-b compat file overlap drifted: {backend}: substrate/generated")
        if substrate & ancillary:
            issues.append(f"wave-b compat file overlap drifted: {backend}: substrate/ancillary")
        if compare_shims & ancillary:
            issues.append(f"wave-b compat file overlap drifted: {backend}: generated/ancillary")
        actual_files = {
            path.removeprefix("pytra/")
            for path in target_inventory[backend]["compat_files"]
        }
        if substrate | compare_shims | ancillary != actual_files:
            issues.append(f"wave-b compat file inventory drifted: {backend}")
    return issues


def _collect_wave_a_native_residual_issues() -> list[str]:
    issues: list[str] = []
    module_buckets = {
        entry["backend"]: entry
        for entry in contract_mod.iter_remaining_noncpp_runtime_module_buckets()
    }
    entries = contract_mod.iter_remaining_noncpp_runtime_wave_a_native_residuals()
    if tuple(entry["backend"] for entry in entries) != ("go", "java", "kotlin", "scala", "swift", "nim"):
        issues.append("wave-a native residual order drifted")
    for entry in entries:
        backend = entry["backend"]
        bucket = module_buckets.get(backend)
        if bucket is None:
            issues.append(f"wave-a native residual backend drifted: {backend}")
            continue
        native_modules = set(bucket["native_modules"])
        substrate = set(entry["substrate_modules"])
        compare_residual = set(entry["compare_residual_modules"])
        if not substrate.issubset(native_modules):
            issues.append(f"wave-a substrate escaped native bucket: {backend}")
        if not compare_residual.issubset(native_modules):
            issues.append(f"wave-a compare residual escaped native bucket: {backend}")
        if substrate & compare_residual:
            issues.append(f"wave-a native residual overlap drifted: {backend}")
    return issues


def _collect_wave_a_native_residual_file_issues() -> list[str]:
    issues: list[str] = []
    entries = contract_mod.iter_remaining_noncpp_runtime_wave_a_native_residual_files()
    if tuple(entry["backend"] for entry in entries) != ("go", "java", "kotlin", "scala", "swift", "nim"):
        issues.append("wave-a native residual file order drifted")
    for entry in entries:
        backend = entry["backend"]
        native_root = ROOT / "src" / "runtime" / backend / "native"
        actual_files = tuple(
            sorted(
                str(path.relative_to(native_root)).replace("\\", "/")
                for path in native_root.rglob("*")
                if path.is_file()
            )
        )
        substrate_files = set(entry["substrate_files"])
        compare_residual_files = set(entry["compare_residual_files"])
        if substrate_files & compare_residual_files:
            issues.append(f"wave-a native residual file overlap drifted: {backend}")
        expected_files = tuple(sorted(substrate_files.union(compare_residual_files)))
        if actual_files != expected_files:
            issues.append(f"wave-a native residual file inventory drifted: {backend}")
    return issues


def main() -> int:
    issues = _collect_contract_issues()
    issues.extend(_collect_wave_a_runtime_hook_issues())
    issues.extend(_collect_current_inventory_issues())
    issues.extend(_collect_target_inventory_issues())
    issues.extend(_collect_module_bucket_issues())
    issues.extend(_collect_wave_b_blocked_reason_issues())
    issues.extend(_collect_wave_b_generated_compare_issues())
    issues.extend(_collect_wave_b_native_residual_issues())
    issues.extend(_collect_wave_b_native_residual_file_issues())
    issues.extend(_collect_wave_b_compat_issues())
    issues.extend(_collect_wave_b_compat_file_issues())
    issues.extend(_collect_wave_a_native_residual_issues())
    issues.extend(_collect_wave_a_native_residual_file_issues())
    if issues:
        print("non-c++ runtime layout rollout remaining contract check failed:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    print("non-c++ runtime layout rollout remaining contract check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
