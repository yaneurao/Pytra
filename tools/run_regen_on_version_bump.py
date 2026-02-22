#!/usr/bin/env python3
"""Run sample regeneration only when transpiler minor/major versions are bumped."""

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

LANG_VERSION_DEPENDENCIES: dict[str, list[str]] = {
    "cpp": ["cpp"],
    "rs": ["rs"],
    "cs": ["cs"],
    "js": ["js"],
    "ts": ["ts", "js"],
    "go": ["go", "cs"],
    "java": ["java", "cs"],
    "swift": ["swift", "cs"],
    "kotlin": ["kotlin", "cs"],
}


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


def _is_minor_or_major_bumped(old_ver: str, new_ver: str) -> bool:
    old_mj, old_mn, _ = _parse_semver(old_ver)
    new_mj, new_mn, _ = _parse_semver(new_ver)
    if new_mj > old_mj:
        return True
    if new_mj == old_mj and new_mn > old_mn:
        return True
    return False


def _load_versions_obj(raw_obj: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(raw_obj, dict):
        raise RuntimeError(f"{label}: version file must be object")

    shared = raw_obj.get("shared")
    if not _is_semver_text(shared):
        raise RuntimeError(f"{label}: shared must be semver x.y.z")

    langs_obj = raw_obj.get("languages")
    if not isinstance(langs_obj, dict):
        raise RuntimeError(f"{label}: languages must be object")

    for lang in LANGS:
        ver = langs_obj.get(lang)
        if not _is_semver_text(ver):
            raise RuntimeError(f"{label}: languages.{lang} must be semver x.y.z")

    return raw_obj


def _load_versions_from_worktree() -> dict[str, Any]:
    if not VERSIONS_FILE.exists():
        raise RuntimeError(f"missing versions file: {VERSIONS_REL}")
    try:
        obj = json.loads(VERSIONS_FILE.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"failed to parse {VERSIONS_REL}: {exc}") from exc
    return _load_versions_obj(obj, label="worktree")


def _load_versions_from_ref(ref: str) -> dict[str, Any] | None:
    cp = subprocess.run(
        ["git", "show", f"{ref}:{VERSIONS_REL}"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if cp.returncode != 0:
        stderr = cp.stderr.strip()
        if "exists on disk, but not in" in stderr or "does not exist in" in stderr:
            return None
        msg = stderr or cp.stdout.strip() or "git show failed"
        raise RuntimeError(f"failed to read {VERSIONS_REL} at {ref}: {msg}")
    try:
        obj = json.loads(cp.stdout)
    except Exception as exc:
        raise RuntimeError(f"failed to parse {VERSIONS_REL} at {ref}: {exc}") from exc
    return _load_versions_obj(obj, label=f"ref:{ref}")


def _collect_bumped(base: dict[str, Any], head: dict[str, Any]) -> tuple[bool, set[str]]:
    shared_bumped = _is_minor_or_major_bumped(str(base["shared"]), str(head["shared"]))
    lang_bumped: set[str] = set()
    for lang in LANGS:
        if _is_minor_or_major_bumped(str(base["languages"][lang]), str(head["languages"][lang])):
            lang_bumped.add(lang)
    return shared_bumped, lang_bumped


def _resolve_affected_langs(shared_bumped: bool, lang_bumped: set[str]) -> list[str]:
    if shared_bumped:
        return list(LANGS)

    affected: set[str] = set()
    for lang in LANGS:
        deps = LANG_VERSION_DEPENDENCIES.get(lang, [lang])
        for dep in deps:
            if dep in lang_bumped:
                affected.add(lang)
                break
    return sorted(affected)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run sample regeneration only for version-bumped targets")
    ap.add_argument("--base-ref", default="HEAD", help="git base ref (default: HEAD)")
    ap.add_argument("--head-ref", default="", help="git head ref (optional; when set, compare base...head)")
    ap.add_argument("--cache-file", default="", help="pass-through cache file path")
    ap.add_argument("--stems", default="", help="pass-through sample stems")
    ap.add_argument("--dry-run", action="store_true", help="only show action")
    ap.add_argument("--verbose", action="store_true", help="verbose output")
    ap.add_argument(
        "--verify-cpp-on-diff",
        action="store_true",
        help="pass-through verify flag to regenerate_samples.py",
    )
    ap.add_argument(
        "--verify-cpp-flags",
        default="-O2",
        help="compile flags for verify_sample_outputs.py",
    )
    args = ap.parse_args()

    head_ref = args.head_ref.strip()
    head_ref_opt = head_ref if head_ref != "" else None

    try:
        base_versions = _load_versions_from_ref(args.base_ref)
        if head_ref_opt is None:
            head_versions = _load_versions_from_worktree()
        else:
            head_tmp = _load_versions_from_ref(head_ref_opt)
            if head_tmp is None:
                raise RuntimeError(f"missing versions file at {head_ref_opt}: {VERSIONS_REL}")
            head_versions = head_tmp
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if base_versions is None:
        print(f"[SKIP] base ref has no {VERSIONS_REL} (bootstrap)")
        return 0

    shared_bumped, lang_bumped = _collect_bumped(base_versions, head_versions)
    affected_langs = _resolve_affected_langs(shared_bumped, lang_bumped)

    if len(affected_langs) == 0:
        print("[SKIP] no transpiler minor/major version bump detected")
        return 0

    cmd = ["python3", "tools/regenerate_samples.py", "--langs", ",".join(affected_langs)]

    if args.cache_file.strip() != "":
        cmd.extend(["--cache-file", args.cache_file.strip()])
    if args.stems.strip() != "":
        cmd.extend(["--stems", args.stems.strip()])
    if args.verbose:
        cmd.append("--verbose")
    if args.verify_cpp_on_diff:
        cmd.append("--verify-cpp-on-diff")
        cmd.extend(["--verify-cpp-flags", args.verify_cpp_flags])
    if args.dry_run:
        cmd.append("--dry-run")

    print("[RUN]", " ".join(cmd))
    cp = subprocess.run(cmd, cwd=str(ROOT))
    return int(cp.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
