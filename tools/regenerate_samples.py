#!/usr/bin/env python3
"""Regenerate sample outputs with version-gated skip decisions.

This script transpiles `sample/py/*.py` into language-specific `sample/<lang>/`
outputs and skips unchanged targets by comparing cached source/output hashes
plus transpiler-version tokens.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_FILE = ROOT / "out" / "sample_regen_cache.json"
DEFAULT_VERSIONS_FILE = ROOT / "src" / "pytra" / "compiler" / "transpiler_versions.json"
CACHE_VERSION = 1


LANG_CONFIGS: dict[str, dict[str, str]] = {
    "cpp": {"cli": "src/py2cpp.py", "out_dir": "sample/cpp", "ext": ".cpp"},
    "rs": {"cli": "src/py2rs.py", "out_dir": "sample/rs", "ext": ".rs"},
    "cs": {"cli": "src/py2cs.py", "out_dir": "sample/cs", "ext": ".cs"},
    "js": {"cli": "src/py2js.py", "out_dir": "sample/js", "ext": ".js"},
    "ts": {"cli": "src/py2ts.py", "out_dir": "sample/ts", "ext": ".ts"},
    "go": {"cli": "src/py2go.py", "out_dir": "sample/go", "ext": ".go"},
    "java": {"cli": "src/py2java.py", "out_dir": "sample/java", "ext": ".java"},
    "swift": {"cli": "src/py2swift.py", "out_dir": "sample/swift", "ext": ".swift"},
    "kotlin": {"cli": "src/py2kotlin.py", "out_dir": "sample/kotlin", "ext": ".kt"},
    "lua": {"cli": "src/py2lua.py", "out_dir": "sample/lua", "ext": ".lua"},
}

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
    "lua": ["lua"],
}

SEMVER_PARTS = 3


def _normalize_langs(raw: str) -> list[str]:
    items: list[str] = []
    for part in raw.split(","):
        name = part.strip()
        if name == "":
            continue
        items.append(name)
    return items


def _normalize_stems(raw: str) -> set[str]:
    out: set[str] = set()
    for part in raw.split(","):
        name = part.strip()
        if name == "":
            continue
        out.add(name)
    return out


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve().as_posix())


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _is_semver_text(raw: Any) -> bool:
    if not isinstance(raw, str):
        return False
    parts = raw.split(".")
    if len(parts) != SEMVER_PARTS:
        return False
    for p in parts:
        if p == "" or not p.isdigit():
            return False
    return True


def _load_versions(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RuntimeError(f"missing versions file: {path}")
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"failed to load versions file: {path}: {exc}") from exc
    if not isinstance(obj, dict):
        raise RuntimeError(f"invalid versions file object: {path}")

    shared = obj.get("shared")
    if not _is_semver_text(shared):
        raise RuntimeError("invalid shared version (expected semver x.y.z)")

    langs_obj = obj.get("languages")
    if not isinstance(langs_obj, dict):
        raise RuntimeError("invalid languages object in versions file")
    for lang in LANG_CONFIGS:
        ver = langs_obj.get(lang)
        if not _is_semver_text(ver):
            raise RuntimeError(f"invalid language version for {lang} (expected semver x.y.z)")
    return obj


def _version_token_for_lang(versions: dict[str, Any], lang: str) -> str:
    shared = str(versions["shared"])
    lang_versions = versions["languages"]
    deps = LANG_VERSION_DEPENDENCIES.get(lang, [lang])
    parts: list[str] = [f"shared={shared}"]
    for dep in deps:
        parts.append(f"{dep}={lang_versions[dep]}")
    return "|".join(parts)


def _load_cache(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"cache_version": CACHE_VERSION, "entries": {}}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"cache_version": CACHE_VERSION, "entries": {}}
    if not isinstance(obj, dict):
        return {"cache_version": CACHE_VERSION, "entries": {}}
    if obj.get("cache_version") != CACHE_VERSION:
        return {"cache_version": CACHE_VERSION, "entries": {}}
    entries = obj.get("entries")
    if not isinstance(entries, dict):
        return {"cache_version": CACHE_VERSION, "entries": {}}
    return {"cache_version": CACHE_VERSION, "entries": entries}


def _save_cache(path: Path, cache: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True)
    path.write_text(txt + "\n", encoding="utf-8")


def _run_transpile(cli_path: Path, src: Path, out: Path) -> tuple[bool, str]:
    cmd = ["python3", str(cli_path), str(src), "-o", str(out)]
    cp = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if cp.returncode == 0:
        return True, ""
    msg = cp.stderr.strip()
    if msg == "":
        msg = cp.stdout.strip()
    if msg == "":
        msg = f"transpiler exited with code {cp.returncode}"
    first = msg.splitlines()[0]
    return False, first


def _entry_key(lang: str, stem: str) -> str:
    return f"{lang}:{stem}"


def _verify_cpp_outputs(changed_cpp_stems: set[str], compile_flags: str) -> tuple[bool, str]:
    if len(changed_cpp_stems) == 0:
        return True, ""
    stems = sorted(changed_cpp_stems)
    cmd = [
        "python3",
        "tools/verify_sample_outputs.py",
        "--samples",
        *stems,
        "--compile-flags",
        compile_flags,
    ]
    cp = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if cp.returncode == 0:
        return True, ""
    msg = cp.stdout.strip()
    if msg == "":
        msg = cp.stderr.strip()
    if msg == "":
        msg = "verify_sample_outputs failed with no output"
    first = msg.splitlines()[0]
    return False, first


def main() -> int:
    ap = argparse.ArgumentParser(description="Regenerate sample outputs with version-gated skip")
    ap.add_argument(
        "--langs",
        default="cpp,rs,cs,js,ts,go,java,swift,kotlin",
        help="comma-separated target languages",
    )
    ap.add_argument(
        "--stems",
        default="",
        help="comma-separated sample stems (default: all sample/py/*.py)",
    )
    ap.add_argument("--cache-file", default=str(DEFAULT_CACHE_FILE), help="cache json path")
    ap.add_argument(
        "--versions-file",
        default=str(DEFAULT_VERSIONS_FILE),
        help="transpiler versions json path",
    )
    ap.add_argument("--force", action="store_true", help="ignore cache and regenerate targets")
    ap.add_argument("--clear-cache", action="store_true", help="discard existing cache entries first")
    ap.add_argument("--dry-run", action="store_true", help="show what would regenerate")
    ap.add_argument("--verbose", action="store_true", help="print per-target decisions")
    ap.add_argument(
        "--verify-cpp-on-diff",
        action="store_true",
        help="run tools/verify_sample_outputs.py only for changed C++ outputs",
    )
    ap.add_argument(
        "--verify-cpp-flags",
        default="-O2",
        help="compile flags passed to verify_sample_outputs.py --compile-flags",
    )
    args = ap.parse_args()

    langs = _normalize_langs(args.langs)
    if len(langs) == 0:
        print("error: no languages selected", file=sys.stderr)
        return 2
    invalid = [l for l in langs if l not in LANG_CONFIGS]
    if len(invalid) > 0:
        print("error: unknown language(s): " + ", ".join(sorted(invalid)), file=sys.stderr)
        return 2

    selected_stems = _normalize_stems(args.stems)
    sample_py_dir = ROOT / "sample" / "py"
    sample_files = sorted(sample_py_dir.glob("*.py"))
    if len(sample_files) == 0:
        print("error: no sample/py files found", file=sys.stderr)
        return 2
    if len(selected_stems) > 0:
        sample_files = [p for p in sample_files if p.stem in selected_stems]
        if len(sample_files) == 0:
            print("error: no sample files matched --stems", file=sys.stderr)
            return 2

    try:
        versions = _load_versions(Path(args.versions_file))
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    cache_path = Path(args.cache_file)
    cache = _load_cache(cache_path)
    if args.clear_cache:
        cache = {"cache_version": CACHE_VERSION, "entries": {}}
    entries = cache.get("entries", {})
    if not isinstance(entries, dict):
        entries = {}
        cache["entries"] = entries

    version_tokens: dict[str, str] = {}
    for lang in langs:
        version_tokens[lang] = _version_token_for_lang(versions, lang)

    total = 0
    skipped = 0
    regenerated = 0
    failed = 0
    changed_cpp_stems: set[str] = set()

    for lang in langs:
        cfg = LANG_CONFIGS[lang]
        cli = ROOT / cfg["cli"]
        out_dir = ROOT / cfg["out_dir"]
        ext = cfg["ext"]
        version_token = version_tokens[lang]

        if not cli.exists():
            print(f"[FAIL] missing transpiler: {cli}")
            failed += 1
            continue

        for src in sample_files:
            total += 1
            stem = src.stem
            out = out_dir / f"{stem}{ext}"
            src_hash = _sha256_file(src)
            key = _entry_key(lang, stem)
            ent_obj = entries.get(key, {})
            ent = ent_obj if isinstance(ent_obj, dict) else {}

            out_hash = ""
            if out.exists():
                out_hash = _sha256_file(out)

            up_to_date = (
                (not args.force)
                and out.exists()
                and ent.get("src_hash") == src_hash
                and ent.get("version_token") == version_token
                and ent.get("out_hash") == out_hash
            )

            if up_to_date:
                skipped += 1
                if args.verbose:
                    print(f"[SKIP] {lang} {stem}")
                continue

            if args.dry_run:
                regenerated += 1
                if args.verbose:
                    print(f"[REGEN-PLAN] {lang} {stem}")
                continue

            out.parent.mkdir(parents=True, exist_ok=True)
            ok, msg = _run_transpile(cli, src, out)
            if not ok:
                failed += 1
                print(f"[FAIL] {lang} {stem}: {msg}")
                continue
            if not out.exists():
                failed += 1
                print(f"[FAIL] {lang} {stem}: output not generated ({out})")
                continue

            regenerated += 1
            new_out_hash = _sha256_file(out)
            if lang == "cpp" and out_hash != new_out_hash:
                changed_cpp_stems.add(stem)
            entries[key] = {
                "lang": lang,
                "stem": stem,
                "src_rel": _rel(src),
                "out_rel": _rel(out),
                "src_hash": src_hash,
                "version_token": version_token,
                "out_hash": new_out_hash,
            }
            if args.verbose:
                print(f"[REGEN] {lang} {stem}")

    if not args.dry_run:
        cache["entries"] = entries
        _save_cache(cache_path, cache)
        if args.verify_cpp_on_diff and len(changed_cpp_stems) > 0:
            ok, msg = _verify_cpp_outputs(changed_cpp_stems, args.verify_cpp_flags)
            if not ok:
                print(f"[FAIL] verify cpp on diff: {msg}")
                failed += 1
            elif args.verbose:
                print("[VERIFY] cpp diff verification passed")

    print(
        "summary:"
        + f" total={total}"
        + f" skip={skipped}"
        + f" regen={regenerated}"
        + f" fail={failed}"
        + (" dry_run=1" if args.dry_run else "")
    )
    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
