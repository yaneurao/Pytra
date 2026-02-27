#!/usr/bin/env python3
"""Prepare selfhost/py2cs.py as a self-contained source.

This script inlines transpile_cli support blocks, CodeEmitter, and C# emitter
into py2cs.py so C# selfhost transpile no longer depends on cross-module imports.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_PY2CS = ROOT / "src" / "py2cs.py"
SRC_BASE = ROOT / "src" / "pytra" / "compiler" / "east_parts" / "code_emitter.py"
SRC_CS_EMITTER = ROOT / "src" / "hooks" / "cs" / "emitter" / "cs_emitter.py"
SRC_PREPARE_BASE = ROOT / "tools" / "prepare_selfhost_source.py"
DST_SELFHOST = ROOT / "selfhost" / "py2cs.py"


def _load_prepare_base_module():
    spec = importlib.util.spec_from_file_location("prepare_selfhost_source_base", SRC_PREPARE_BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load prepare_selfhost_source.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _remove_first_import_with_prefix(src: str, prefix: str) -> tuple[str, bool]:
    lines = src.splitlines(keepends=True)
    out_lines: list[str] = []
    removed = False
    skipping_block = False
    paren_depth = 0
    for line in lines:
        if skipping_block:
            paren_depth += line.count("(") - line.count(")")
            if paren_depth <= 0:
                skipping_block = False
            continue
        if (not removed) and line.startswith(prefix):
            removed = True
            paren_depth = line.count("(") - line.count(")")
            if paren_depth > 0:
                skipping_block = True
            continue
        out_lines.append(line)
    return "".join(out_lines), removed


def _remove_import_lines(text: str) -> str:
    out = text
    targets = [
        "from hooks.cs.emitter.cs_emitter import ",
        "from pytra.compiler.transpile_cli import ",
    ]
    for prefix in targets:
        out, removed = _remove_first_import_with_prefix(out, prefix)
        if not removed:
            raise RuntimeError("failed to remove required import: " + prefix.strip())
    return out


def _extract_cs_emitter_core(text: str) -> str:
    marker = "def load_cs_profile() -> dict[str, Any]:"
    i = text.find(marker)
    if i < 0:
        raise RuntimeError("failed to find load_cs_profile in cs_emitter.py")
    core = text[i:].rstrip() + "\n"

    old = (
        "def load_cs_hooks(profile: dict[str, Any]) -> dict[str, Any]:\n"
        "    \"\"\"C# 用 hook を読み込む。\"\"\"\n"
        "    _ = profile\n"
        "    hooks = build_cs_hooks()\n"
        "    if isinstance(hooks, dict):\n"
        "        return hooks\n"
        "    return {}\n"
    )
    new = (
        "def load_cs_hooks(profile: dict[str, Any]) -> dict[str, Any]:\n"
        "    \"\"\"selfhost 互換: C# hook は静的に無効化。\"\"\"\n"
        "    _ = profile\n"
        "    return {}\n"
    )
    if old not in core:
        raise RuntimeError("failed to patch load_cs_hooks block in cs_emitter core")
    core = core.replace(old, new)
    return core


def _insert_support_blocks(py2cs_text: str, support_blocks: str, base_class: str, cs_core: str) -> str:
    marker = "\ndef load_east("
    i = py2cs_text.find(marker)
    if i < 0:
        raise RuntimeError("failed to find load_east marker in py2cs.py")
    prefix = py2cs_text[:i].rstrip()
    suffix = py2cs_text[i + 1 :]
    return prefix + "\n\n" + support_blocks + "\n" + base_class + "\n" + cs_core + "\n" + suffix


def main() -> int:
    prepare_base = _load_prepare_base_module()
    py2cs_text = SRC_PY2CS.read_text(encoding="utf-8")
    base_text = SRC_BASE.read_text(encoding="utf-8")
    cs_emitter_text = SRC_CS_EMITTER.read_text(encoding="utf-8")

    support_blocks = prepare_base._extract_support_blocks()
    base_class = prepare_base._strip_triple_quoted_docstrings(prepare_base._extract_code_emitter_class(base_text))
    cs_core = _extract_cs_emitter_core(cs_emitter_text)

    py2cs_text = _remove_import_lines(py2cs_text)
    out = _insert_support_blocks(py2cs_text, support_blocks, base_class, cs_core)

    DST_SELFHOST.parent.mkdir(parents=True, exist_ok=True)
    DST_SELFHOST.write_text(out, encoding="utf-8")
    print(str(DST_SELFHOST))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

