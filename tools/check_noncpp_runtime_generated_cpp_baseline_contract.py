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

    return issues


def main() -> int:
    issues = _collect_contract_issues()
    if issues:
        for issue in issues:
            print(f"[NG] {issue}")
        return 1
    print("[OK] non-c++ generated cpp baseline contract matches current tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

