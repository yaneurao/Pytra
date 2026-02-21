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
   - [x] `Call` 前処理（`_prepare_call_parts`）を `CodeEmitter` 側へ移管し、selfhost-safe 化のうえ `py2cpp.py` 側フォールバックを削除した。
   - [x] `IfExp` 共通レンダ（`_render_ifexp_expr`）と定数解析ヘルパ（`_one_char_str_const`, `_const_int_literal`）を `CodeEmitter` 側へ移管した。
   - [x] `BinOp` の優先順位/括弧補完ヘルパ（`_binop_precedence`, `_wrap_for_binop_operand`）を `CodeEmitter` 側へ移管した。
   - [x] 文字列探索/末尾セグメント抽出ヘルパ（`_contains_text`, `_last_dotted_name`）を `CodeEmitter` 側へ移管した。
   - [x] 最適化レベル判定ヘルパ（`_opt_ge`）を `CodeEmitter` 側へ移管した。
   - [x] import 解決ヘルパ（`_resolve_imported_module_name`, `_resolve_imported_symbol`）を `CodeEmitter` 側へ移管した。
   - [x] 上記 import 解決ヘルパは selfhost-safe 化（`__dict__` 非依存・型付き dict 直接参照）を完了した。
   - [x] 実行時キャスト対象判定（`_can_runtime_cast_target`）を `CodeEmitter` 側へ移管した。
   - [x] `std::` runtime 判定ヘルパ（`_is_std_runtime_call`）を `CodeEmitter` 側へ移管した。
   - [x] call/attribute 周辺の `module.attr` runtime lookup を helper 化し、`render_call`/`render_attribute`/hooks から共通利用するよう整理した。
   - [ ] call/attribute 周辺の C++ 固有分岐をさらに helper/hook 化して `py2cpp.py` 本体行数を削減する。
2. [ ] `render_expr` の `Call` 分岐（builtin/module/method）を機能単位に分割し、`CodeEmitter` helper へ移す。
   - [x] `render_expr(Call)` 末尾の `kw_values/kw_nodes` マージ処理を `_merge_call_kw_values` / `_merge_call_arg_nodes` へ分離した。
   - [x] 上記 helper を `CodeEmitter.merge_call_kw_values` / `CodeEmitter.merge_call_arg_nodes` へ移管した。
3. [ ] `render_expr` の算術/比較/型変換分岐を独立関数へ分割し、profile/hook 経由で切替可能にする。
4. [ ] `Constant(Name/Attribute)` の基本レンダを `CodeEmitter` 共通へ移す。
5. [ ] `emit_stmt` の制御構文分岐をテンプレート化して `CodeEmitter.syntax_*` へ寄せる。
6. [ ] C++ 固有差分（brace省略や range-mode）だけ hook 側で上書きする。
7. [ ] `FunctionDef` / `ClassDef` の共通テンプレート（open/body/close）を `CodeEmitter` 側に寄せる。
8. [ ] 未使用関数の掃除を継続する（詳細タスクは最優先側へ移動しながら管理）。

## P2: Any/object 境界の整理

1. [ ] `CodeEmitter` の `Any/dict` 境界を selfhost で崩れない実装へ段階移行する。
2. [ ] `cpp_type` と式レンダリングで `object` 退避を最小化する。
3. [ ] `Any -> object` が必要な経路と不要な経路を分離し、`make_object(...)` の過剰挿入を減らす。
4. [ ] `py_dict_get_default` / `dict_get_node` の既定値引数が `object` 必須になる箇所を整理する。
5. [ ] `py2cpp.py` で `nullopt` を default 値に渡している箇所を洗い出し、型ごとの既定値へ置換する。
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
