#!/usr/bin/env python3
"""Synchronize docs/en/todo/archive translation scaffolding from docs/ja/todo/archive."""

from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JP_DIR = ROOT / "docs" / "ja" / "todo" / "archive"
EN_DIR = ROOT / "docs" / "en" / "todo" / "archive"
DATE_FILE_RE = re.compile(r"^[0-9]{8}\.md$")
STATUS_PENDING = "pending"
STATUS_DONE = "done"


@dataclass
class SyncResult:
    created: list[str]
    existing: list[str]
    pending: list[str]
    done: list[str]


def _source_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _load_date_files(directory: Path) -> list[str]:
    if not directory.exists():
        return []
    out: list[str] = []
    for p in sorted(directory.iterdir()):
        if p.is_file() and DATE_FILE_RE.match(p.name):
            out.append(p.name)
    return out


def _date_label(stem8: str) -> str:
    return f"{stem8[0:4]}-{stem8[4:6]}-{stem8[6:8]}"


def _read_translation_status(path: Path) -> str:
    if not path.exists():
        return STATUS_PENDING
    txt = path.read_text(encoding="utf-8")
    m = re.search(r"<!--\s*translation-status:\s*(pending|done)\s*-->", txt)
    if m:
        return m.group(1)
    # Backward compatibility: treat files without marker as done translation.
    return STATUS_DONE


def _write_stub(name: str, *, dry_run: bool, overwrite: bool) -> bool:
    dst = EN_DIR / name
    if dst.exists() and not overwrite:
        return False
    src = JP_DIR / name
    src_hash = _source_hash(src)
    date_txt = _date_label(name[:-3])
    body = (
        f"# TODO History ({date_txt})\n\n"
        f"<a href=\"../../../ja/todo/archive/{name}\">\n"
        "  <img alt=\"Read in Japanese\" src=\"https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square\">\n"
        "</a>\n\n"
        "<!-- translation-status: pending -->\n"
        f"<!-- source-sha256: {src_hash} -->\n\n"
        "This file is an English translation mirror of the Japanese source.\n\n"
        f"- Source of truth: `docs/ja/todo/archive/{name}`\n"
        "- Status: pending translation\n"
        "- Workflow: translate this file, then update `translation-status` to `done`.\n"
    )
    if not dry_run:
        dst.write_text(body, encoding="utf-8")
    return True


def _render_index(date_files: list[str], status_map: dict[str, str]) -> str:
    lines: list[str] = []
    lines.append("# TODO History (Index)")
    lines.append("")
    lines.append("<a href=\"../../../ja/todo/archive/index.md\">")
    lines.append("  <img alt=\"Read in Japanese\" src=\"https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square\">")
    lines.append("</a>")
    lines.append("")
    lines.append(f"Last updated: {date.today().isoformat()}")
    lines.append("")
    lines.append("## Policy")
    lines.append("")
    lines.append("- `docs/ja/todo/archive/` is the source of truth.")
    lines.append("- Keep one file per date (`YYYYMMDD.md`).")
    lines.append("- Use `python3 tools/sync_todo_history_translation.py` to create missing mirror files and refresh this index.")
    lines.append("")
    lines.append("## Date Links")
    lines.append("")
    for name in sorted(date_files, reverse=True):
        stem8 = name[:-3]
        label = _date_label(stem8)
        status = status_map.get(name, STATUS_PENDING)
        lines.append(f"- [{label}]({name}) (`{status}`)")
    lines.append("")
    return "\n".join(lines)


def sync(*, dry_run: bool) -> SyncResult:
    date_files = _load_date_files(JP_DIR)
    EN_DIR.mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    existing: list[str] = []
    for name in date_files:
        created_now = _write_stub(name, dry_run=dry_run, overwrite=False)
        if created_now:
            created.append(name)
        else:
            existing.append(name)

    status_map: dict[str, str] = {}
    pending: list[str] = []
    done: list[str] = []
    for name in date_files:
        st = _read_translation_status(EN_DIR / name)
        status_map[name] = st
        if st == STATUS_PENDING:
            pending.append(name)
        else:
            done.append(name)

    index_txt = _render_index(date_files, status_map)
    if not dry_run:
        (EN_DIR / "index.md").write_text(index_txt, encoding="utf-8")

    return SyncResult(created=created, existing=existing, pending=pending, done=done)


def rewrite_pending_stubs(*, dry_run: bool) -> list[str]:
    date_files = _load_date_files(JP_DIR)
    rewritten: list[str] = []
    for name in date_files:
        path = EN_DIR / name
        if _read_translation_status(path) != STATUS_PENDING:
            continue
        changed = _write_stub(name, dry_run=dry_run, overwrite=True)
        if changed:
            rewritten.append(name)
    return rewritten


def check_only() -> int:
    jp_dates = _load_date_files(JP_DIR)
    en_dates = _load_date_files(EN_DIR)
    missing = sorted(set(jp_dates) - set(en_dates))
    extra = sorted(set(en_dates) - set(jp_dates))
    index_exists = (EN_DIR / "index.md").exists()

    if missing:
        print("[FAIL] missing docs/en/todo/archive translations:")
        for name in missing:
            print(f"  - {name}")
    if extra:
        print("[FAIL] extra docs/en/todo/archive files not present in docs/ja:")
        for name in extra:
            print(f"  - {name}")
    if not index_exists:
        print("[FAIL] missing docs/en/todo/archive/index.md")

    if missing or extra or not index_exists:
        return 1

    print("[OK] docs/en/todo/archive file set is synchronized with docs/ja/todo/archive")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="sync docs/en/todo/archive from docs/ja/todo/archive")
    ap.add_argument("--check", action="store_true", help="check only (no write)")
    ap.add_argument("--dry-run", action="store_true", help="show action without writing")
    ap.add_argument(
        "--rewrite-pending",
        action="store_true",
        help="rewrite files marked as pending translation using the latest stub template",
    )
    args = ap.parse_args()

    if args.check:
        return check_only()

    result = sync(dry_run=args.dry_run)
    rewritten = rewrite_pending_stubs(dry_run=args.dry_run) if args.rewrite_pending else []
    print(
        "summary:"
        + f" created={len(result.created)}"
        + f" existing={len(result.existing)}"
        + f" pending={len(result.pending)}"
        + f" done={len(result.done)}"
        + f" rewritten={len(rewritten)}"
        + (" dry_run=1" if args.dry_run else "")
    )
    if len(result.created) > 0:
        print("created files:")
        for name in result.created:
            print(f"  - docs/en/todo/archive/{name}")
    if len(rewritten) > 0:
        print("rewritten files:")
        for name in rewritten:
            print(f"  - docs/en/todo/archive/{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
