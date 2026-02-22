#!/usr/bin/env python3
"""Fail when transpiler-related changes are missing required minor version bumps."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VERSIONS_FILE = ROOT / "src" / "pytra" / "compiler" / "transpiler_versions.json"
VERSIONS_REL = VERSIONS_FILE.relative_to(ROOT).as_posix()

LANGS = ["cpp", "rs", "cs", "js", "ts", "go", "java", "swift", "kotlin"]

SHARED_DEPENDENCY_PATHS = [
    "src/pytra",
    "src/profiles/common",
    "src/hooks/__init__.py",
]

LANG_DIRECT_DEPENDENCY_PATHS: dict[str, list[str]] = {
    "cpp": ["src/py2cpp.py", "src/hooks/cpp", "src/profiles/cpp"],
    "rs": ["src/py2rs.py", "src/hooks/rs", "src/profiles/rs"],
    "cs": ["src/py2cs.py", "src/hooks/cs", "src/profiles/cs"],
    "js": ["src/py2js.py", "src/hooks/js", "src/profiles/js"],
    "ts": ["src/py2ts.py", "src/hooks/ts"],
    "go": ["src/py2go.py", "src/hooks/go"],
    "java": ["src/py2java.py", "src/hooks/java"],
    "swift": ["src/py2swift.py", "src/hooks/swift"],
    "kotlin": ["src/py2kotlin.py", "src/hooks/kotlin"],
}


def _git_stdout(args: list[str], *, check: bool = True) -> str:
    cp = subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True)
    if check and cp.returncode != 0:
        msg = cp.stderr.strip() or cp.stdout.strip() or f"git {' '.join(args)} failed"
        raise RuntimeError(msg)
    return cp.stdout


def _path_matches(changed: str, target: str) -> bool:
    target_norm = target.rstrip("/")
    if changed == target_norm:
        return True
    return changed.startswith(target_norm + "/")


def _list_changed_files(base_ref: str, head_ref: str | None) -> list[str]:
    files: set[str] = set()
    if head_ref is None:
        out = _git_stdout(["diff", "--name-only", base_ref, "--"])
        for line in out.splitlines():
            rel = line.strip()
            if rel:
                files.add(rel)
        # Include untracked files when checking worktree against a base commit.
        out_untracked = _git_stdout(["ls-files", "--others", "--exclude-standard"])
        for line in out_untracked.splitlines():
            rel = line.strip()
            if rel:
                files.add(rel)
    else:
        out = _git_stdout(["diff", "--name-only", f"{base_ref}...{head_ref}", "--"])
        for line in out.splitlines():
            rel = line.strip()
            if rel:
                files.add(rel)
    return sorted(files)


def _is_semver_text(raw: Any) -> bool:
    if not isinstance(raw, str):
        return False
    parts = raw.split(".")
    if len(parts) != 3:
        return False
    for p in parts:
        if p == "" or not p.isdigit():
            return False
    return True


def _parse_semver(raw: str) -> tuple[int, int, int]:
    p0, p1, p2 = raw.split(".")
    return (int(p0), int(p1), int(p2))


def _load_versions_obj(raw_obj: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(raw_obj, dict):
        raise RuntimeError(f"{label}: version file must be an object")
    shared = raw_obj.get("shared")
    if not _is_semver_text(shared):
        raise RuntimeError(f"{label}: shared must be semver (x.y.z)")

    langs_obj = raw_obj.get("languages")
    if not isinstance(langs_obj, dict):
        raise RuntimeError(f"{label}: languages must be an object")
    for lang in LANGS:
        ver = langs_obj.get(lang)
        if not _is_semver_text(ver):
            raise RuntimeError(f"{label}: languages.{lang} must be semver (x.y.z)")

    return raw_obj


def _load_versions_from_worktree() -> dict[str, Any]:
    if not VERSIONS_FILE.exists():
        raise RuntimeError(f"missing versions file: {VERSIONS_REL}")
    try:
        raw_obj = json.loads(VERSIONS_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"failed to parse {VERSIONS_REL}: {exc}") from exc
    return _load_versions_obj(raw_obj, label="worktree")


def _load_versions_from_ref(ref: str) -> dict[str, Any]:
    cp = subprocess.run(
        ["git", "show", f"{ref}:{VERSIONS_REL}"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if cp.returncode != 0:
        msg = cp.stderr.strip() or cp.stdout.strip() or "git show failed"
        raise RuntimeError(f"failed to read {VERSIONS_REL} at {ref}: {msg}")
    try:
        raw_obj = json.loads(cp.stdout)
    except Exception as exc:
        raise RuntimeError(f"failed to parse {VERSIONS_REL} at {ref}: {exc}") from exc
    return _load_versions_obj(raw_obj, label=f"ref:{ref}")


def _collect_required_components(changed_files: list[str]) -> tuple[bool, set[str], list[str]]:
    touched_shared = False
    touched_langs: set[str] = set()
    touched_paths: list[str] = []

    for rel in changed_files:
        if rel == VERSIONS_REL:
            continue
        is_relevant = False
        for dep in SHARED_DEPENDENCY_PATHS:
            if _path_matches(rel, dep):
                touched_shared = True
                is_relevant = True
                break

        for lang in LANGS:
            for dep in LANG_DIRECT_DEPENDENCY_PATHS[lang]:
                if _path_matches(rel, dep):
                    touched_langs.add(lang)
                    is_relevant = True
                    break

        if is_relevant:
            touched_paths.append(rel)

    return touched_shared, touched_langs, touched_paths


def _is_minor_or_major_bumped(old_ver: str, new_ver: str) -> bool:
    old_mj, old_mn, _ = _parse_semver(old_ver)
    new_mj, new_mn, _ = _parse_semver(new_ver)
    if new_mj > old_mj:
        return True
    if new_mj == old_mj and new_mn > old_mn:
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Check transpiler version bump gate")
    ap.add_argument(
        "--base-ref",
        default="HEAD",
        help="git base ref (default: HEAD; compare base commit with current worktree)",
    )
    ap.add_argument(
        "--head-ref",
        default="",
        help="git head ref (optional; when set, compare base...head)",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable report in JSON",
    )
    args = ap.parse_args()

    head_ref = args.head_ref.strip()
    head_ref_opt = head_ref if head_ref != "" else None

    try:
        changed_files = _list_changed_files(args.base_ref, head_ref_opt)
        touched_shared, touched_langs, touched_paths = _collect_required_components(changed_files)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if len(touched_paths) == 0:
        if args.json:
            payload = {
                "base_ref": args.base_ref,
                "head_ref": head_ref_opt,
                "touched_shared": False,
                "touched_langs": [],
                "touched_paths": [],
                "ok": [],
                "missing": [],
            }
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print("[OK] no transpiler-related changes detected")
        return 0

    try:
        if head_ref_opt is None:
            base_versions = _load_versions_from_ref(args.base_ref)
            head_versions = _load_versions_from_worktree()
        else:
            base_versions = _load_versions_from_ref(args.base_ref)
            head_versions = _load_versions_from_ref(head_ref_opt)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    missing: list[str] = []
    ok_components: list[str] = []

    if touched_shared:
        old_shared = str(base_versions["shared"])
        new_shared = str(head_versions["shared"])
        if _is_minor_or_major_bumped(old_shared, new_shared):
            ok_components.append(f"shared {old_shared} -> {new_shared}")
        else:
            missing.append(f"shared (need minor+ bump): {old_shared} -> {new_shared}")

    for lang in sorted(touched_langs):
        old_ver = str(base_versions["languages"][lang])
        new_ver = str(head_versions["languages"][lang])
        if _is_minor_or_major_bumped(old_ver, new_ver):
            ok_components.append(f"{lang} {old_ver} -> {new_ver}")
        else:
            missing.append(f"{lang} (need minor+ bump): {old_ver} -> {new_ver}")

    if args.json:
        payload = {
            "base_ref": args.base_ref,
            "head_ref": head_ref_opt,
            "touched_shared": touched_shared,
            "touched_langs": sorted(touched_langs),
            "touched_paths": touched_paths,
            "ok": ok_components,
            "missing": missing,
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))

    if len(missing) > 0:
        if not args.json:
            print("[FAIL] transpiler version bump gate")
            print("  touched paths:")
            for p in touched_paths:
                print(f"    - {p}")
            print("  missing bumps:")
            for m in missing:
                print(f"    - {m}")
            print(f"  versions file: {VERSIONS_REL}")
        return 1

    if not args.json:
        print("[OK] transpiler version bump gate passed")
        if len(ok_components) > 0:
            print("  bumped components:")
            for comp in ok_components:
                print(f"    - {comp}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
