// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/compiler/east_parts/core.py
// generated-by: src/py2cpp.py

#ifndef PYTRA_COMPILER_EAST_PARTS_CORE_H
#define PYTRA_COMPILER_EAST_PARTS_CORE_H

#include <tuple>
#include <optional>

namespace pytra::compiler::east_parts::core {

struct EastBuildError;
struct _ShExprParser;

extern set<str> INT_TYPES;
extern set<str> FLOAT_TYPES;
extern set<str> _SH_STR_PREFIX_CHARS;
extern dict<str, str> _SH_FN_RETURNS;
extern dict<str, dict<str, str>> _SH_CLASS_METHOD_RETURNS;
extern dict<str, ::std::optional<str>> _SH_CLASS_BASE;
extern dict<str, object> _SH_EMPTY_SPAN;

void _sh_set_parse_context(const dict<str, str>& fn_returns, const dict<str, dict<str, str>>& class_method_returns, const dict<str, ::std::optional<str>>& class_base);
rc<EastBuildError> _make_east_build_error(const str& kind, const str& message, const dict<str, object>& source_span, const str& hint);
dict<str, object> convert_source_to_east(const str& source, const str& filename);
dict<str, int64> _sh_span(int64 line, int64 col, int64 end_col);
str _sh_ann_to_type(const str& ann);
list<::std::tuple<str, int64>> _sh_split_args_with_offsets(const str& arg_text);
int64 _sh_scan_string_token(const str& text, int64 start, int64 quote_pos, int64 line_no, int64 col_base);
str _sh_decode_py_string_body(const str& text, bool raw_mode);
void _sh_append_fstring_literal(const list<dict<str, object>>& values, const str& segment, const dict<str, int64>& span, bool raw_mode);
::std::optional<dict<str, object>> _sh_parse_def_sig(int64 ln_no, const str& ln, const str& in_class);
::std::tuple<int64, str> _sh_scan_logical_line_state(const str& txt, int64 depth, const str& mode);
::std::tuple<list<::std::tuple<int64, str>>, dict<int64, ::std::tuple<int64, int64>>> _sh_merge_logical_lines(const list<::std::tuple<int64, str>>& raw_lines);
list<str> _sh_split_top_commas(const str& txt);
int64 _sh_split_top_keyword(const str& text, const str& kw);
list<str> _sh_split_top_plus(const str& text);
str _sh_infer_item_type(const dict<str, object>& node);
dict<str, str> _sh_bind_comp_target_types(const dict<str, str>& base_types, const dict<str, object>& target_node, const dict<str, object>& iter_node);
dict<str, int64> _sh_block_end_span(const list<::std::tuple<int64, str>>& body_lines, int64 start_ln, int64 start_col, int64 fallback_end_col, int64 end_idx_exclusive);
dict<str, int64> _sh_stmt_span(const dict<int64, ::std::tuple<int64, int64>>& merged_line_end, int64 start_ln, int64 start_col, int64 fallback_end_col);
int64 _sh_push_stmt_with_trivia(const list<dict<str, object>>& stmts, const list<dict<str, object>>& pending_leading_trivia, int64 pending_blank_count, const dict<str, object>& stmt);
::std::tuple<list<::std::tuple<int64, str>>, int64> _sh_collect_indented_block(const list<::std::tuple<int64, str>>& body_lines, int64 start, int64 parent_indent);
::std::optional<::std::tuple<str, str>> _sh_split_top_level_assign(const str& text);
str _sh_strip_inline_comment(const str& text);
::std::optional<::std::tuple<str, str>> _sh_split_top_level_from(const str& text);
::std::tuple<list<dict<str, object>>, int64> _sh_parse_if_tail(int64 start_idx, int64 parent_indent, const list<::std::tuple<int64, str>>& body_lines, const dict<str, str>& name_types, const str& scope_label);
::std::tuple<::std::optional<str>, list<dict<str, object>>> _sh_extract_leading_docstring(const list<dict<str, object>>& stmts);
void _sh_append_import_binding(const list<dict<str, object>>& import_bindings, const set<str>& import_binding_names, const str& module_id, const str& export_name, const str& local_name, const str& binding_kind, const str& source_file, int64 source_line);
dict<str, object> _sh_parse_expr(const str& text, int64 line_no, int64 col_base, const dict<str, str>& name_types, const dict<str, str>& fn_return_types, const dict<str, dict<str, str>>& class_method_return_types, const dict<str, ::std::optional<str>>& class_base);
dict<str, object> _sh_parse_expr_lowered(const str& expr_txt, int64 ln_no, int64 col, const dict<str, str>& name_types);
list<dict<str, object>> _sh_parse_stmt_block(const list<::std::tuple<int64, str>>& body_lines, const dict<str, str>& name_types, const str& scope_label);
dict<str, object> convert_source_to_east_self_hosted(const str& source, const str& filename);
dict<str, object> convert_source_to_east_with_backend(const str& source, const str& filename, const str& parser_backend);
dict<str, object> convert_path(const Path& input_path, const str& parser_backend);

}  // namespace pytra::compiler::east_parts::core

#endif  // PYTRA_COMPILER_EAST_PARTS_CORE_H
