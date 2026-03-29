#!/usr/bin/env python3
"""Guard EAST stage boundaries to prevent cross-stage semantic regressions."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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


def _iter_string_literals(tree: ast.Module) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append((node.value, int(getattr(node, "lineno", 0))))
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


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _check_import_call_boundary(
    path: Path,
    *,
    forbidden_import_prefixes: tuple[str, ...],
    forbidden_calls: tuple[str, ...],
    allowed_imports: tuple[str, ...] = (),
    stage_label: str,
    errors: list[str],
) -> None:
    tree = _load_ast(path)
    rel = _display_path(path)
    for name, lineno in _iter_imports(tree):
        if name in allowed_imports:
            continue
        if _matches_prefix(name, forbidden_import_prefixes):
            errors.append(f"{rel}:{lineno} disallowed import in {stage_label}: {name}")
    for name, lineno in _iter_calls(tree):
        if _matches_call(name, forbidden_calls):
            errors.append(f"{rel}:{lineno} disallowed call in {stage_label}: {name}")


def _check_semantic_literals(
    path: Path,
    *,
    forbidden_literals: tuple[str, ...],
    stage_label: str,
    errors: list[str],
) -> None:
    tree = _load_ast(path)
    rel = _display_path(path)
    for value, lineno in _iter_string_literals(tree):
        if value in forbidden_literals:
            errors.append(f"{rel}:{lineno} disallowed semantic literal in {stage_label}: {value}")


def _check_east2_boundary(errors: list[str]) -> None:
    paths = (
        ROOT / "src" / "toolchain" / "misc" / "east_parts" / "east2.py",
        ROOT / "src" / "toolchain" / "compile" / "east2.py",
    )
    forbidden_import_prefixes = (
        "toolchain.misc.east_parts.east3",
        "toolchain.misc.east_parts.east2_to_east3_lowering",
        "toolchain.compile.east3",
        "toolchain.compile.east2_to_east3_lowering",
        "src.toolchain.misc.east_parts.east3",
        "src.toolchain.misc.east_parts.east2_to_east3_lowering",
        "src.toolchain.compile.east3",
        "src.toolchain.compile.east2_to_east3_lowering",
    )
    forbidden_calls = (
        "lower_east2_to_east3",
        "lower_east2_to_east3_document",
        "load_east3_document",
    )
    forbidden_literals = ("dispatch_mode", "schema_version", "linked_program_v1")
    for path in paths:
        _check_import_call_boundary(
            path,
            forbidden_import_prefixes=forbidden_import_prefixes,
            forbidden_calls=forbidden_calls,
            stage_label="EAST2 stage",
            errors=errors,
        )
        if path.parent.name == "ir":
            _check_semantic_literals(
                path,
                forbidden_literals=forbidden_literals,
                stage_label="EAST2 stage",
                errors=errors,
            )


def _check_code_emitter_boundary(errors: list[str]) -> None:
    shim_path = ROOT / "src" / "toolchain" / "misc" / "east_parts" / "code_emitter.py"
    impl_path = ROOT / "src" / "toolchain" / "emit" / "common" / "emitter" / "code_emitter.py"
    paths = (
        (shim_path, ()),
        (
            impl_path,
            (
                "toolchain.misc.transpile_cli",
                "toolchain.misc.transpile_cli.make_user_error",
            ),
        ),
    )
    forbidden_import_prefixes = (
        "toolchain.misc.east",
        "toolchain.misc.transpile_cli",
        "toolchain.misc.east_parts.east1",
        "toolchain.misc.east_parts.east2",
        "toolchain.misc.east_parts.east3",
        "toolchain.misc.east_parts.east2_to_east3_lowering",
        "src.toolchain.misc.east",
        "src.toolchain.misc.transpile_cli",
        "src.toolchain.misc.east_parts.east1",
        "src.toolchain.misc.east_parts.east2",
        "src.toolchain.misc.east_parts.east3",
        "src.toolchain.misc.east_parts.east2_to_east3_lowering",
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
    forbidden_literals = ("east_stage", "schema_version", "linked_program_v1")
    for path, allowed_imports in paths:
        _check_import_call_boundary(
            path,
            forbidden_import_prefixes=forbidden_import_prefixes,
            forbidden_calls=forbidden_calls,
            allowed_imports=allowed_imports,
            stage_label="CodeEmitter base",
            errors=errors,
        )
        if path.parent.name == "emitter":
            _check_semantic_literals(
                path,
                forbidden_literals=forbidden_literals,
                stage_label="CodeEmitter base",
                errors=errors,
            )


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
