#!/usr/bin/env python3
"""Classify C++ emitter hooks and report semantic/syntax baseline metrics."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CPP_HOOKS = ROOT / "src" / "hooks" / "cpp" / "hooks" / "cpp_hooks.py"
ADD_RE = re.compile(r'hooks\.add\("([^"]+)",\s*([a-zA-Z_][a-zA-Z0-9_]*)\)')

# NOTE:
# This is the P0 baseline classifier. S2 will tighten policy by rejecting
# unexpected semantic hook additions in CI.
SEMANTIC_HOOKS = {
    "on_render_object_method",
    "on_render_binop",
    "on_render_expr_kind",
    "on_for_range_mode",
}
NOOP_HOOKS = {
    "on_render_call",
}


def _collect_hook_names(text: str) -> list[str]:
    names: list[str] = []
    for m in ADD_RE.finditer(text):
        names.append(m.group(1))
    return names


def main() -> int:
    ap = argparse.ArgumentParser(description="report semantic/syntax hook budget for C++ hooks")
    ap.add_argument("--json", action="store_true", help="print JSON instead of plain text")
    ap.add_argument(
        "--max-semantic",
        type=int,
        default=-1,
        help="if set (>=0), fail when semantic hook count exceeds this threshold",
    )
    args = ap.parse_args()

    if not CPP_HOOKS.exists():
        print(f"missing hooks file: {CPP_HOOKS}", file=sys.stderr)
        return 2

    text = CPP_HOOKS.read_text(encoding="utf-8")
    hook_names = _collect_hook_names(text)

    semantic: list[str] = []
    noop: list[str] = []
    syntax: list[str] = []
    unknown: list[str] = []
    for name in hook_names:
        if name in SEMANTIC_HOOKS:
            semantic.append(name)
        elif name in NOOP_HOOKS:
            noop.append(name)
        elif name.startswith("on_"):
            syntax.append(name)
        else:
            unknown.append(name)

    payload = {
        "file": str(CPP_HOOKS.relative_to(ROOT)),
        "total": len(hook_names),
        "semantic_count": len(semantic),
        "syntax_count": len(syntax),
        "noop_count": len(noop),
        "unknown_count": len(unknown),
        "semantic_hooks": sorted(semantic),
        "syntax_hooks": sorted(syntax),
        "noop_hooks": sorted(noop),
        "unknown_hooks": sorted(unknown),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"file={payload['file']}")
        print(
            "total={total} semantic={semantic_count} syntax={syntax_count} noop={noop_count} unknown={unknown_count}".format(
                **payload
            )
        )
        if semantic:
            print("semantic_hooks:", ", ".join(sorted(semantic)))
        if syntax:
            print("syntax_hooks:", ", ".join(sorted(syntax)))
        if noop:
            print("noop_hooks:", ", ".join(sorted(noop)))
        if unknown:
            print("unknown_hooks:", ", ".join(sorted(unknown)))

    if args.max_semantic >= 0 and len(semantic) > args.max_semantic:
        print(
            f"[FAIL] semantic hooks {len(semantic)} exceed budget {args.max_semantic}",
            file=sys.stderr,
        )
        return 1
    if len(unknown) > 0:
        print(f"[FAIL] unknown hooks detected: {', '.join(sorted(unknown))}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
