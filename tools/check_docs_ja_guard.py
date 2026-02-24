#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_JA = ROOT / "docs-ja"

ALLOWED_EXACT: set[str] = {
    "how-to-use.md",
    "news/index.md",
    "spec/index.md",
    "todo.md",
    "todo-history/index.md",
}

ALLOWED_REGEX: tuple[re.Pattern[str], ...] = (
    re.compile(r"^todo-history/[0-9]{8}\.md$"),
    re.compile(r"^plans/.+\.md$"),
    re.compile(r"^language/.+\.md$"),
    re.compile(r"^spec/spec-(boxing|codex|dev|east|east123|east123-migration|gc|import|iterable|language-profile|linker|options|runtime|tools|type_id|user|pylib-modules|sample-code|philosophy|make|template)\.md$"),
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
    if not DOCS_JA.exists():
        print("docs-ja guard: docs-ja/ が存在しません。", file=sys.stderr)
        return 1

    disallowed: list[str] = []
    for entry in sorted(DOCS_JA.rglob("*")):
        if not entry.is_file():
            continue
        rel = entry.relative_to(DOCS_JA)
        if not _is_allowed(rel):
            disallowed.append(rel.as_posix())

    if disallowed:
        print("docs-ja guard failed: docs-ja/ 配下に未管理ファイルがあります。")
        for item in disallowed:
            print(f"- docs-ja/{item}")
        print("意図した追加なら、明示依頼を得たうえでこのガードを更新してください。")
        return 1

    print("docs-ja guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
