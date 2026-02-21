# TODO（未完了）

<a href="../docs/todo.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


最終更新: 2026-02-21

## P1: CodeEmitter / Hooks 移管

1. [x] フック注入 (`EmitterHooks`) を実装する。
   - [x] `CodeEmitter` 共通モジュールに `EmitterHooks` コンテナを追加した。
   - [x] `build_cpp_hooks()` を `EmitterHooks` 経由の組み立てへ移行した（最終出力は従来どおり dict）。
2. [x] `render_expr(Call/BinOp/Compare)` の巨大分岐を hooks + helper へ段階分離する。
   - [x] `BinOp` の C++ 固有分岐（`Div/FloorDiv/Mod/Mult`）を `cpp_hooks.on_render_binop` へ抽出した（selfhost 互換のため `py2cpp.py` に同等フォールバックを残置）。
   - [x] `module.attr` の runtime 解決ロジックを `CppEmitter._lookup_module_attr_runtime_call` へ一本化し、`py2cpp.py` / `cpp_hooks.py` の重複分岐を削減した。
   - [x] `Compare(lowered_kind=Contains)` の C++ 固有分岐を `cpp_hooks.on_render_expr_kind(kind=Compare)` へ抽出した（selfhost 互換のため `py2cpp.py` 側フォールバックは残置）。
   - [x] `Call(Attribute)` の object-method 特殊処理フォールバック（`_render_call_object_method`）を削除し、hook 優先の経路へ一本化した。
   - [x] `Call(Attribute)` の class-method 分岐に hook（`on_render_class_method`）を追加し、`_render_call_attribute` から hook 優先で描画できる導線を追加した（selfhost 互換のため `py2cpp.py` 側フォールバックは維持）。
3. [ ] profile で表現しにくいケースのみ hooks 側へ寄せる（`py2cpp.py` に条件分岐を残さない）。

## P1: py2cpp 縮退（行数削減）

1. [x] `src/py2cpp.py` の未移行ロジックを `CodeEmitter` 側へ移し、行数を段階的に削減する。
   - [x] `args + kw` 結合ロジックを `CodeEmitter.merge_call_args` へ移管し、`py2cpp.py` 側の重複実装を削除した。
   - [x] `list[dict]` 抽出ヘルパ（`_dict_stmt_list`）を `CodeEmitter` 側へ移管し、`py2cpp.py` 側の重複実装を削除した。
   - [x] `Call` 前処理（`_prepare_call_parts`）を `CodeEmitter` 側へ移管し、selfhost-safe 化した（互換維持のため `py2cpp.py` 側フォールバックは残置）。
   - [x] `IfExp` 共通レンダ（`_render_ifexp_expr`）と定数解析ヘルパ（`_one_char_str_const`, `_const_int_literal`）を `CodeEmitter` 側へ移管した。
   - [x] `BinOp` の優先順位/括弧補完ヘルパ（`_binop_precedence`, `_wrap_for_binop_operand`）を `CodeEmitter` 側へ移管した。
   - [x] 文字列探索/末尾セグメント抽出ヘルパ（`_contains_text`, `_last_dotted_name`）を `CodeEmitter` 側へ移管した。
   - [x] 最適化レベル判定ヘルパ（`_opt_ge`）を `CodeEmitter` 側へ移管した。
   - [x] import 解決ヘルパ（`_resolve_imported_module_name`, `_resolve_imported_symbol`）を `CodeEmitter` 側へ移管した。
   - [x] 上記 import 解決ヘルパは selfhost-safe 化（`__dict__` 非依存・型付き dict 直接参照）を完了した。
   - [x] import 解決ヘルパに `meta` 由来フォールバックを追加し、selfhost で `from X import Y` 由来の `Y.attr(...)` が未解決になる差分を解消した（`tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で `mismatches=0`）。
   - [x] 実行時キャスト対象判定（`_can_runtime_cast_target`）を `CodeEmitter` 側へ移管した。
   - [x] `std::` runtime 判定ヘルパ（`_is_std_runtime_call`）を `CodeEmitter` 側へ移管した。
   - [x] call/attribute 周辺の `module.attr` runtime lookup を helper 化し、`render_call`/`render_attribute`/hooks から共通利用するよう整理した。
   - [x] `obj.append(...)` の C++ 固有型変換分岐を `_render_append_call_object_method` へ分離し、`_render_call_object_method` 本体を縮退した。
   - [x] Attribute owner の `kind/type/module/attr` 解決を `CodeEmitter` helper（`resolve_attribute_owner_context` / `resolve_attribute_owner_type` / `attr_name`）へ移管し、`_render_call_attribute` / `_render_attribute_expr` の重複ロジックを削減した（selfhost の静的束縛回避のため `owner_expr` は呼び出し側で先に描画して渡す形にした）。
   - [x] `Call(Attribute)` 前処理 helper（`resolve_call_attribute_context`）を `CodeEmitter` 側へ移管し、`py2cpp.py` の `_resolve_call_attribute_context` を削除した。
   - [x] Any boxing 判定 helper（`is_boxed_object_expr`）を `CodeEmitter` 側へ移管し、`py2cpp.py` 側の重複実装（`_is_boxed_object_expr`）を削除した。
   - [x] 描画済み引数の型補完 helper（`infer_rendered_arg_type`）を `CodeEmitter` 側へ移管し、`py2cpp.py` 側の重複実装（`_infer_rendered_arg_type`）を削除した。
   - [x] `Call(Name)` の `set/list/dict` コンストラクタ分岐と `int/float/bool` キャスト分岐を helper（`_render_collection_constructor_call` / `_render_scalar_cast_builtin_call`）へ切り出し、`_render_call_name_or_attr` 本体の重複を削減した。
   - [x] `Call(Name)` の `print/len/reversed/enumerate/any/all/isinstance` 分岐を helper（`_render_simple_name_builtin_call` / `_render_isinstance_name_call`）へ切り出し、`_render_call_name_or_attr` の条件分岐を縮退した。
   - [x] `Class.method(...)` 分岐を `_render_call_class_method` として切り出し、`_render_call_attribute` の class-method 経路を分離した。
   - [x] `_render_builtin_call` の owner 付き runtime 分岐（`exists/replace/startswith...` と共通 `py_/std` 呼び出し）を helper（`_render_builtin_call_owner_expr` / `_render_builtin_call_owner_runtime`）へ分離した。
   - [x] `_render_builtin_call` の `runtime_call=static_cast` 分岐を helper（`_render_builtin_static_cast_call`）へ分離し、本体の条件分岐を削減した。
   - [x] `_render_builtin_call` の `runtime_call=py_join` 分岐を helper（`_render_builtin_join_call`）へ分離し、owner 再解決ロジックを削除した。
   - [x] `_render_builtin_call` の runtime 分岐（`py_print/py_len/py_to_string/...`）を helper（`_render_builtin_runtime_fallback`）へ抽出し、本体を dispatch + constructor 分岐へ縮退した。
   - [x] `Call(Name)` の import 解決 + runtime/namespace 呼び出し分岐を helper（`_resolve_or_render_imported_symbol_name_call`）へ分離し、`_render_call_name_or_attr` 本体の分岐を削減した。
   - [x] `Call(Name)` の残りビルトイン分岐（`bytes/bytearray/str/int(base)/ord/chr/min/max/perf_counter/Path/Exception`）を helper（`_render_misc_name_builtin_call`）へ分離した。
   - [x] `_render_call_fallback` の `*.append` 分岐を helper（`_render_append_fallback_call`）へ分離し、`_render_append_call_object_method` と型変換ロジックを共通化した。
   - [x] `Call(Attribute)` owner 解決前処理（owner/module/type/attr）を helper（`_resolve_call_attribute_context`）へ分離し、`_render_call_attribute` 本体を縮退した。
   - [x] `Call(Attribute)` の object-method 分岐に hook（`on_render_object_method`）を追加し、`_render_call_attribute` から hook 優先で描画できるようにした（`_render_call_object_method` フォールバックは削除済み）。
   - [x] `Call(Attribute)` の class-method 分岐に hook（`on_render_class_method`）を追加し、`cpp_hooks.py` 側に C++ 固有の class-method レンダ経路を分離した（`py2cpp.py` 側フォールバックは selfhost 互換のため維持）。
   - [x] `Call(Attribute)` の module-method 分岐に hook（`on_render_module_method`）を追加し、`_render_call_module_method` は hook 優先 + 最小フォールバック（namespace 解決のみ）へ縮退した。
   - [x] `Call(Attribute)` の C++ 固有 object-method 分岐を `cpp_hooks.py` 側へ集約し、`py2cpp.py` から文字列系専用 helper（`_render_string_object_method`）を削除した。
   - [x] `BuiltinCall` の direct runtime 分岐（`py_print/py_len/py_to_string/py_min|max/perf_counter/open/py_join/...`）を `cpp_hooks.on_render_call` へ追加し、`py2cpp.py` 側は selfhost（hooks stub）向けフォールバックとして維持した。
   - [x] `BuiltinCall(runtime_call=static_cast)` の C++ 固有分岐を `cpp_hooks.on_render_call` 側へ追加し、通常経路を hook 優先へ移行した（`py2cpp.py` 側フォールバックは selfhost 互換のため維持）。
   - [x] `module.method(...)` namespace 解決 helper の `CodeEmitter` 移管を検証し、selfhost C++ の静的束縛で派生専用メソッド呼び出しが崩れることを確認したため、共通化は見送り（`py2cpp.py` / `cpp_hooks.py` 側の局所実装を維持）とした。
   - [x] 引数型強制の重複ロジック（`_coerce_args_for_known_function` / `_coerce_args_for_class_method`）を `_coerce_args_by_signature` へ統合し、`Call` 系分岐の重複を削減した。
   - [x] `isinstance` 変換の型マップ分岐（`Call(Name)` / fallback）を `_render_isinstance_type_check` へ統合し、`Call` 分岐の重複を削減した。
   - [x] `module.method(...)` の namespace 呼び出し重複を `_render_call_module_method_with_namespace` へ統合し、`_render_call_module_method` の重複分岐を削減した。
   - [x] `Call(Attribute)` の object/class 分岐を `_render_call_attribute_non_module` へ切り出し、`_render_call_attribute` 本体を module 解決 + dispatch へ縮退した。
   - [x] `from-import` 解決と `module.method(...)` の namespace 呼び出しを `_render_namespaced_module_call` へ統合し、call/attribute 周辺の重複分岐を追加削減した。
   - [x] `Attribute` 式の self/class/module 基本分岐を `CodeEmitter` helper（`render_attribute_self_or_class_access` / `render_attribute_module_access`）へ抽出し、`py2cpp.py` と `cpp_hooks.py` の重複を追加削減した。
   - [x] `cpp_hooks.on_render_module_method` でも `CppEmitter._render_namespaced_module_call` を優先利用し、hooks 側の namespace 分岐重複を削減した。
   - [x] call/attribute 周辺の C++ 固有分岐を helper/hook 化し、`py2cpp.py` 本体と `cpp_hooks.py` の重複分岐を段階的に削減した（残課題は profile 化 / 共通ディスパッチ再設計へ移管）。
2. [x] `render_expr` の `Call` 分岐（builtin/module/method）を機能単位に分割し、`CodeEmitter` helper へ移す。
   - [x] `call_parts` 展開処理（`fn/fn_name/args/kw/first_arg`）を `CodeEmitter.unpack_prepared_call_parts` へ移管した。
   - [x] object レシーバ禁止検証を `CodeEmitter.validate_call_receiver_or_raise` へ移管し、`py2cpp.py` 側の `Call(Attribute)` 直書き分岐を削減した。
   - [x] `render_expr(Call)` 本体を `_render_call_expr_from_context` へ分離し、hook/builtin/name-or-attr/fallback の段階処理を独立関数化した。
   - [x] `render_expr(Call)` 末尾の `kw_values/kw_nodes` マージ処理を `_merge_call_kw_values` / `_merge_call_arg_nodes` へ分離した。
   - [x] 上記 helper を `CodeEmitter.merge_call_kw_values` / `CodeEmitter.merge_call_arg_nodes` へ移管した。
   - [x] `render_expr(Call)` の `Call(Name)` import 経路を `_resolve_or_render_imported_symbol_name_call` へ抽出し、段階処理（import解決→ビルトイン→fallback）を明確化した。
3. [x] `render_expr` の算術/比較/型変換分岐を独立関数へ分割し、profile/hook 経由で切替可能にする。
   - [x] `RangeExpr/BinOp/UnaryOp/BoolOp/Compare/IfExp` の分岐を `_render_operator_family_expr` へ集約し、`render_expr` 本体の分岐を削減した。
   - [x] `RangeExpr` の C++ レンダ（`py_range(...)`）を `cpp_hooks.on_render_expr_kind(kind=RangeExpr)` へ抽出した（`py2cpp.py` 側フォールバックは残置）。
4. [x] `Constant(Name/Attribute)` の基本レンダを `CodeEmitter` 共通へ移す。
   - [x] `Name` の基本レンダ（予約語回避 + `self` 置換）を `CodeEmitter.render_name_expr_common` へ移管した。
   - [x] `Constant` の非文字列系レンダ（`bool`/`None`/数値）を `CodeEmitter.render_constant_non_string_common` へ移管した。
   - [x] selfhost C++ での bool 判定崩れを避けるため、`render_constant_non_string_common` は handled フラグを `"0"/"1"` 文字列で返す方式へ調整した。
   - [x] `Attribute` の基本レンダ（self/class/module）の共通 helper 化を実施した（`resolve_*` + `render_attribute_*` を利用）。
5. [x] `emit_stmt` の制御構文分岐をテンプレート化して `CodeEmitter.syntax_*` へ寄せる。
   - [x] `try/catch/finally(scope guard)` の開始行（`scope_open` / `scope_exit_open` / `try_open` / `catch_open`）を `syntax.json` + `syntax_line` 経由へ移管した。
   - [x] `for` ブロック開始行（`hdr + " {"`）を `for_open_block` テンプレートへ移管した。
   - [x] `pass/break/continue` の文生成を `syntax.json`（`pass_stmt` / `break_stmt` / `continue_stmt`）経由へ移管した。
   - [x] `swap` / `raise` の文生成を `syntax.json`（`swap_stmt` / `raise_default` / `raise_expr`）経由へ移管した。
   - [x] `Expr` / `Return` の文生成を `syntax.json`（`expr_stmt` / `return_void` / `return_value`）経由へ移管した。
   - [x] `Function/Class/Block` open/close 出力（`emit_function_open` / `emit_ctor_open` / `emit_dtor_open` / `emit_class_open` / `emit_class_close` / `emit_block_close`）を `syntax_line` / `syntax_text` 経由へ統一した。
6. [x] C++ 固有差分（brace省略や range-mode）だけ hook 側で上書きする。
   - [x] object-method（`strip/lstrip/rstrip/startswith/endswith/replace/find/rfind/...`）の C++ 固有分岐用 hook（`cpp_hooks.on_render_object_method`）を追加し、段階的に `py2cpp.py` 本体から分離する導線を作成した。
   - [x] object-method hook に `clear` / `append` 経路を追加し、`py2cpp.py` 側フォールバック依存を追加で縮退した（selfhost 互換のためフォールバックは残置）。
   - [x] module-method（`module.func(...)` 解決）の C++ 固有分岐用 hook（`cpp_hooks.on_render_module_method`）を追加し、段階的に `py2cpp.py` 本体から分離する導線を作成した。
7. [x] `FunctionDef` / `ClassDef` の共通テンプレート（open/body/close）を `CodeEmitter` 側に寄せる。
   - [x] `Function/Class` のヘッダ/終端出力を `syntax_line` / `syntax_text` へ寄せ、文字列直書き依存を削減した（selfhost互換のため呼び出しは `CppEmitter` 側ラッパで維持）。
   - [x] `_cpp_expr_to_module_name` を `CodeEmitter` 側へ移管し、hook 実装から共通 helper を参照する形に統一した。
8. [x] 未使用関数の掃除を継続する（詳細タスクは最優先側へ移動しながら管理）。
   - [x] 未再利用 helper `_dict_any_get_list` を削除し、`_dict_any_get_str_list` へ内包した。
   - [x] 単発 helper `_dict_str_list_get` を削除し、`_graph_cycle_dfs` 側へ内包した。
   - [x] `src/py2cpp.py` / `src/pytra/compiler/east_parts/code_emitter.py` について repo 全体参照を監査し、単独未参照シンボルがないことを確認した（現時点の明確な削除候補なし）。
9. [ ] `CodeEmitter` 側の共通ディスパッチを再設計する（selfhost C++ の静的束縛制約を回避）。
   - [ ] 非 virtual 前提でも派生レンダへ到達できる hook 注入ベースの経路を設計し、`render_expr` / `emit_stmt` の段階的置換計画を作成する。

## P2: Any/object 境界の整理

1. [x] `CodeEmitter` の `Any/dict` 境界を selfhost で崩れない実装へ段階移行する。
   - [x] `CppEmitter._render_call_attribute` の module/object 呼び出し中間値を branch-local 化し、selfhost 生成 C++ で `object` へ退避しない形に修正した。
   - [x] 上記修正後も `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で `mismatches=0` を確認した。
   - [x] `dict[str, str]` 変換ヘルパ（`CodeEmitter.any_to_str_dict_or_empty`）を追加し、`render_expr(Call)` の `kw` 展開で共通利用するようにした。
   - [x] `is_boxed_object_expr` / `infer_rendered_arg_type` を `CodeEmitter` 側へ移管し、Any/object 境界ロジックを基底へ集約した。
2. [x] `cpp_type` と式レンダリングで `object` 退避を最小化する。
   - [x] モジュール関数引数の boxing 判定で、`arg_node` 側型が unknown の場合に描画済み式（例: `x`, `(x)`）から `declared_var_types` を参照して型補完する helper（`_infer_rendered_arg_type`）を追加し、不要な `make_object(...)` を抑制した。
3. [x] `Any -> object` が必要な経路と不要な経路を分離し、`make_object(...)` の過剰挿入を減らす。
   - [x] Any/object 向け boxing 判定を `_box_expr_for_any` へ集約し、`List`/`Dict` リテラル生成で「既に object/Any の式」を二重に `make_object(...)` しないようにした。
   - [x] `Constant(None)` の Any/object 経路を `make_object(1)` から `object{}` へ修正し、`None` の表現を統一した。
   - [x] boxing 済み判定 helper（`_is_boxed_object_expr`）を追加し、`_coerce_args_for_module_function` / `_coerce_py_assert_args` / Assign/AnnAssign / dict key coercion で `object{}` の再 boxing を抑止した。
   - [x] `py_assert_*` の object 引数 boxing をノード型付き（`arg_nodes`）で判定し、`object/Any` 引数への不要な `make_object(...)` を回避した。
4. [x] `py_dict_get_default` / `dict_get_node` の既定値引数が `object` 必須になる箇所を整理する。
   - [x] `dict.get` の object 系 owner 経路で、`resolved_type` または既定値型が数値（int/float）なら `dict_get_int` / `dict_get_float` を優先し、`py_dict_get_default`/`dict_get_node` の汎用 object 経路を減らした。
5. [x] `py2cpp.py` で `nullopt` を default 値に渡している箇所を洗い出し、型ごとの既定値へ置換する。
   - [x] 関数引数既定値（`_render_param_default_expr` / `_header_render_default_expr`）で `None` を一律 `::std::nullopt` にしていた処理を型別既定値へ変更した（`int -> 0`, `float -> 0.0`, `str -> str()`, `Any/object -> object{}` など）。
   - [x] 既存 optional 型（`optional[...]` / `| None`）は `::std::nullopt` を維持するようにした。
6. [x] `std::any` を経由する経路（selfhost 変換由来）をログベースでリスト化し、順次削除する。
   - [x] `unknown` / 混在 `Union` / `list[unknown]` / `dict[..., unknown]` の既定マッピングを `::std::any` から `object` 系へ寄せた（`_cpp_type_text`）。
   - [x] `render_minmax` / 内包表現の動的型判定で `std::any` 依存判定を削減し、`object`/`auto` 判定へ寄せた。
7. [x] 上位3関数ごとにパッチを分けて改善し、毎回 `check_py2cpp_transpile.py` を通す。
   - [x] 直近の `py2cpp.py`/`code_emitter.py` リファクタ（引数強制統合・isinstance統合・module call helper 化）で、各ステップごとに `test/unit/test_py2cpp_codegen_issues.py` / `tools/check_py2cpp_transpile.py` / `tools/build_selfhost.py` / `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` を実行して回帰なしを確認した。

## P3: 低優先（可読性・Pythonらしさの回復）

1. [x] `src/py2cpp.py` の selfhost 都合で平易化している実装を棚卸しし、一般的な Python 風の書き方へ戻す候補一覧を作る。
   - [x] 候補一覧を `docs-jp/pythonic-backlog.md` に作成した。
2. [x] `src/pytra/compiler/east_parts/code_emitter.py` で同様に平易化されている箇所を段階的に Python らしい記述へ戻す。
   - [x] `merge_call_args` / `merge_call_kw_values` / `merge_call_arg_nodes` の冗長な while ループ実装を、`list(...)` + `for` ベースの簡潔な実装へ置換した（`dict` 直接反復は selfhost 崩れのため `kw.items()` 経由で keys を収集）。
   - [x] `unpack_prepared_call_parts` の `args/kw_values` 変換ループを index `while` から `for` へ置換し、selfhost 差分を保ったまま可読性を改善した。
   - [x] `normalize_type_name` / `_resolve_imported_symbol` / `_prepare_call_parts` の単純走査ループを `for` ベースへ置換し、selfhost 差分を維持したまま冗長な index 管理を削減した。
   - [x] `_strip_outer_parens` の前後空白トリムを `_trim_ws` 共通化し、`_trim_ws` 実装を `text.strip()` へ簡潔化した（同時に `is_declared` の逆走査も `range(..., -1, -1)` 形式へ置換した）。
   - [x] `_strip_outer_parens` の字句走査と `_last_dotted_name` の末尾要素抽出を `enumerate` ベースへ置換し、インデックス手動更新を削減した。
3. [x] `sample/` のコードについても、selfhost 都合の書き方が残っている箇所を通常の Python らしい表現へ順次戻す。
   - [x] `sample/py/15_mini_language_interpreter.py` の `tokenize()` で、行走査を index `while` から `enumerate` ベースの `for` へ置換した。
   - [x] `sample/py/15_mini_language_interpreter.py` の `parse_add()` / `parse_mul()` で、`done` フラグ式ループを `while True ... break` へ置換した。
   - [x] `sample/py/09_fire_simulation.py` / `sample/py/10_plasma_effect.py` のフレーム書き込みで、手動インデックス加算（`i += 1`）を `row_base + x` 形式へ置換した。
   - [x] `sample/py/08_langtons_ant.py` / `sample/py/14_raymarching_light_cycle.py` / `sample/py/16_glass_sculpture_chaos.py` のフレーム書き込みで、手動インデックス加算（`i += 1`）を `row_base + x` 形式へ置換した。
   - [x] `sample/py/08_langtons_ant.py` のグリッド初期化を二重 `for` からリスト内包表記（`[[0] * w for _ in range(h)]`）へ置換した。
   - [x] `sample/py/15_mini_language_interpreter.py` の `new_expr_nodes()` で空 list 生成を簡潔化した。
   - [x] `sample/py/07_game_of_life_loop.py` のグリッド初期化を二重 `for` からリスト内包表記（`[[0] * w for _ in range(h)]`）へ置換した。
   - [x] `sample/py/05_mandelbrot_zoom.py` / `sample/py/06_julia_parameter_sweep.py` のフレーム書き込みで、手動インデックス加算（`idx += 1`）を `row_base + x` 形式へ置換した。
4. [x] 上記の戻し作業は低優先で進め、各ステップで `tools/build_selfhost.py` と `tools/check_py2cpp_transpile.py` を通して回帰を防ぐ。

## 補助メモ

- 完了済みタスクと過去ログは `docs-jp/todo-old.md` に移管済み。
- 今後 `docs-jp/todo.md` は未完了タスクのみを保持する。
