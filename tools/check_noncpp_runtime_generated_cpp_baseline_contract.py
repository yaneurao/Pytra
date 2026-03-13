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

from src.toolchain.compiler import (  # noqa: E402
    noncpp_runtime_generated_cpp_baseline_contract as contract_mod,
    noncpp_runtime_layout_contract as layout_contract_mod,
    noncpp_runtime_layout_rollout_remaining_contract as remaining_contract_mod,
)


CPP_GENERATED_ROOT = ROOT / "src" / "runtime" / "cpp" / "generated"


def _collect_cpp_generated_bucket_modules(bucket: str) -> tuple[str, ...]:
    base = CPP_GENERATED_ROOT / bucket
    if not base.exists():
        return ()
    return tuple(
        sorted(
            {
                path.stem
                for path in base.iterdir()
                if path.is_file() and path.suffix in {".h", ".cpp"}
            }
        )
    )


def _generated_suffix_for_backend(backend: str) -> str:
    return {
        "cs": ".cs",
        "go": ".go",
        "java": ".java",
        "kotlin": ".kt",
        "nim": ".nim",
        "rs": ".rs",
        "swift": ".swift",
    }[backend]


def _collect_backend_generated_modules(backend: str, bucket: str) -> tuple[str, ...]:
    base = ROOT / "src" / "runtime" / backend / "generated" / bucket
    suffix = _generated_suffix_for_backend(backend)
    if not base.exists():
        return ()
    return tuple(sorted(path.stem for path in base.iterdir() if path.is_file() and path.suffix == suffix))


def _collect_runtime_layout_legacy_state_buckets() -> tuple[dict[str, object], ...]:
    baseline = set(contract_mod.iter_noncpp_runtime_generated_cpp_baseline_modules())
    buckets: dict[tuple[str, str], set[str]] = {}
    backend_order = {
        backend: index
        for index, backend in enumerate(
            (
                "cs",
                "go",
                "java",
                "kotlin",
                "lua",
                "nim",
                "rs",
                "ruby",
                "scala",
                "swift",
            )
        )
    }
    state_order = {
        state: index
        for index, state in enumerate(
            contract_mod.iter_noncpp_runtime_generated_cpp_baseline_forbidden_legacy_states()
        )
    }

    def add(backend: str, legacy_state: str, modules: tuple[str, ...]) -> None:
        filtered = tuple(module for module in modules if module in baseline)
        if not filtered:
            return
        buckets.setdefault((backend, legacy_state), set()).update(filtered)

    for backend, entries in (
        ("cs", layout_contract_mod.iter_cs_std_lane_ownership()),
        ("rs", layout_contract_mod.iter_rs_std_lane_ownership()),
    ):
        for entry in entries:
            module = f"std/{entry['module_name']}"
            if module not in baseline:
                continue
            generated_state = entry["generated_std_state"]
            canonical_lane = entry["canonical_lane"]
            if generated_state != "canonical_generated":
                add(backend, generated_state, (module,))
            if canonical_lane.startswith("native/"):
                add(backend, "native_canonical", (module,))

    for entry in remaining_contract_mod.iter_remaining_noncpp_runtime_module_buckets():
        add(entry["backend"], "blocked", entry["blocked_modules"])
    for entry in remaining_contract_mod.iter_remaining_noncpp_runtime_wave_a_native_residuals():
        add(entry["backend"], "native_canonical", entry["compare_residual_modules"])
    for entry in remaining_contract_mod.iter_remaining_noncpp_runtime_wave_b_native_residuals():
        add(entry["backend"], "native_canonical", entry["compare_residual_modules"])

    return tuple(
        {
            "backend": backend,
            "legacy_state": legacy_state,
            "modules": tuple(sorted(modules)),
        }
        for (backend, legacy_state), modules in sorted(
            buckets.items(),
            key=lambda item: (
                backend_order[item[0][0]],
                state_order[item[0][1]],
            ),
        )
    )


def _collect_helper_artifact_overlap_modules() -> tuple[str, ...]:
    baseline = set(contract_mod.iter_noncpp_runtime_generated_cpp_baseline_modules())
    overlap: set[str] = set()
    def is_helper_shaped(module: str) -> bool:
        stem = module.rsplit("/", 1)[-1]
        return stem.endswith("_helper") or stem == "image_runtime"
    for entry in remaining_contract_mod.iter_remaining_noncpp_runtime_wave_a_generated_compare():
        overlap.update(
            module
            for module in entry["helper_artifact_modules"]
            if module in baseline and is_helper_shaped(module)
        )
    for entry in remaining_contract_mod.iter_remaining_noncpp_runtime_wave_b_generated_compare():
        overlap.update(
            module
            for module in entry["helper_artifact_modules"]
            if module in baseline and is_helper_shaped(module)
        )
    return tuple(sorted(overlap))


def _collect_contract_issues() -> list[str]:
    issues: list[str] = []

    bucket_entries = contract_mod.iter_noncpp_runtime_generated_cpp_baseline_buckets()
    bucket_order = tuple(entry["bucket"] for entry in bucket_entries)
    if bucket_order != contract_mod.iter_noncpp_runtime_generated_cpp_baseline_bucket_order():
        issues.append("bucket order drifted")

    full_modules: list[str] = []
    for entry in bucket_entries:
        bucket = entry["bucket"]
        expected_modules = entry["modules"]
        actual_modules = _collect_cpp_generated_bucket_modules(bucket)
        if actual_modules != expected_modules:
            issues.append(
                f"cpp/generated baseline drifted for {bucket}: "
                f"expected={expected_modules!r} actual={actual_modules!r}"
            )
        full_modules.extend(f"{bucket}/{module}" for module in expected_modules)

    if tuple(full_modules) != contract_mod.iter_noncpp_runtime_generated_cpp_baseline_modules():
        issues.append("flattened module baseline drifted")

    forbidden_states = contract_mod.iter_noncpp_runtime_generated_cpp_baseline_forbidden_legacy_states()
    if forbidden_states != ("blocked", "compare_artifact", "no_runtime_module", "native_canonical", "helper_artifact"):
        issues.append("forbidden legacy state order drifted")

    actual_legacy_buckets = _collect_runtime_layout_legacy_state_buckets()
    expected_legacy_buckets = contract_mod.iter_noncpp_runtime_generated_cpp_baseline_legacy_state_buckets()
    if actual_legacy_buckets != expected_legacy_buckets:
        issues.append(
            "legacy baseline exception buckets drifted: "
            f"expected={expected_legacy_buckets!r} actual={actual_legacy_buckets!r}"
        )

    helper_overlap = _collect_helper_artifact_overlap_modules()
    if helper_overlap != contract_mod.iter_noncpp_runtime_generated_cpp_baseline_helper_artifact_overlap():
        issues.append(
            "baseline helper-artifact overlap drifted: "
            f"expected={contract_mod.iter_noncpp_runtime_generated_cpp_baseline_helper_artifact_overlap()!r} "
            f"actual={helper_overlap!r}"
        )

    for backend in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_materialized_backends():
        for entry in bucket_entries:
            bucket = entry["bucket"]
            expected_modules = entry["modules"]
            actual_modules = _collect_backend_generated_modules(backend, bucket)
            missing = tuple(module for module in expected_modules if module not in actual_modules)
            if missing:
                issues.append(
                    f"{backend} generated baseline missing modules for {bucket}: {missing!r}"
                )

    return issues


def _collect_policy_wording_issues() -> list[str]:
    issues: list[str] = []
    for entry in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_legacy_policy_files():
        text = (ROOT / entry["path"]).read_text(encoding="utf-8")
        if entry["required_needle"] not in text:
            issues.append(f"legacy policy file wording drifted: {entry['path']}")
    for entry in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_active_policy_docs():
        text = (ROOT / entry["path"]).read_text(encoding="utf-8")
        for needle in entry["required_needles"]:
            if needle not in text:
                issues.append(f"active policy doc missing required wording: {entry['path']}: {needle}")
        for needle in entry["forbidden_needles"]:
            if needle in text:
                issues.append(f"active policy doc kept legacy wording: {entry['path']}: {needle}")
    return issues


def main() -> int:
    issues = _collect_contract_issues()
    issues.extend(_collect_policy_wording_issues())
    if issues:
        for issue in issues:
            print(f"[NG] {issue}")
        return 1
    print("[OK] non-c++ generated cpp baseline contract matches current tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
