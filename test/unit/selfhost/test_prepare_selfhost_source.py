from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "src").exists())
MODULE_PATH = ROOT / "tools" / "prepare_selfhost_source.py"
GENERATED_CPP_CORE = ROOT / "selfhost" / "runtime" / "cpp" / "pytra-gen" / "compiler" / "east_parts" / "core.cpp"


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
    def test_load_cpp_hooks_patch_function_is_absent(self) -> None:
        mod = _load_prepare_module()
        self.assertFalse(hasattr(mod, "_patch_load_cpp_hooks_for_selfhost"))

    def test_remove_import_line_removes_required_imports(self) -> None:
        mod = _load_prepare_module()
        py2cpp_text = mod.SRC_PY2CPP.read_text(encoding="utf-8")
        removed = mod._remove_import_line(py2cpp_text)
        self.assertNotIn(
            "from toolchain.compiler.east_parts.code_emitter import CodeEmitter\n",
            removed,
        )
        self.assertNotIn(
            "from toolchain.compiler.transpile_cli import ",
            removed,
        )
        self.assertNotIn(
            "from backends.cpp.emitter.hooks_registry import build_cpp_hooks as _build_cpp_hooks_impl\n",
            removed,
        )

    def test_remove_import_line_raises_when_required_import_missing(self) -> None:
        mod = _load_prepare_module()
        broken = (
            "from toolchain.compiler.east_parts.code_emitter import CodeEmitter\n"
            "from toolchain.compiler.transpile_cli import any_symbol\n"
        )
        with self.assertRaisesRegex(RuntimeError, "build_cpp_hooks import"):
            mod._remove_import_line(broken)

    def test_extract_support_blocks_does_not_inline_build_cpp_hooks_stub(self) -> None:
        mod = _load_prepare_module()
        support_blocks = mod._extract_support_blocks()
        self.assertIn("_JSON_NOMINALS: set[str] = {\"JsonValue\", \"JsonObj\", \"JsonArr\"}", support_blocks)
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
        self.assertIn("def parse_type_expr_text(raw_text: str, *, type_aliases: dict[str, str] | None = None) -> dict[str, Any]:", support_blocks)
        self.assertIn("def type_expr_to_string(expr: dict[str, Any]) -> str:", support_blocks)
        self.assertIn("def normalize_type_text(raw_text: str, *, type_aliases: dict[str, str] | None = None) -> str:", support_blocks)
        self.assertIn("if name in _JSON_NOMINALS:", support_blocks)
        self.assertIn("\"kind\": \"NominalAdtType\"", support_blocks)
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
        self.assertIn("def collect_store_names_from_target(", support_blocks)
        self.assertIn(
            "def collect_store_names_from_target_plan(",
            support_blocks,
        )
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
        self.assertIn("def print_user_error(err_text: str) -> None:", support_blocks)
        self.assertIn("def normalize_east_root_document(doc: dict[str, object]) -> dict[str, object]:", support_blocks)
        self.assertIn("def normalize_east1_to_east2_document(east_doc: dict[str, object]) -> dict[str, object]:", support_blocks)
        self.assertIn("def load_east_document(input_path: Path, parser_backend: str = \"self_hosted\") -> dict[str, object]:", support_blocks)
        self.assertIn(
            "def load_east3_document(",
            support_blocks,
        )
        self.assertIn("def is_pytra_module_name(module_name: str) -> bool:", support_blocks)
        self.assertIn("def module_name_from_path_for_graph(root: Path, module_path: Path) -> str:", support_blocks)
        self.assertIn("def module_id_from_east_for_graph(root: Path, module_path: Path, east_doc: dict[str, Any]) -> str:", support_blocks)
        self.assertIn("def sanitize_module_label(text: str) -> str:", support_blocks)
        self.assertIn("def module_rel_label(root: Path, module_path: Path) -> str:", support_blocks)
        self.assertIn("def module_export_table(", support_blocks)
        self.assertIn("def build_module_symbol_index(", support_blocks)
        self.assertIn("def analyze_import_graph(", support_blocks)
        self.assertIn("def build_module_east_map(", support_blocks)
        self.assertIn("def build_module_east_map_from_analysis(", support_blocks)
        self.assertIn("def build_module_type_schema(", support_blocks)
        self.assertIn("def meta_import_bindings(east_module: dict[str, object]) -> list[dict[str, str]]:", support_blocks)
        self.assertIn("def meta_qualified_symbol_refs(east_module: dict[str, object]) -> list[dict[str, str]]:", support_blocks)
        self.assertIn("def path_key_for_graph(p: Path) -> str:", support_blocks)
        self.assertIn("def rel_disp_for_graph(", support_blocks)
        self.assertIn("def python_module_exists_under(root_dir: Path, module_tail: str) -> bool:", support_blocks)
        self.assertIn("def collect_reserved_import_conflicts(root: Path) -> list[str]:", support_blocks)
        self.assertIn("def module_parse_metrics(east_module: dict[str, object]) -> dict[str, int]:", support_blocks)
        self.assertIn("def module_analyze_metrics(", support_blocks)
        self.assertIn("def select_guard_module_map(", support_blocks)
        self.assertIn("def set_import_module_binding(", support_blocks)
        self.assertIn("def set_import_symbol_binding(", support_blocks)
        self.assertIn("def set_import_symbol_binding_and_module_set(", support_blocks)
        self.assertIn("def resolve_user_module_path_for_graph(module_name: str, search_root: Path) -> Path:", support_blocks)
        self.assertIn("def format_graph_list_section(", support_blocks)
        self.assertIn("def dump_deps_text(east_module: dict[str, object]) -> str:", support_blocks)
        self.assertIn("def format_import_graph_report(analysis: dict[str, object]) -> str:", support_blocks)
        self.assertIn("def dump_deps_graph_text(", support_blocks)
        self.assertIn("def collect_import_modules(east_module: dict[str, object]) -> list[str]:", support_blocks)
        self.assertIn("def is_known_non_user_import(", support_blocks)
        self.assertIn("def resolve_module_name_for_graph(", support_blocks)
        self.assertIn("def resolve_module_name(", support_blocks)
        self.assertIn("def validate_from_import_symbols_or_raise(", support_blocks)
        self.assertIn("def validate_import_graph_or_raise(analysis: dict[str, object]) -> None:", support_blocks)
        self.assertIn("def build_module_east_map_common(", support_blocks)
        self.assertIn("def dump_deps_graph_text_common(", support_blocks)
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

    def test_extract_type_expr_support_blocks_keeps_json_nominal_helpers(self) -> None:
        mod = _load_prepare_module()
        support_blocks = mod._extract_type_expr_support_blocks()
        self.assertIn("_JSON_NOMINALS: set[str] = {\"JsonValue\", \"JsonObj\", \"JsonArr\"}", support_blocks)
        self.assertIn("def _make_union_type_expr(options: list[dict[str, Any]]) -> dict[str, Any]:", support_blocks)
        self.assertIn("def parse_type_expr_text(raw_text: str, *, type_aliases: dict[str, str] | None = None) -> dict[str, Any]:", support_blocks)
        self.assertIn("def type_expr_to_string(expr: dict[str, Any]) -> str:", support_blocks)
        self.assertIn("def normalize_type_text(raw_text: str, *, type_aliases: dict[str, str] | None = None) -> str:", support_blocks)
        self.assertIn("if name in _JSON_NOMINALS:", support_blocks)
        self.assertIn("\"kind\": \"NominalAdtType\"", support_blocks)

    def test_load_cpp_hooks_uses_factory_fallback_in_merged_source(self) -> None:
        mod = _load_prepare_module()
        py2cpp_text = mod.SRC_PY2CPP.read_text(encoding="utf-8")
        base_text = mod.SRC_BASE.read_text(encoding="utf-8")
        support_blocks = mod._extract_support_blocks()
        base_class = mod._strip_triple_quoted_docstrings(mod._extract_code_emitter_class(base_text))
        merged = mod._insert_code_emitter(mod._remove_import_line(py2cpp_text), base_class, support_blocks)
        load_cpp_hooks_block = _slice_block(
            merged,
            "def load_cpp_hooks(",
            "\n\ndef load_cpp_identifier_rules(",
        )
        self.assertIn("hooks = _build_cpp_hooks_impl()", load_cpp_hooks_block)
        self.assertIn("try:", load_cpp_hooks_block)
        self.assertIn("if isinstance(hooks, dict):", load_cpp_hooks_block)
        self.assertNotIn("from backends.cpp.emitter.hooks_registry import build_cpp_hooks as _build_cpp_hooks_impl", merged)
        self.assertIn("def _build_cpp_hooks_impl() -> dict[str, Any]:", merged)

    def test_hook_patch_injects_dynamic_hook_disable_and_call_hook_stub(self) -> None:
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

        pre_call_hook = _slice_block(merged, "    def _call_hook(", "\n    def _call_hook1(")
        post_call_hook = _slice_block(patched, "    def _call_hook(", "\n    def _call_hook1(")
        self.assertNotEqual(post_call_hook, pre_call_hook)
        self.assertIn("selfhost 互換: dynamic hooks は無効化済みなので常に未処理を返す。", post_call_hook)
        self.assertIn("return None", post_call_hook)
        self.assertNotIn("fn = self._lookup_hook(name)", post_call_hook)
        self.assertNotIn("pass", post_call_hook)

        self.assertIn("self.init_base_state(", patched)
        self.assertIn("self.set_dynamic_hooks_enabled(False)", patched)

        hook_emit_stmt_block = _slice_block(patched, "    def hook_on_emit_stmt(", "\n    def hook_on_emit_stmt_kind(")
        self.assertIn("v = self._call_hook1(", hook_emit_stmt_block)
        self.assertIn("if isinstance(v, bool):", hook_emit_stmt_block)
        self.assertNotIn("pass", hook_emit_stmt_block)

    def test_hook_patch_raises_when_markers_missing(self) -> None:
        mod = _load_prepare_module()
        with self.assertRaisesRegex(RuntimeError, "_call_hook"):
            mod._patch_code_emitter_hooks_for_selfhost("class CodeEmitter:\n    pass\n")

        broken_order = (
            "class CodeEmitter:\n"
            "    def _call_hook(\n"
            "        self,\n"
            "        name: str,\n"
            "    ) -> object:\n"
            "        return None\n"
            "    def _call_hook1(self, name: str, arg0: object) -> object:\n"
            "        return None\n"
            "class CppEmitter(CodeEmitter):\n"
            "    def __init__(self):\n"
            "        pass\n"
        )
        with self.assertRaisesRegex(RuntimeError, "init_base_state call"):
            mod._patch_code_emitter_hooks_for_selfhost(broken_order)

    def test_generated_cpp_core_uses_helpers_for_module_and_class_root_nodes(self) -> None:
        text = GENERATED_CPP_CORE.read_text(encoding="utf-8")
        self.assertIn("dict<str, object> _sh_make_import_stmt(", text)
        self.assertIn("dict<str, object> _sh_make_import_from_stmt(", text)
        self.assertIn("dict<str, object> _sh_make_function_def_stmt(", text)
        self.assertIn("dict<str, object> _sh_make_class_def_stmt(", text)
        self.assertIn("dict<str, object> _sh_make_assign_stmt(", text)
        self.assertIn("dict<str, object> _sh_make_ann_assign_stmt(", text)
        self.assertIn("dict<str, object> _sh_make_attribute_expr(", text)
        self.assertIn("dict<str, object> _sh_make_call_expr(", text)
        self.assertIn("dict<str, object> _sh_make_binop_expr(", text)
        self.assertIn("dict<str, object> _sh_make_unaryop_expr(", text)
        self.assertIn("dict<str, object> _sh_make_boolop_expr(", text)
        self.assertIn("dict<str, object> _sh_make_compare_expr(", text)
        self.assertIn("dict<str, object> _sh_make_ifexp_expr(", text)
        self.assertIn("dict<str, object> _sh_make_arg_node(", text)
        self.assertIn("dict<str, object> _sh_make_lambda_arg_entry(", text)
        self.assertIn("dict<str, object> _sh_make_lambda_expr(", text)
        self.assertIn("dict<str, object> _sh_make_formatted_value_node(", text)
        self.assertIn("dict<str, object> _sh_make_joined_str_expr(", text)
        self.assertIn("dict<str, object> _sh_make_keyword_arg(", text)
        self.assertIn("dict<str, object> _sh_make_cast_entry(", text)
        self.assertIn("dict<str, object> _sh_make_constant_expr(", text)
        self.assertIn("dict<str, object> _sh_make_if_stmt(", text)
        self.assertIn("dict<str, object> _sh_make_for_stmt(", text)
        self.assertIn("dict<str, object> _sh_make_for_range_stmt(", text)
        self.assertIn("dict<str, object> _sh_make_range_expr(", text)
        self.assertNotIn('dict<str, object> item = dict<str, object>{{"kind", make_object("FunctionDef")}', text)
        self.assertNotIn('dict<str, object> cls_item = dict<str, object>{{"kind", make_object("ClassDef")}', text)
        self.assertNotIn('body_items.append(dict<str, object>(dict<str, object>{{"kind", make_object("Import")}', text)
        self.assertNotIn('body_items.append(dict<str, object>(dict<str, object>{{"kind", make_object("ImportFrom")}', text)
        self.assertNotIn('node = dict<str, object>{{"kind", make_object("Attribute")}', text)
        self.assertNotIn('dict<str, object> payload = dict<str, object>{{"kind", make_object("Call")}', text)
        self.assertNotIn('return dict<str, object>{{"kind", make_object("BinOp")}', text)
        self.assertNotIn('return dict<str, object>{{"kind", make_object("Lambda")}', text)
        self.assertNotIn('return dict<str, object>{{"kind", make_object("IfExp")}', text)
        self.assertNotIn('return dict<str, object>{{"kind", make_object("BoolOp")}', text)
        self.assertNotIn('return dict<str, object>{{"kind", make_object("UnaryOp")}', text)
        self.assertNotIn('return dict<str, object>{{"kind", make_object("Compare")}', text)
        self.assertNotIn('dict<str, object> fv = dict<str, object>{{"kind", make_object("FormattedValue")}', text)
        self.assertNotIn('values.append(dict<str, object>(dict<str, object>{{"kind", make_object("FormattedValue")}', text)
        self.assertNotIn('return dict<str, object>{{"kind", make_object("JoinedStr")}', text)
        self.assertNotIn('dict<str, object> elif_item = dict<str, object>{{"kind", make_object("If")}', text)
        self.assertNotIn('pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("If")}', text)
        self.assertNotIn('pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("ForRange")}', text)
        self.assertNotIn('pending_blank_count = _sh_push_stmt_with_trivia(stmts, pending_leading_trivia, pending_blank_count, dict<str, object>{{"kind", make_object("For")}', text)
        self.assertNotIn('iter_expr = dict<str, object>{{"kind", make_object("RangeExpr")}', text)
        self.assertNotIn('iter_node = dict<str, object>{{"kind", make_object("RangeExpr")}', text)
        self.assertNotIn('keywords.append(dict<str, object>(dict<str, object>{{"arg", make_object(py_to_string(py_dict_get(name_tok, py_to_string("v"))))}, {"value", make_object(kw_val)}}))', text)
        self.assertNotIn('casts.append(dict<str, object>(dict<str, str>{{"on", "left"}, {"from", "int64"}, {"to", "float64"}, {"reason", "numeric_promotion"}}))', text)
        self.assertNotIn('casts.append(dict<str, object>(dict<str, str>{{"on", "right"}, {"from", "int64"}, {"to", "float64"}, {"reason", "numeric_promotion"}}))', text)


if __name__ == "__main__":
    unittest.main()
