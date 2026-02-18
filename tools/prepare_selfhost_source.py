#!/usr/bin/env python3
"""Prepare selfhost/py2cpp.py as a self-contained source.

This script inlines CodeEmitter into py2cpp.py so transpiling selfhost input
no longer depends on cross-module import resolution.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC_PY2CPP = ROOT / "src" / "py2cpp.py"
SRC_BASE = ROOT / "src" / "common" / "code_emitter.py"
DST_SELFHOST = ROOT / "selfhost" / "py2cpp.py"


def _extract_code_emitter_class(text: str) -> str:
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
    target = "from common.code_emitter import CodeEmitter\n"
    if target not in text:
        raise RuntimeError("py2cpp.py import for CodeEmitter not found")
    return text.replace(target, "", 1)


def _insert_code_emitter(text: str, base_class_text: str) -> str:
    marker = "CPP_HEADER = "
    i = text.find(marker)
    if i < 0:
        raise RuntimeError("CPP_HEADER marker not found in py2cpp.py")
    prefix = text[:i]
    suffix = text[i:]
    return prefix.rstrip() + "\n\n" + base_class_text + "\n" + suffix


def main() -> int:
    py2cpp_text = SRC_PY2CPP.read_text(encoding="utf-8")
    base_text = SRC_BASE.read_text(encoding="utf-8")

    base_class = _strip_triple_quoted_docstrings(_extract_code_emitter_class(base_text))
    py2cpp_text = _remove_import_line(py2cpp_text)
    out = _insert_code_emitter(py2cpp_text, base_class)

    DST_SELFHOST.parent.mkdir(parents=True, exist_ok=True)
    DST_SELFHOST.write_text(out, encoding="utf-8")
    print(str(DST_SELFHOST))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
