#!/usr/bin/env python3
"""Static import guard for `pytra` 3-layer boundaries.

Rules:
- `frontends` must not import `backends`.
- `ir` must not import `backends`.
- `backends` must not import `pytra.frontends`.
- `ir` must not import `pytra.frontends` except explicit allowlist paths.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FRONTENDS_ROOT = ROOT / "src" / "pytra" / "frontends"
IR_ROOT = ROOT / "src" / "pytra" / "ir"
BACKENDS_ROOT = ROOT / "src" / "backends"

ALLOW_IR_FRONTENDS_IMPORTS = {
    (IR_ROOT / "core.py").resolve(),
}


def _module_matches(module_name: str, prefixes: list[str]) -> bool:
    for prefix in prefixes:
        if module_name == prefix or module_name.startswith(prefix + "."):
            return True
    return False


def _iter_import_targets(tree: ast.AST) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append((int(node.lineno), str(alias.name)))
        elif isinstance(node, ast.ImportFrom):
            if int(node.level) != 0:
                continue
            if isinstance(node.module, str) and node.module != "":
                out.append((int(node.lineno), str(node.module)))
    return out


def _group_for(path: Path) -> str:
    resolved = path.resolve()
    if resolved.is_relative_to(FRONTENDS_ROOT):
        return "frontends"
    if resolved.is_relative_to(IR_ROOT):
        return "ir"
    if resolved.is_relative_to(BACKENDS_ROOT):
        return "backends"
    return ""


def _check_file(path: Path) -> list[str]:
    errs: list[str] = []
    group = _group_for(path)
    if group == "":
        return errs

    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        rel = path.relative_to(ROOT).as_posix()
        return [f"{rel}:1: read error: {exc}"]

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        rel = path.relative_to(ROOT).as_posix()
        ln = int(exc.lineno) if isinstance(exc.lineno, int) else 1
        return [f"{rel}:{ln}: syntax error while scanning imports: {exc.msg}"]

    rel = path.relative_to(ROOT).as_posix()
    for lineno, module_name in _iter_import_targets(tree):
        if group == "frontends":
            if _module_matches(module_name, ["backends", "src.backends", "pytra.compiler.east_parts"]):
                errs.append(f"{rel}:{lineno}: frontends must not import `{module_name}`")
            continue

        if group == "ir":
            if _module_matches(module_name, ["backends", "src.backends"]):
                errs.append(f"{rel}:{lineno}: ir must not import `{module_name}`")
                continue
            if _module_matches(module_name, ["pytra.frontends", "src.pytra.frontends"]):
                if path.resolve() not in ALLOW_IR_FRONTENDS_IMPORTS:
                    errs.append(f"{rel}:{lineno}: ir must not import `{module_name}`")
            continue

        if group == "backends":
            if _module_matches(module_name, ["pytra.frontends", "src.pytra.frontends"]):
                errs.append(f"{rel}:{lineno}: backends must not import `{module_name}`")
            continue

    return errs


def main() -> int:
    paths = list(FRONTENDS_ROOT.rglob("*.py"))
    paths += list(IR_ROOT.rglob("*.py"))
    paths += list(BACKENDS_ROOT.rglob("*.py"))
    paths = sorted({p.resolve() for p in paths})

    errors: list[str] = []
    for p in paths:
        errors.extend(_check_file(Path(p)))

    if len(errors) == 0:
        print("[OK] pytra layer boundary check passed")
        return 0

    print("[FAIL] pytra layer boundary check")
    for msg in errors:
        print("  - " + msg)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

