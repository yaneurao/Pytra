#!/usr/bin/env python3
"""Enforce top-level responsibility boundary of src/py2cpp.py.

Policy:
- src/py2cpp.py top-level defs must be either:
  1) C++-specific responsibilities, or
  2) explicit compatibility wrappers that delegate to shared compiler APIs.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "src" / "py2cpp.py"


# C++ 固有責務として py2cpp.py に残すトップレベル関数。
CPP_SPECIFIC_TOPLEVEL: set[str] = {
    "_build_cpp_hooks_impl",
    "_module_tail_to_cpp_header_path",
    "_join_runtime_path",
    "_runtime_cpp_header_exists_for_module",
    "load_cpp_profile",
    "load_cpp_bin_ops",
    "load_cpp_cmp_ops",
    "load_cpp_aug_ops",
    "load_cpp_aug_bin",
    "load_cpp_type_map",
    "load_cpp_hooks",
    "load_cpp_identifier_rules",
    "load_cpp_module_attr_call_map",
    "cpp_string_lit",
    "cpp_char_lit",
    "_transpile_to_cpp_with_map",
    "transpile_to_cpp",
    "_header_cpp_type_from_east",
    "_header_guard_from_path",
    "_header_allows_none_default",
    "_header_none_default_expr_for_type",
    "_header_render_default_expr",
    "build_cpp_header_from_east",
    "_runtime_module_tail_from_source_path",
    "_prepend_generated_cpp_banner",
    "_is_runtime_emit_input_path",
    "_runtime_output_rel_tail",
    "_runtime_namespace_for_tail",
    "_write_multi_file_cpp",
    "_is_valid_cpp_namespace_name",
    "main",
}

# 共通層 API へ委譲する互換ラッパ。
COMPAT_WRAPPER_TOPLEVEL: set[str] = {
    "load_east",
    "_analyze_import_graph",
    "build_module_east_map",
    "dump_deps_graph_text",
}

# ラッパごとの最低限の委譲シグネチャ検査（source substring）。
WRAPPER_DELEGATION_MARKERS: dict[str, str] = {
    "load_east": "load_east3_document(",
    "_analyze_import_graph": "analyze_import_graph(",
    "build_module_east_map": "build_module_east_map_common(",
    "dump_deps_graph_text": "dump_deps_graph_text_common(",
}


def _collect_top_level_defs(tree: ast.Module) -> list[ast.FunctionDef]:
    out: list[ast.FunctionDef] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            out.append(node)
    return out


def _slice_lines(src: str, node: ast.AST) -> str:
    lines = src.splitlines()
    lineno = getattr(node, "lineno", 1)
    end_lineno = getattr(node, "end_lineno", lineno)
    start = max(1, lineno) - 1
    end = max(start + 1, end_lineno)
    return "\n".join(lines[start:end])


def main() -> int:
    src = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(src)
    defs = _collect_top_level_defs(tree)
    names = sorted([d.name for d in defs])

    allowed = CPP_SPECIFIC_TOPLEVEL | COMPAT_WRAPPER_TOPLEVEL
    extras = [name for name in names if name not in allowed]
    missing = sorted([name for name in allowed if name not in names])

    if extras:
        print("[FAIL] py2cpp boundary guard: unexpected top-level def(s)")
        for name in extras:
            print(f"  - {name}")
        print("Move language-agnostic logic to src/pytra/compiler/* first.")
        return 1

    # 許可集合を縮退した場合の追従漏れも検出。
    if missing:
        print("[FAIL] py2cpp boundary guard: expected def(s) missing from src/py2cpp.py")
        for name in missing:
            print(f"  - {name}")
        print("Update tools/check_py2cpp_boundary.py if boundary contract intentionally changed.")
        return 1

    by_name: dict[str, ast.FunctionDef] = {d.name: d for d in defs}
    for wrapper_name, marker in WRAPPER_DELEGATION_MARKERS.items():
        node = by_name.get(wrapper_name)
        if node is None:
            print(f"[FAIL] wrapper missing: {wrapper_name}")
            return 1
        block = _slice_lines(src, node)
        if marker not in block:
            print(f"[FAIL] wrapper does not delegate as expected: {wrapper_name}")
            print(f"  expected marker: {marker}")
            return 1

    print("[OK] py2cpp boundary guard passed")
    print(f"  top-level defs: {len(names)}")
    print(f"  cpp-specific: {len(CPP_SPECIFIC_TOPLEVEL)}")
    print(f"  compatibility wrappers: {len(COMPAT_WRAPPER_TOPLEVEL)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
