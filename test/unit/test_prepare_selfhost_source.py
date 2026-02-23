from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "prepare_selfhost_source.py"


def _load_prepare_module() -> object:
    spec = importlib.util.spec_from_file_location("prepare_selfhost_source", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load tools/prepare_selfhost_source.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _slice_block(text: str, start_marker: str, end_marker: str) -> str:
    i = text.find(start_marker)
    if i < 0:
        raise RuntimeError(f"start marker not found: {start_marker}")
    j = text.find(end_marker, i + len(start_marker))
    if j < 0:
        raise RuntimeError(f"end marker not found: {end_marker}")
    return text[i:j]


class PrepareSelfhostSourceTest(unittest.TestCase):
    def test_remove_import_line_removes_required_imports(self) -> None:
        mod = _load_prepare_module()
        py2cpp_text = mod.SRC_PY2CPP.read_text(encoding="utf-8")
        removed = mod._remove_import_line(py2cpp_text)
        self.assertNotIn(
            "from pytra.compiler.east_parts.code_emitter import CodeEmitter\n",
            removed,
        )
        self.assertNotIn(
            "from pytra.compiler.transpile_cli import append_unique_non_empty, assign_targets, collect_import_modules, collect_store_names_from_target, collect_symbols_from_stmt, collect_symbols_from_stmt_list, count_text_lines, dict_any_get, dict_any_get_str, dict_any_get_list, dict_any_get_dict, dict_any_get_dict_list, dict_any_get_str_list, dict_any_kind, dict_str_get, dump_codegen_options_text, dump_deps_text, extract_function_arg_types_from_python_source, extract_function_signatures_from_python_source, first_import_detail_line, format_graph_list_section, format_import_graph_report, graph_cycle_dfs, inject_after_includes_block, is_known_non_user_import, is_pytra_module_name, join_str_list, local_binding_name, load_east_document, looks_like_runtime_function_name, make_user_error, meta_import_bindings, meta_qualified_symbol_refs, mkdirs_for_cli, module_analyze_metrics, module_id_from_east_for_graph, module_name_from_path_for_graph, module_parse_metrics, module_export_table, build_module_symbol_index, build_module_east_map_from_analysis, build_module_type_schema, module_rel_label, name_target_id, normalize_param_annotation, parse_py2cpp_argv, check_analyze_stage_guards, check_guard_limit, check_parse_stage_guards, resolve_guard_limits, parse_user_error, path_key_for_graph, path_parent_text, python_module_exists_under, collect_reserved_import_conflicts, rel_disp_for_graph, replace_first, resolve_codegen_options, resolve_module_name, resolve_module_name_for_graph, resolve_user_module_path_for_graph, sanitize_module_label, select_guard_module_map, set_import_module_binding, set_import_symbol_binding, set_import_symbol_binding_and_module_set, sort_str_list_copy, collect_user_module_files_for_graph, finalize_import_graph_analysis, split_graph_issue_entry, split_infix_once, split_top_level_csv, split_top_level_union, split_type_args, split_ws_tokens, stmt_assigned_names, stmt_child_stmt_lists, stmt_list_parse_metrics, stmt_list_scope_depth, stmt_target_name, validate_codegen_options, validate_from_import_symbols_or_raise, validate_import_graph_or_raise, write_text_file\n",
            removed,
        )
        self.assertNotIn(
            "from hooks.cpp.hooks.cpp_hooks import build_cpp_hooks\n",
            removed,
        )

    def test_remove_import_line_raises_when_required_import_missing(self) -> None:
        mod = _load_prepare_module()
        broken = (
            "from pytra.compiler.east_parts.code_emitter import CodeEmitter\n"
            "from pytra.compiler.transpile_cli import append_unique_non_empty, assign_targets, collect_import_modules, collect_store_names_from_target, collect_symbols_from_stmt, collect_symbols_from_stmt_list, count_text_lines, dict_any_get, dict_any_get_str, dict_any_get_list, dict_any_get_dict, dict_any_get_dict_list, dict_any_get_str_list, dict_any_kind, dict_str_get, dump_codegen_options_text, dump_deps_text, extract_function_arg_types_from_python_source, extract_function_signatures_from_python_source, first_import_detail_line, format_graph_list_section, format_import_graph_report, graph_cycle_dfs, inject_after_includes_block, is_known_non_user_import, is_pytra_module_name, join_str_list, local_binding_name, load_east_document, looks_like_runtime_function_name, make_user_error, meta_import_bindings, meta_qualified_symbol_refs, mkdirs_for_cli, module_analyze_metrics, module_id_from_east_for_graph, module_name_from_path_for_graph, module_parse_metrics, module_export_table, build_module_symbol_index, build_module_east_map_from_analysis, build_module_type_schema, module_rel_label, name_target_id, normalize_param_annotation, parse_py2cpp_argv, check_analyze_stage_guards, check_guard_limit, check_parse_stage_guards, resolve_guard_limits, parse_user_error, path_key_for_graph, path_parent_text, python_module_exists_under, collect_reserved_import_conflicts, rel_disp_for_graph, replace_first, resolve_codegen_options, resolve_module_name, resolve_module_name_for_graph, resolve_user_module_path_for_graph, sanitize_module_label, select_guard_module_map, set_import_module_binding, set_import_symbol_binding, set_import_symbol_binding_and_module_set, sort_str_list_copy, collect_user_module_files_for_graph, finalize_import_graph_analysis, split_graph_issue_entry, split_infix_once, split_top_level_csv, split_top_level_union, split_type_args, split_ws_tokens, stmt_assigned_names, stmt_child_stmt_lists, stmt_list_parse_metrics, stmt_list_scope_depth, stmt_target_name, validate_codegen_options, validate_from_import_symbols_or_raise, validate_import_graph_or_raise, write_text_file\n"
        )
        with self.assertRaisesRegex(RuntimeError, "build_cpp_hooks import"):
            mod._remove_import_line(broken)

    def test_extract_support_blocks_does_not_inline_build_cpp_hooks_stub(self) -> None:
        mod = _load_prepare_module()
        support_blocks = mod._extract_support_blocks()
        self.assertIn("def join_str_list(sep: str, items: list[str]) -> str:", support_blocks)
        self.assertIn("def mkdirs_for_cli(path_txt: str) -> None:", support_blocks)
        self.assertIn("def path_parent_text(path_obj: Path) -> str:", support_blocks)
        self.assertIn("def replace_first(text: str, old: str, replacement: str) -> str:", support_blocks)
        self.assertIn("def inject_after_includes_block(cpp_text: str, block: str) -> str:", support_blocks)
        self.assertIn("def split_infix_once(text: str, sep: str) -> tuple[str, str, bool]:", support_blocks)
        self.assertIn("def local_binding_name(name: str, asname: str) -> str:", support_blocks)
        self.assertIn("def split_graph_issue_entry(v_txt: str) -> tuple[str, str]:", support_blocks)
        self.assertIn("def split_top_level_csv(text: str) -> list[str]:", support_blocks)
        self.assertIn("def split_top_level_union(text: str) -> list[str]:", support_blocks)
        self.assertIn("def split_type_args(text: str) -> list[str]:", support_blocks)
        self.assertIn("def split_ws_tokens(text: str) -> list[str]:", support_blocks)
        self.assertIn("def normalize_param_annotation(ann: str) -> str:", support_blocks)
        self.assertIn("def extract_function_signatures_from_python_source(src_path: Path)", support_blocks)
        self.assertIn("def extract_function_arg_types_from_python_source(src_path: Path)", support_blocks)
        self.assertIn("def append_unique_non_empty(items: list[str], seen: set[str], value: str) -> None:", support_blocks)
        self.assertIn("def assign_targets(stmt: dict[str, object]) -> list[dict[str, object]]:", support_blocks)
        self.assertIn("def sort_str_list_copy(items: list[str]) -> list[str]:", support_blocks)
        self.assertIn("def collect_user_module_files_for_graph(visited_order: list[str], key_to_path: dict[str, Path]) -> list[str]:", support_blocks)
        self.assertIn("def finalize_import_graph_analysis(", support_blocks)
        self.assertIn("def count_text_lines(text: str) -> int:", support_blocks)
        self.assertIn("def dict_any_get(src: dict[str, object], key: str) -> object | None:", support_blocks)
        self.assertIn("def dict_any_get_str(src: dict[str, object], key: str, default_value: str = \"\") -> str:", support_blocks)
        self.assertIn("def dict_any_get_list(src: dict[str, object], key: str) -> list[object]:", support_blocks)
        self.assertIn("def dict_any_get_dict(src: dict[str, object], key: str) -> dict[str, object]:", support_blocks)
        self.assertIn("def dict_any_get_dict_list(src: dict[str, object], key: str) -> list[dict[str, object]]:", support_blocks)
        self.assertIn("def dict_any_get_str_list(src: dict[str, object], key: str) -> list[str]:", support_blocks)
        self.assertIn("def dict_any_kind(src: dict[str, object]) -> str:", support_blocks)
        self.assertIn("def name_target_id(target: dict[str, object]) -> str:", support_blocks)
        self.assertIn("def stmt_assigned_names(stmt: dict[str, object]) -> list[str]:", support_blocks)
        self.assertIn("def stmt_child_stmt_lists(stmt: dict[str, object]) -> list[list[dict[str, object]]]:", support_blocks)
        self.assertIn("def collect_store_names_from_target(target: dict[str, object], out: set[str]) -> None:", support_blocks)
        self.assertIn("def collect_symbols_from_stmt(stmt: dict[str, object]) -> set[str]:", support_blocks)
        self.assertIn("def collect_symbols_from_stmt_list(body: list[dict[str, object]]) -> set[str]:", support_blocks)
        self.assertIn("def stmt_list_parse_metrics(body: list[dict[str, object]], depth: int) -> tuple[int, int]:", support_blocks)
        self.assertIn("def stmt_list_scope_depth(", support_blocks)
        self.assertIn("def stmt_target_name(stmt: dict[str, object]) -> str:", support_blocks)
        self.assertIn("def dict_str_get(src: dict[str, str], key: str, default_value: str = \"\") -> str:", support_blocks)
        self.assertIn("def looks_like_runtime_function_name(name: str) -> bool:", support_blocks)
        self.assertIn("def first_import_detail_line(source_text: str, kind: str) -> str:", support_blocks)
        self.assertIn("def make_user_error(category: str, summary: str, details: list[str]) -> Exception:", support_blocks)
        self.assertIn("def parse_user_error(err_text: str) -> dict[str, object]:", support_blocks)
        self.assertIn("def load_east_document(input_path: Path, parser_backend: str = \"self_hosted\") -> dict[str, object]:", support_blocks)
        self.assertIn("def is_pytra_module_name(module_name: str) -> bool:", support_blocks)
        self.assertIn("def module_name_from_path_for_graph(root: Path, module_path: Path) -> str:", support_blocks)
        self.assertIn("def module_id_from_east_for_graph(root: Path, module_path: Path, east_doc: dict[str, Any]) -> str:", support_blocks)
        self.assertIn("def sanitize_module_label(text: str) -> str:", support_blocks)
        self.assertIn("def module_rel_label(root: Path, module_path: Path) -> str:", support_blocks)
        self.assertIn("def module_export_table(", support_blocks)
        self.assertIn("def build_module_symbol_index(", support_blocks)
        self.assertIn("def build_module_east_map_from_analysis(", support_blocks)
        self.assertIn("def build_module_type_schema(", support_blocks)
        self.assertIn("def meta_import_bindings(east_module: dict[str, object]) -> list[dict[str, str]]:", support_blocks)
        self.assertIn("def meta_qualified_symbol_refs(east_module: dict[str, object]) -> list[dict[str, str]]:", support_blocks)
        self.assertIn("def path_key_for_graph(p: Path) -> str:", support_blocks)
        self.assertIn("def rel_disp_for_graph(base: Path, p: Path) -> str:", support_blocks)
        self.assertIn("def python_module_exists_under(root_dir: Path, module_tail: str) -> bool:", support_blocks)
        self.assertIn("def collect_reserved_import_conflicts(root: Path) -> list[str]:", support_blocks)
        self.assertIn("def module_parse_metrics(east_module: dict[str, object]) -> dict[str, int]:", support_blocks)
        self.assertIn("def module_analyze_metrics(", support_blocks)
        self.assertIn("def select_guard_module_map(", support_blocks)
        self.assertIn("def set_import_module_binding(", support_blocks)
        self.assertIn("def set_import_symbol_binding(", support_blocks)
        self.assertIn("def set_import_symbol_binding_and_module_set(", support_blocks)
        self.assertIn("def resolve_user_module_path_for_graph(module_name: str, search_root: Path) -> Path:", support_blocks)
        self.assertIn("def format_graph_list_section(out: str, label: str, items: list[str]) -> str:", support_blocks)
        self.assertIn("def dump_deps_text(east_module: dict[str, object]) -> str:", support_blocks)
        self.assertIn("def format_import_graph_report(analysis: dict[str, object]) -> str:", support_blocks)
        self.assertIn("def collect_import_modules(east_module: dict[str, object]) -> list[str]:", support_blocks)
        self.assertIn("def is_known_non_user_import(", support_blocks)
        self.assertIn("def resolve_module_name_for_graph(", support_blocks)
        self.assertIn("def resolve_module_name(", support_blocks)
        self.assertIn("def validate_from_import_symbols_or_raise(", support_blocks)
        self.assertIn("def validate_import_graph_or_raise(analysis: dict[str, object]) -> None:", support_blocks)
        self.assertIn("def graph_cycle_dfs(", support_blocks)
        self.assertIn("def write_text_file(path_obj: Path, text: str) -> None:", support_blocks)
        self.assertIn("def parse_guard_limit_or_raise(raw: str, option_name: str) -> int:", support_blocks)
        self.assertIn("def guard_profile_base_limits(profile: str) -> dict[str, int]:", support_blocks)
        self.assertIn("def check_parse_stage_guards(", support_blocks)
        self.assertIn("def check_analyze_stage_guards(", support_blocks)
        self.assertIn("def resolve_guard_limits(", support_blocks)
        self.assertIn("def raise_guard_limit_exceeded(", support_blocks)
        self.assertIn("def check_guard_limit(", support_blocks)
        self.assertNotIn("def build_cpp_hooks() -> dict[str, Any]:", support_blocks)

    def test_load_cpp_hooks_is_patched_to_empty_dict_in_merged_source(self) -> None:
        mod = _load_prepare_module()
        py2cpp_text = mod.SRC_PY2CPP.read_text(encoding="utf-8")
        base_text = mod.SRC_BASE.read_text(encoding="utf-8")
        support_blocks = mod._extract_support_blocks()
        base_class = mod._strip_triple_quoted_docstrings(mod._extract_code_emitter_class(base_text))
        merged = mod._insert_code_emitter(mod._remove_import_line(py2cpp_text), base_class, support_blocks)
        merged = mod._patch_load_cpp_hooks_for_selfhost(merged)
        load_cpp_hooks_block = _slice_block(
            merged,
            "def load_cpp_hooks(",
            "\n\ndef load_cpp_identifier_rules(",
        )
        self.assertIn("hooks = {}", load_cpp_hooks_block)
        self.assertNotIn("hooks = build_cpp_hooks()", load_cpp_hooks_block)
        self.assertIn("try:", load_cpp_hooks_block)
        self.assertIn("if isinstance(hooks, dict):", load_cpp_hooks_block)
        self.assertNotIn("def build_cpp_hooks() -> dict[str, Any]:", merged)

    def test_hook_patch_only_replaces_call_hook_body(self) -> None:
        mod = _load_prepare_module()
        py2cpp_text = mod.SRC_PY2CPP.read_text(encoding="utf-8")
        base_text = mod.SRC_BASE.read_text(encoding="utf-8")
        support_blocks = mod._extract_support_blocks()
        base_class = mod._strip_triple_quoted_docstrings(mod._extract_code_emitter_class(base_text))
        merged = mod._insert_code_emitter(mod._remove_import_line(py2cpp_text), base_class, support_blocks)
        patched = mod._patch_code_emitter_hooks_for_selfhost(merged)

        pre_call_hook1 = _slice_block(merged, "    def _call_hook1(", "\n    def _call_hook2(")
        post_call_hook1 = _slice_block(patched, "    def _call_hook1(", "\n    def _call_hook2(")
        self.assertEqual(post_call_hook1, pre_call_hook1)
        self.assertIn("return self._call_hook(", post_call_hook1)
        self.assertNotIn("pass", post_call_hook1)

        post_call_hook = _slice_block(patched, "    def _call_hook(", "\n    def _call_hook1(")
        self.assertIn("fn = self._lookup_hook(name)", post_call_hook)
        self.assertNotIn("return fn(self", post_call_hook)
        self.assertNotIn("pass", post_call_hook)

        hook_emit_stmt_block = _slice_block(patched, "    def hook_on_emit_stmt(", "\n    def hook_on_emit_stmt_kind(")
        self.assertIn("v = self._call_hook1(", hook_emit_stmt_block)
        self.assertIn("if isinstance(v, bool):", hook_emit_stmt_block)
        self.assertNotIn("pass", hook_emit_stmt_block)

    def test_hook_patch_raises_when_markers_missing(self) -> None:
        mod = _load_prepare_module()
        with self.assertRaisesRegex(RuntimeError, "_call_hook block"):
            mod._patch_code_emitter_hooks_for_selfhost("class CodeEmitter:\n    pass\n")

        broken_order = (
            "class CodeEmitter:\n"
            "    def _call_hook(self):\n"
            "        return None\n"
            "    def hook_on_emit_stmt(self):\n"
            "        return None\n"
        )
        with self.assertRaisesRegex(RuntimeError, "_call_hook1 marker"):
            mod._patch_code_emitter_hooks_for_selfhost(broken_order)

        broken_block = (
            "class CodeEmitter:\n"
            "    def _call_hook(\n"
            "        self,\n"
            "        name: str,\n"
            "    ) -> Any:\n"
            "        return None\n"
            "    def _call_hook1(self, name: str, arg0: Any) -> Any:\n"
            "        return self._call_hook(name, arg0, None, None, None, None, None, 1)\n"
        )
        with self.assertRaisesRegex(RuntimeError, "neutralize _call_hook dynamic calls"):
            mod._patch_code_emitter_hooks_for_selfhost(broken_block)

    def test_load_cpp_hooks_patch_raises_when_markers_missing(self) -> None:
        mod = _load_prepare_module()
        with self.assertRaisesRegex(RuntimeError, "load_cpp_hooks block"):
            mod._patch_load_cpp_hooks_for_selfhost("def x():\n    pass\n")

        broken_order = (
            "def load_cpp_hooks(profile: dict[str, Any] | None = None) -> dict[str, Any]:\n"
            "    return {}\n"
        )
        with self.assertRaisesRegex(RuntimeError, "load_cpp_identifier_rules marker"):
            mod._patch_load_cpp_hooks_for_selfhost(broken_order)

        broken_call = (
            "def load_cpp_hooks(profile: dict[str, Any] | None = None) -> dict[str, Any]:\n"
            "    hooks: Any = {}\n"
            "    try:\n"
            "        hooks = {}\n"
            "    except Exception:\n"
            "        return {}\n"
            "\n"
            "def load_cpp_identifier_rules() -> tuple[set[str], str]:\n"
            "    return set(), \"\"\n"
        )
        with self.assertRaisesRegex(RuntimeError, "hooks = build_cpp_hooks"):
            mod._patch_load_cpp_hooks_for_selfhost(broken_call)


if __name__ == "__main__":
    unittest.main()
