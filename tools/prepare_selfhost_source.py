#!/usr/bin/env python3
"""Prepare selfhost/py2cpp.py as a self-contained source.

This script inlines CodeEmitter into py2cpp.py so transpiling selfhost input
no longer depends on cross-module import resolution.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_PY2CPP = ROOT / "src" / "py2cpp.py"
SRC_BASE = ROOT / "src" / "pytra" / "compiler" / "east_parts" / "code_emitter.py"
DST_SELFHOST = ROOT / "selfhost" / "py2cpp.py"
SRC_TRANSPILE_CLI = ROOT / "src" / "pytra" / "compiler" / "transpile_cli.py"


def _extract_code_emitter_class(text: str) -> str:
    marker = "class EmitterHooks:"
    i = text.find(marker)
    if i < 0:
        marker = "class CodeEmitter:"
        i = text.find(marker)
    if i < 0:
        raise RuntimeError("CodeEmitter class not found")
    return text[i:].rstrip() + "\n"


def _strip_triple_quoted_docstrings(text: str) -> str:
    out: list[str] = []
    in_doc = False
    quote = ""
    for line in text.splitlines():
        stripped = line.lstrip()
        if not in_doc:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                q = stripped[:3]
                # one-line docstring
                if stripped.count(q) >= 2 and len(stripped) > 3:
                    continue
                in_doc = True
                quote = q
                continue
            out.append(line)
        else:
            if quote in stripped:
                in_doc = False
                quote = ""
            continue
    return "\n".join(out) + "\n"


def _remove_import_line(text: str) -> str:
    targets: list[tuple[str, str]] = [
        ("from pytra.compiler.east_parts.code_emitter import CodeEmitter\n", "CodeEmitter import"),
        (
            "from pytra.compiler.transpile_cli import dump_codegen_options_text, parse_py2cpp_argv, resolve_codegen_options, validate_codegen_options\n",
            "transpile_cli import",
        ),
        ("from hooks.cpp.hooks.cpp_hooks import build_cpp_hooks\n", "build_cpp_hooks import"),
    ]
    out = text
    missing: list[str] = []
    for target, label in targets:
        if target in out:
            out = out.replace(target, "", 1)
        else:
            missing.append(label)
    if len(missing) > 0:
        raise RuntimeError("failed to remove required import lines: " + ", ".join(missing))
    return out


def _extract_top_level_block(text: str, name: str, kind: str) -> str:
    lines = text.splitlines(keepends=True)
    marker = f"{kind} {name}"
    start = -1
    for i, line in enumerate(lines):
        if line.startswith(marker):
            start = i
            if i > 0 and lines[i - 1].startswith("@"):
                start = i - 1
            break
    if start < 0:
        raise RuntimeError(f"block not found: {kind} {name}")
    end = len(lines)
    i = start + 1
    while i < len(lines):
        line = lines[i]
        if line.startswith("def ") or line.startswith("class ") or line.startswith("@"):
            end = i
            break
        i += 1
    block = "".join(lines[start:end]).rstrip() + "\n"
    return block


def _extract_support_blocks() -> str:
    cli_text = SRC_TRANSPILE_CLI.read_text(encoding="utf-8")
    names = [
        "resolve_codegen_options",
        "validate_codegen_options",
        "dump_codegen_options_text",
        "empty_parse_dict",
        "_parse_error_dict",
        "parse_py2cpp_argv",
    ]
    parts: list[str] = []
    for name in names:
        parts.append(_extract_top_level_block(cli_text, name, "def"))
    # selfhost では hooks モジュールを import しないため、最小スタブを同梱する。
    parts.append(
        "def build_cpp_hooks() -> dict[str, Any]:\n"
        "    return {}\n"
    )
    return "\n".join(parts)


def _insert_code_emitter(text: str, base_class_text: str, support_blocks: str) -> str:
    marker = "CPP_HEADER = "
    i = text.find(marker)
    if i < 0:
        raise RuntimeError("CPP_HEADER marker not found in py2cpp.py")
    prefix = text[:i]
    suffix = text[i:]
    return prefix.rstrip() + "\n\n" + support_blocks + "\n" + base_class_text + "\n" + suffix


def _patch_code_emitter_hooks_for_selfhost(text: str) -> str:
    """CodeEmitter の hook 呼び出しヘルパを selfhost 用に no-op 化する。"""
    start_marker = "    def _call_hook("
    end_marker = "\n    def _call_hook1("
    i = text.find(start_marker)
    j = text.find(end_marker)
    if i < 0:
        raise RuntimeError("failed to find _call_hook block in merged selfhost source")
    if j <= i:
        raise RuntimeError("failed to find _call_hook1 marker after _call_hook in merged selfhost source")
    block = text[i:j]
    targets = [
        "            return fn(self)\n",
        "            return fn(self, arg0)\n",
        "            return fn(self, arg0, arg1)\n",
        "            return fn(self, arg0, arg1, arg2)\n",
        "            return fn(self, arg0, arg1, arg2, arg3)\n",
        "            return fn(self, arg0, arg1, arg2, arg3, arg4)\n",
        "            return fn(self, arg0, arg1, arg2, arg3, arg4, arg5)\n",
    ]
    missing: list[str] = []
    for target in targets:
        if target in block:
            block = block.replace(target, "            return None\n", 1)
        else:
            missing.append(target.strip())
    if len(missing) > 0:
        raise RuntimeError("failed to neutralize _call_hook dynamic calls: " + ", ".join(missing))
    return text[:i] + block + text[j:]


def main() -> int:
    py2cpp_text = SRC_PY2CPP.read_text(encoding="utf-8")
    base_text = SRC_BASE.read_text(encoding="utf-8")
    support_blocks = _extract_support_blocks()

    base_class = _strip_triple_quoted_docstrings(_extract_code_emitter_class(base_text))
    py2cpp_text = _remove_import_line(py2cpp_text)
    out = _insert_code_emitter(py2cpp_text, base_class, support_blocks)
    out = _patch_code_emitter_hooks_for_selfhost(out)

    DST_SELFHOST.parent.mkdir(parents=True, exist_ok=True)
    DST_SELFHOST.write_text(out, encoding="utf-8")
    print(str(DST_SELFHOST))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
