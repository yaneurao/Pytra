# TODO（未完了）

<a href="../docs/todo.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


最終更新: 2026-02-21

## P1: CodeEmitter / Hooks 移管

1. [x] フック注入 (`EmitterHooks`) を実装する。
   - [x] `CodeEmitter` 共通モジュールに `EmitterHooks` コンテナを追加した。
   - [x] `build_cpp_hooks()` を `EmitterHooks` 経由の組み立てへ移行した（最終出力は従来どおり dict）。
2. [ ] `render_expr(Call/BinOp/Compare)` の巨大分岐を hooks + helper へ段階分離する。
   - [x] `BinOp` の C++ 固有分岐（`Div/FloorDiv/Mod/Mult`）を `cpp_hooks.on_render_binop` へ抽出した（selfhost 互換のため `py2cpp.py` に同等フォールバックを残置）。
   - [x] `module.attr` の runtime 解決ロジックを `CppEmitter._lookup_module_attr_runtime_call` へ一本化し、`py2cpp.py` / `cpp_hooks.py` の重複分岐を削減した。
3. [ ] profile で表現しにくいケースのみ hooks 側へ寄せる（`py2cpp.py` に条件分岐を残さない）。

## P1: py2cpp 縮退（行数削減）

1. [ ] `src/py2cpp.py` の未移行ロジックを `CodeEmitter` 側へ移し、行数を段階的に削減する。
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
   - [x] `Call(Name)` の `set/list/dict` コンストラクタ分岐と `int/float/bool` キャスト分岐を helper（`_render_collection_constructor_call` / `_render_scalar_cast_builtin_call`）へ切り出し、`_render_call_name_or_attr` 本体の重複を削減した。
   - [x] `Call(Name)` の `print/len/reversed/enumerate/any/all/isinstance` 分岐を helper（`_render_simple_name_builtin_call` / `_render_isinstance_name_call`）へ切り出し、`_render_call_name_or_attr` の条件分岐を縮退した。
   - [x] `Class.method(...)` 分岐を `_render_call_class_method` として切り出し、`_render_call_attribute` の class-method 経路を分離した。
   - [x] `_render_builtin_call` の owner 付き runtime 分岐（`exists/replace/startswith...` と共通 `py_/std` 呼び出し）を helper（`_render_builtin_call_owner_expr` / `_render_builtin_call_owner_runtime`）へ分離した。
   - [x] `_render_builtin_call` の `runtime_call=static_cast` 分岐を helper（`_render_builtin_static_cast_call`）へ分離し、本体の条件分岐を削減した。
   - [x] `_render_builtin_call` の `runtime_call=py_join` 分岐を helper（`_render_builtin_join_call`）へ分離し、owner 再解決ロジックを削除した。
   - [x] `Call(Name)` の import 解決 + runtime/namespace 呼び出し分岐を helper（`_resolve_or_render_imported_symbol_name_call`）へ分離し、`_render_call_name_or_attr` 本体の分岐を削減した。
   - [x] `Call(Name)` の残りビルトイン分岐（`bytes/bytearray/str/int(base)/ord/chr/min/max/perf_counter/Path/Exception`）を helper（`_render_misc_name_builtin_call`）へ分離した。
   - [x] `_render_call_fallback` の `*.append` 分岐を helper（`_render_append_fallback_call`）へ分離し、`_render_append_call_object_method` と型変換ロジックを共通化した。
   - [x] `Call(Attribute)` owner 解決前処理（owner/module/type/attr）を helper（`_resolve_call_attribute_context`）へ分離し、`_render_call_attribute` 本体を縮退した。
   - [ ] call/attribute 周辺の C++ 固有分岐をさらに helper/hook 化して `py2cpp.py` 本体行数を削減する。
2. [ ] `render_expr` の `Call` 分岐（builtin/module/method）を機能単位に分割し、`CodeEmitter` helper へ移す。
   - [x] `call_parts` 展開処理（`fn/fn_name/args/kw/first_arg`）を `CodeEmitter.unpack_prepared_call_parts` へ移管した。
   - [x] object レシーバ禁止検証を `CodeEmitter.validate_call_receiver_or_raise` へ移管し、`py2cpp.py` 側の `Call(Attribute)` 直書き分岐を削減した。
   - [x] `render_expr(Call)` 本体を `_render_call_expr_from_context` へ分離し、hook/builtin/name-or-attr/fallback の段階処理を独立関数化した。
   - [x] `render_expr(Call)` 末尾の `kw_values/kw_nodes` マージ処理を `_merge_call_kw_values` / `_merge_call_arg_nodes` へ分離した。
   - [x] 上記 helper を `CodeEmitter.merge_call_kw_values` / `CodeEmitter.merge_call_arg_nodes` へ移管した。
   - [x] `render_expr(Call)` の `Call(Name)` import 経路を `_resolve_or_render_imported_symbol_name_call` へ抽出し、段階処理（import解決→ビルトイン→fallback）を明確化した。
3. [ ] `render_expr` の算術/比較/型変換分岐を独立関数へ分割し、profile/hook 経由で切替可能にする。
   - [x] `RangeExpr/BinOp/UnaryOp/BoolOp/Compare/IfExp` の分岐を `_render_operator_family_expr` へ集約し、`render_expr` 本体の分岐を削減した。
4. [ ] `Constant(Name/Attribute)` の基本レンダを `CodeEmitter` 共通へ移す。
   - [ ] `CodeEmitter` 側の共通ディスパッチは selfhost C++ で静的束縛（非 virtual）により派生レンダへ到達しないため、別方式（hook 注入）で再設計する。
5. [ ] `emit_stmt` の制御構文分岐をテンプレート化して `CodeEmitter.syntax_*` へ寄せる。
   - [x] `try/catch/finally(scope guard)` の開始行（`scope_open` / `scope_exit_open` / `try_open` / `catch_open`）を `syntax.json` + `syntax_line` 経由へ移管した。
   - [x] `for` ブロック開始行（`hdr + " {"`）を `for_open_block` テンプレートへ移管した。
   - [x] `pass/break/continue` の文生成を `syntax.json`（`pass_stmt` / `break_stmt` / `continue_stmt`）経由へ移管した。
   - [x] `swap` / `raise` の文生成を `syntax.json`（`swap_stmt` / `raise_default` / `raise_expr`）経由へ移管した。
   - [x] `Expr` / `Return` の文生成を `syntax.json`（`expr_stmt` / `return_void` / `return_value`）経由へ移管した。
6. [ ] C++ 固有差分（brace省略や range-mode）だけ hook 側で上書きする。
7. [ ] `FunctionDef` / `ClassDef` の共通テンプレート（open/body/close）を `CodeEmitter` 側に寄せる。
8. [ ] 未使用関数の掃除を継続する（詳細タスクは最優先側へ移動しながら管理）。

## P2: Any/object 境界の整理

1. [ ] `CodeEmitter` の `Any/dict` 境界を selfhost で崩れない実装へ段階移行する。
   - [x] `CppEmitter._render_call_attribute` の module/object 呼び出し中間値を branch-local 化し、selfhost 生成 C++ で `object` へ退避しない形に修正した。
   - [x] 上記修正後も `tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` で `mismatches=0` を確認した。
   - [x] `dict[str, str]` 変換ヘルパ（`CodeEmitter.any_to_str_dict_or_empty`）を追加し、`render_expr(Call)` の `kw` 展開で共通利用するようにした。
2. [ ] `cpp_type` と式レンダリングで `object` 退避を最小化する。
3. [ ] `Any -> object` が必要な経路と不要な経路を分離し、`make_object(...)` の過剰挿入を減らす。
   - [x] Any/object 向け boxing 判定を `_box_expr_for_any` へ集約し、`List`/`Dict` リテラル生成で「既に object/Any の式」を二重に `make_object(...)` しないようにした。
   - [x] `Constant(None)` の Any/object 経路を `make_object(1)` から `object{}` へ修正し、`None` の表現を統一した。
   - [x] boxing 済み判定 helper（`_is_boxed_object_expr`）を追加し、`_coerce_args_for_module_function` / `_coerce_py_assert_args` / Assign/AnnAssign / dict key coercion で `object{}` の再 boxing を抑止した。
   - [x] `py_assert_*` の object 引数 boxing をノード型付き（`arg_nodes`）で判定し、`object/Any` 引数への不要な `make_object(...)` を回避した。
4. [ ] `py_dict_get_default` / `dict_get_node` の既定値引数が `object` 必須になる箇所を整理する。
   - [x] `dict.get` の object 系 owner 経路で、`resolved_type` または既定値型が数値（int/float）なら `dict_get_int` / `dict_get_float` を優先し、`py_dict_get_default`/`dict_get_node` の汎用 object 経路を減らした。
5. [ ] `py2cpp.py` で `nullopt` を default 値に渡している箇所を洗い出し、型ごとの既定値へ置換する。
   - [x] 関数引数既定値（`_render_param_default_expr` / `_header_render_default_expr`）で `None` を一律 `::std::nullopt` にしていた処理を型別既定値へ変更した（`int -> 0`, `float -> 0.0`, `str -> str()`, `Any/object -> object{}` など）。
   - [x] 既存 optional 型（`optional[...]` / `| None`）は `::std::nullopt` を維持するようにした。
6. [ ] `std::any` を経由する経路（selfhost 変換由来）をログベースでリスト化し、順次削除する。
   - [x] `unknown` / 混在 `Union` / `list[unknown]` / `dict[..., unknown]` の既定マッピングを `::std::any` から `object` 系へ寄せた（`_cpp_type_text`）。
   - [x] `render_minmax` / 内包表現の動的型判定で `std::any` 依存判定を削減し、`object`/`auto` 判定へ寄せた。
7. [ ] 上位3関数ごとにパッチを分けて改善し、毎回 `check_py2cpp_transpile.py` を通す。

## P3: 低優先（可読性・Pythonらしさの回復）

1. [x] `src/py2cpp.py` の selfhost 都合で平易化している実装を棚卸しし、一般的な Python 風の書き方へ戻す候補一覧を作る。
   - [x] 候補一覧を `docs-jp/pythonic-backlog.md` に作成した。
2. [ ] `src/pytra/compiler/east_parts/code_emitter.py` で同様に平易化されている箇所を段階的に Python らしい記述へ戻す。
3. [ ] `sample/` のコードについても、selfhost 都合の書き方が残っている箇所を通常の Python らしい表現へ順次戻す。
4. [ ] 上記の戻し作業は低優先で進め、各ステップで `tools/build_selfhost.py` と `tools/check_py2cpp_transpile.py` を通して回帰を防ぐ。

## 補助メモ

- 完了済みタスクと過去ログは `docs-jp/todo-old.md` に移管済み。
- 今後 `docs-jp/todo.md` は未完了タスクのみを保持する。
