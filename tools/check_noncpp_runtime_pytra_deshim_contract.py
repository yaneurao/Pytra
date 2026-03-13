#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.toolchain.compiler import noncpp_runtime_pytra_deshim_contract as contract_mod


RUNTIME_ROOT = ROOT / "src" / "runtime"


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _collect_pytra_dirs() -> tuple[str, ...]:
    return tuple(
        sorted(
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in RUNTIME_ROOT.glob("*/pytra")
            if path.is_dir()
        )
    )


def _collect_pytra_files() -> tuple[str, ...]:
    results: list[str] = []
    for rel_dir in contract_mod.iter_noncpp_pytra_deshim_current_dirs():
        base = ROOT / rel_dir
        if not base.exists():
            continue
        results.extend(
            str(path.relative_to(ROOT)).replace("\\", "/")
            for path in base.rglob("*")
            if path.is_file()
        )
    return tuple(sorted(results))


def _collect_contract_issues() -> list[str]:
    issues: list[str] = []
    if contract_mod.iter_noncpp_pytra_deshim_backend_order() != (
        "rs",
        "go",
        "java",
        "kotlin",
        "scala",
        "swift",
        "nim",
        "js",
        "ts",
        "lua",
        "ruby",
        "php",
    ):
        issues.append("backend order drifted")
    if contract_mod.iter_noncpp_pytra_deshim_bucket_order() != (
        "direct_load_smoke",
        "runtime_shim_writer",
        "contract_allowlist",
        "selfhost_stage",
    ):
        issues.append("blocker bucket order drifted")
    backend_names = tuple(entry["backend"] for entry in contract_mod.iter_noncpp_pytra_deshim_backends())
    if backend_names != contract_mod.iter_noncpp_pytra_deshim_backend_order():
        issues.append("backend mapping order drifted")
    backend_dir_set = tuple(sorted(entry["current_dir"] for entry in contract_mod.iter_noncpp_pytra_deshim_backends()))
    if backend_dir_set != contract_mod.iter_noncpp_pytra_deshim_current_dirs():
        issues.append("backend mapping/current dir inventory drifted")
    for entry in contract_mod.iter_noncpp_pytra_deshim_backends():
        if entry["target_roots"] != ("generated", "native"):
            issues.append(f"target roots drifted: {entry['backend']}")
        if not entry["target_policy"].startswith("delete_target"):
            issues.append(f"target policy is no longer delete-target oriented: {entry['backend']}")
        for bucket in entry["blocker_buckets"]:
            if bucket not in contract_mod.iter_noncpp_pytra_deshim_bucket_order():
                issues.append(f"unknown blocker bucket: {entry['backend']}: {bucket}")
    return issues


def _collect_inventory_issues() -> list[str]:
    issues: list[str] = []
    if _collect_pytra_dirs() != contract_mod.iter_noncpp_pytra_deshim_current_dirs():
        issues.append("checked-in pytra directory inventory drifted")
    if _collect_pytra_files() != contract_mod.iter_noncpp_pytra_deshim_current_files():
        issues.append("checked-in pytra file inventory drifted")
    return issues


def _collect_blocker_issues() -> list[str]:
    issues: list[str] = []
    for entry in contract_mod.iter_noncpp_pytra_deshim_blockers():
        path = ROOT / entry["path"]
        if not path.exists():
            issues.append(f"missing blocker path: {entry['backend']}: {entry['path']}")
            continue
        text = _load_text(path)
        for needle in entry["needles"]:
            if needle not in text:
                issues.append(f"missing blocker needle: {entry['backend']}: {entry['path']}: {needle}")
    return issues


def main() -> int:
    issues = [
        *_collect_contract_issues(),
        *_collect_inventory_issues(),
        *_collect_blocker_issues(),
    ]
    if issues:
        print("[FAIL] non-C++ pytra deshim contract drifted")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print("[OK] non-C++ pytra deshim contract matches baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
