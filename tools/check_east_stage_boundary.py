#!/usr/bin/env python3
"""Guard EAST stage boundaries to prevent cross-stage semantic regressions."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _qualname(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _qualname(node.value)
        if base == "":
            return node.attr
        return base + "." + node.attr
    if isinstance(node, ast.Call):
        return _qualname(node.func)
    return ""


def _iter_imports(tree: ast.Module) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.append((alias.name, int(getattr(node, "lineno", 0))))
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            lineno = int(getattr(node, "lineno", 0))
            if module != "":
                out.append((module, lineno))
            for alias in node.names:
                if module == "":
                    out.append((alias.name, lineno))
                else:
                    out.append((module + "." + alias.name, lineno))
    return out


def _iter_calls(tree: ast.Module) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = _qualname(node.func)
            if name != "":
                out.append((name, int(getattr(node, "lineno", 0))))
    return out


def _matches_prefix(name: str, prefixes: tuple[str, ...]) -> bool:
    for prefix in prefixes:
        if name == prefix or name.startswith(prefix + "."):
            return True
    return False


def _matches_call(name: str, forbidden: tuple[str, ...]) -> bool:
    for item in forbidden:
        if name == item or name.endswith("." + item):
            return True
    return False


def _load_ast(path: Path) -> ast.Module:
    text = path.read_text(encoding="utf-8")
    return ast.parse(text, filename=str(path))


def _check_east2_boundary(errors: list[str]) -> None:
    path = ROOT / "src" / "pytra" / "compiler" / "east_parts" / "east2.py"
    tree = _load_ast(path)
    rel = path.relative_to(ROOT).as_posix()
    forbidden_import_prefixes = (
        "pytra.compiler.east_parts.east3",
        "pytra.compiler.east_parts.east2_to_east3_lowering",
        "src.pytra.compiler.east_parts.east3",
        "src.pytra.compiler.east_parts.east2_to_east3_lowering",
    )
    forbidden_calls = (
        "lower_east2_to_east3",
        "lower_east2_to_east3_document",
        "load_east3_document",
    )
    for name, lineno in _iter_imports(tree):
        if _matches_prefix(name, forbidden_import_prefixes):
            errors.append(f"{rel}:{lineno} disallowed import in EAST2 stage: {name}")
    for name, lineno in _iter_calls(tree):
        if _matches_call(name, forbidden_calls):
            errors.append(f"{rel}:{lineno} disallowed lowering call in EAST2 stage: {name}")


def _check_code_emitter_boundary(errors: list[str]) -> None:
    path = ROOT / "src" / "pytra" / "compiler" / "east_parts" / "code_emitter.py"
    tree = _load_ast(path)
    rel = path.relative_to(ROOT).as_posix()
    forbidden_import_prefixes = (
        "pytra.compiler.east",
        "pytra.compiler.transpile_cli",
        "pytra.compiler.east_parts.east1",
        "pytra.compiler.east_parts.east2",
        "pytra.compiler.east_parts.east3",
        "pytra.compiler.east_parts.east2_to_east3_lowering",
        "src.pytra.compiler.east",
        "src.pytra.compiler.transpile_cli",
        "src.pytra.compiler.east_parts.east1",
        "src.pytra.compiler.east_parts.east2",
        "src.pytra.compiler.east_parts.east3",
        "src.pytra.compiler.east_parts.east2_to_east3_lowering",
    )
    forbidden_calls = (
        "convert_source_to_east_with_backend",
        "convert_path",
        "load_east_document",
        "load_east_document_compat",
        "load_east3_document",
        "normalize_east1_to_east2_document",
        "lower_east2_to_east3",
        "lower_east2_to_east3_document",
    )
    for name, lineno in _iter_imports(tree):
        if _matches_prefix(name, forbidden_import_prefixes):
            errors.append(f"{rel}:{lineno} disallowed import in CodeEmitter base: {name}")
    for name, lineno in _iter_calls(tree):
        if _matches_call(name, forbidden_calls):
            errors.append(f"{rel}:{lineno} disallowed stage reinterpretation call in CodeEmitter base: {name}")


def main() -> int:
    errors: list[str] = []
    _check_east2_boundary(errors)
    _check_code_emitter_boundary(errors)
    if errors:
        for err in errors:
            print("[NG]", err)
        return 1
    print("[OK] east stage boundary guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
