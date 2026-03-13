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
    pytra_cli_profiles as cli_profiles_mod,
)


CPP_GENERATED_ROOT = ROOT / "src" / "runtime" / "cpp" / "generated"
_OUTPUT_EXTENSIONS = {
    "cs": ".cs",
    "go": ".go",
    "java": ".java",
    "js": ".js",
    "ts": ".ts",
    "swift": ".swift",
    "kotlin": ".kt",
    "scala": ".scala",
    "lua": ".lua",
    "ruby": ".rb",
    "php": ".php",
    "nim": ".nim",
    "rs": ".rs",
}


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
        "js": ".js",
        "kotlin": ".kt",
        "lua": ".lua",
        "nim": ".nim",
        "php": ".php",
        "ruby": ".rb",
        "rs": ".rs",
        "scala": ".scala",
        "swift": ".swift",
        "ts": ".ts",
    }[backend]


def _collect_backend_generated_modules(backend: str, bucket: str) -> tuple[str, ...]:
    base = ROOT / "src" / "runtime" / backend / "generated" / bucket
    suffix = _generated_suffix_for_backend(backend)
    if not base.exists():
        return ()
    return tuple(sorted(path.stem for path in base.iterdir() if path.is_file() and path.suffix == suffix))


def _collect_backend_runtime_file_inventory(backend: str) -> dict[str, object]:
    base = ROOT / "src" / "runtime" / backend
    suffix = _generated_suffix_for_backend(backend)
    generated_files = tuple(
        sorted(
            str(path.relative_to(base)).replace("\\", "/")
            for path in (base / "generated").glob(f"**/*{suffix}")
            if path.is_file()
        )
    )
    native_files = tuple(
        sorted(
            str(path.relative_to(base)).replace("\\", "/")
            for path in (base / "native").glob(f"**/*{suffix}")
            if path.is_file()
        )
    )
    compat_files = tuple(
        sorted(
            str(path.relative_to(base)).replace("\\", "/")
            for path in (base / "pytra").glob("**/*")
            if path.is_file()
            and (
                path.suffix == suffix
                or str(path.relative_to(base)).replace("\\", "/") == "pytra/README.md"
            )
        )
    )
    return {
        "backend": backend,
        "generated_files": generated_files,
        "native_files": native_files,
        "compat_files": compat_files,
    }


def _collect_expected_runtime_file_inventory() -> tuple[dict[str, object], ...]:
    local_entries = {
        entry["backend"]: {
            "backend": entry["backend"],
            "generated_files": entry["generated_files"],
            "native_files": entry["native_files"],
            "compat_files": entry["compat_files"],
        }
        for entry in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_local_runtime_file_inventory()
    }
    merged: list[dict[str, object]] = []
    for backend in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_materialized_backends():
        if backend in local_entries:
            merged.append(local_entries[backend])
            continue
        remaining_entry = next(
            entry
            for entry in remaining_contract_mod.iter_remaining_noncpp_runtime_target_inventory()
            if entry["backend"] == backend
        )
        merged.append(
            {
                "backend": backend,
                "generated_files": remaining_entry["generated_files"],
                "native_files": remaining_entry["native_files"],
                "compat_files": remaining_entry["compat_files"],
            }
        )
    return tuple(merged)


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
                "js",
                "kotlin",
                "lua",
                "nim",
                "php",
                "rs",
                "ruby",
                "scala",
                "swift",
                "ts",
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


def _collect_build_profile_inventory() -> tuple[dict[str, object], ...]:
    staged_runtime_names = {
        "py_runtime.go",
        "png.go",
        "gif.go",
        "PyRuntime.java",
        "png.java",
        "gif.java",
        "py_runtime.swift",
        "image_runtime.swift",
        "py_runtime.kt",
        "image_runtime.kt",
        "py_runtime.scala",
        "image_runtime.scala",
    }
    inventories: list[dict[str, object]] = []
    for entry in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_build_profiles():
        backend = entry["backend"]
        extension = _OUTPUT_EXTENSIONS[backend]
        output_path = Path("out") / ("Main.java" if backend == "java" else f"main{extension}")
        plan = cli_profiles_mod.make_noncpp_build_plan(
            root=ROOT,
            target=backend,
            output_path=output_path,
            source_stem="main",
            run_after_build=True,
        )
        runtime_refs: list[str] = []
        for arg in tuple(plan.build_cmd or ()) + tuple(plan.run_cmd or ()):
            if arg.startswith(str(ROOT / "src" / "runtime")):
                runtime_refs.append(Path(arg).relative_to(ROOT).as_posix())
                continue
            if not arg.startswith("out/"):
                continue
            if Path(arg).name == output_path.name:
                continue
            if Path(arg).name in staged_runtime_names:
                runtime_refs.append(arg)
        if any(ref.startswith("src/runtime/") for ref in runtime_refs):
            wiring_mode = "repo_runtime_bundle_residual"
        elif runtime_refs and backend == "scala":
            wiring_mode = "staged_output_runner_bundle"
        elif runtime_refs:
            wiring_mode = "staged_output_runtime_bundle"
        elif backend in {"js", "ts", "lua", "ruby", "php"}:
            wiring_mode = "direct_script_runner"
        else:
            wiring_mode = "standalone_compiler_only"
        inventories.append(
            {
                "backend": backend,
                "wiring_mode": wiring_mode,
                "runtime_refs": tuple(runtime_refs),
            }
        )
    return tuple(inventories)


def _collect_smoke_inventory_issues() -> list[str]:
    issues: list[str] = []
    for entry in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_smoke_inventory():
        test_path = ROOT / entry["test_path"]
        text = test_path.read_text(encoding="utf-8")
        for test_name in entry["required_tests"]:
            needle = f"def {test_name}("
            if needle not in text:
                issues.append(f"generated-first smoke inventory drifted: {entry['test_path']}: {test_name}")
    return issues


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

    actual_build_profiles = _collect_build_profile_inventory()
    expected_build_profiles = contract_mod.iter_noncpp_runtime_generated_cpp_baseline_build_profiles()
    if actual_build_profiles != expected_build_profiles:
        issues.append(
            "generated-first build profile inventory drifted: "
            f"expected={expected_build_profiles!r} actual={actual_build_profiles!r}"
        )

    actual_runtime_file_inventory = tuple(
        _collect_backend_runtime_file_inventory(backend)
        for backend in contract_mod.iter_noncpp_runtime_generated_cpp_baseline_materialized_backends()
    )
    expected_runtime_file_inventory = _collect_expected_runtime_file_inventory()
    if actual_runtime_file_inventory != expected_runtime_file_inventory:
        issues.append(
            "generated-first runtime file inventory drifted: "
            f"expected={expected_runtime_file_inventory!r} actual={actual_runtime_file_inventory!r}"
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


def _collect_smoke_issues() -> list[str]:
    return _collect_smoke_inventory_issues()


def main() -> int:
    issues = _collect_contract_issues()
    issues.extend(_collect_policy_wording_issues())
    issues.extend(_collect_smoke_issues())
    if issues:
        for issue in issues:
            print(f"[NG] {issue}")
        return 1
    print("[OK] non-c++ generated cpp baseline contract matches current tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
