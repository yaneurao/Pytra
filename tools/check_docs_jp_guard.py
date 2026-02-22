#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_JP = ROOT / "docs-jp"

ALLOWED_EXACT: set[str] = {
    "how-to-use.md",
    "philosophy.md",
    "spec-codex.md",
    "spec/index.md",
    "todo.md",
    "todo-history/index.md",
}

ALLOWED_REGEX: tuple[re.Pattern[str], ...] = (
    re.compile(r"^todo-history/[0-9]{8}\.md$"),
    re.compile(r"^plans/.+\.md$"),
    re.compile(r"^language/.+\.md$"),
    re.compile(r"^spec/spec-(dev|east|gc|import|language-profile|options|runtime|tools|user|pylib-modules|sample-code)\.md$"),
)


def _is_allowed(rel_path: Path) -> bool:
    rel_txt = rel_path.as_posix()
    if rel_txt in ALLOWED_EXACT:
        return True
    for pat in ALLOWED_REGEX:
        if pat.fullmatch(rel_txt):
            return True
    return False


def main() -> int:
    if not DOCS_JP.exists():
        print("docs-jp guard: docs-jp/ が存在しません。", file=sys.stderr)
        return 1

    disallowed: list[str] = []
    for entry in sorted(DOCS_JP.rglob("*")):
        if not entry.is_file():
            continue
        rel = entry.relative_to(DOCS_JP)
        if not _is_allowed(rel):
            disallowed.append(rel.as_posix())

    if disallowed:
        print("docs-jp guard failed: docs-jp/ 配下に未管理ファイルがあります。")
        for item in disallowed:
            print(f"- docs-jp/{item}")
        print("意図した追加なら、明示依頼を得たうえでこのガードを更新してください。")
        return 1

    print("docs-jp guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
