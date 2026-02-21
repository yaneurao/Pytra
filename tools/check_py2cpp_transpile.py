#!/usr/bin/env python3
"""Check py2cpp transpile success for fixtures and samples."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY2CPP = ROOT / "src" / "py2cpp.py"

DEFAULT_EXPECTED_FAILS = {
    "test/fixtures/signature/ng_kwargs.py",
    "test/fixtures/signature/ng_object_receiver.py",
    "test/fixtures/signature/ng_posonly.py",
    "test/fixtures/signature/ng_varargs.py",
    "test/fixtures/typing/any_class_alias.py",
}


def _run_one(src: Path, out: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python3", str(PY2CPP), str(src), "-o", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if cp.returncode == 0:
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    first = msg.splitlines()[0] if msg else "unknown error"
    return False, first


def _run_one_multifile(src: Path, out_dir: Path) -> tuple[bool, str]:
    cp = subprocess.run(
        ["python3", str(PY2CPP), str(src), "--multi-file", "--output-dir", str(out_dir)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if cp.returncode == 0:
        return True, ""
    msg = cp.stderr.strip() or cp.stdout.strip()
    first = msg.splitlines()[0] if msg else "unknown error"
    return False, first


def _has_import_statement(src: Path) -> bool:
    text = src.read_text(encoding="utf-8")
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("import ") or s.startswith("from "):
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="check py2cpp transpile success for fixtures/sample")
    ap.add_argument("--include-expected-failures", action="store_true", help="do not skip known negative fixtures")
    ap.add_argument("--verbose", action="store_true", help="print passing files")
    ap.add_argument(
        "--check-multi-file-imports",
        action="store_true",
        help="also run --multi-file check for sample files that contain import/from",
    )
    ap.add_argument(
        "--check-yanesdk-smoke",
        action="store_true",
        help="also run reduced Yanesdk smoke cases (library + one game) when sources exist",
    )
    args = ap.parse_args()

    fixture_files = sorted((ROOT / "test" / "fixtures").rglob("*.py"))
    sample_files = sorted((ROOT / "sample" / "py").glob("*.py"))
    yanesdk_files: list[Path] = []
    if args.check_yanesdk_smoke:
        lib = ROOT / "Yanesdk" / "yanesdk" / "yanesdk.py"
        if lib.exists():
            yanesdk_files.append(lib)
        docs_games: list[Path] = []
        docs_root = ROOT / "Yanesdk" / "docs"
        if docs_root.exists():
            for p in sorted(docs_root.rglob("*.py")):
                if p.name == "yanesdk.py":
                    continue
                docs_games.append(p)
        if len(docs_games) > 0:
            yanesdk_files.append(docs_games[0])
    expected_fails = set() if args.include_expected_failures else DEFAULT_EXPECTED_FAILS

    fails: list[tuple[str, str]] = []
    skipped = 0
    ok = 0
    total = 0
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "out.cpp"
        for src in fixture_files + sample_files + yanesdk_files:
            rel = str(src.relative_to(ROOT))
            if rel in expected_fails:
                skipped += 1
                continue
            total += 1
            good, msg = _run_one(src, out)
            if good:
                ok += 1
                if args.verbose:
                    print("OK", rel)
            else:
                fails.append((rel, msg))
        if args.check_multi_file_imports:
            for src in sample_files:
                rel = str(src.relative_to(ROOT))
                if not _has_import_statement(src):
                    continue
                total += 1
                out_dir = Path(tmpdir) / "multi_out"
                good, msg = _run_one_multifile(src, out_dir)
                if good:
                    ok += 1
                    if args.verbose:
                        print("OK", rel, "[multi-file]")
                else:
                    fails.append((rel + " [multi-file]", msg))

    print(f"checked={total} ok={ok} fail={len(fails)} skipped={skipped}")
    if fails:
        for rel, msg in fails:
            print(f"FAIL {rel}: {msg}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
