# TODO（未完了）

<a href="../docs/todo.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


最終更新: 2026-02-21

## P0: selfhost 安定化

1. [ ] `tools/prepare_selfhost_source.py` の selfhost 専用スタブ整理を継続する。
   - [ ] `load_cpp_hooks` スタブを除去する（hooks 同梱または等価の汎用手段で対応）。
   - [ ] import-graph 系スタブ（`_analyze_import_graph` / `_format_import_graph_report` / `_validate_import_graph_or_raise` / `_rel_disp_for_graph`）を除去する。
   - [ ] `build_module_east_map` スタブを除去する。
   - [ ] multi-file 系スタブ（`_write_multi_file_cpp`）を除去する。
   - [ ] `_extract_function_arg_types_from_python_source` スタブを除去する。
   - [ ] `build_cpp_header_from_east` スタブを除去する。
2. [ ] 上記の各段階で `build_selfhost` / `build_selfhost_stage2` / 差分チェック2系統を green 維持する。

## P1: CodeEmitter / Hooks 移管

1. [ ] フック注入 (`EmitterHooks`) を実装する。
2. [ ] `render_expr(Call/BinOp/Compare)` の巨大分岐を hooks + helper へ段階分離する。
3. [ ] profile で表現しにくいケースのみ hooks 側へ寄せる（`py2cpp.py` に条件分岐を残さない）。

## P1: py2cpp 縮退（行数削減）

1. [ ] `src/py2cpp.py` の未移行ロジックを `CodeEmitter` 側へ移し、行数を段階的に削減する。
2. [ ] `render_expr` の `Call` 分岐（builtin/module/method）を機能単位に分割し、`CodeEmitter` helper へ移す。
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
7. [ ] 上位3関数ごとにパッチを分けて改善し、毎回 `check_py2cpp_transpile.py` を通す。

## P3: 低優先（可読性・Pythonらしさの回復）

1. [ ] `src/py2cpp.py` の selfhost 都合で平易化している実装を棚卸しし、一般的な Python 風の書き方へ戻す候補一覧を作る。
2. [ ] `src/pytra/compiler/east_parts/code_emitter.py` で同様に平易化されている箇所を段階的に Python らしい記述へ戻す。
3. [ ] `sample/` のコードについても、selfhost 都合の書き方が残っている箇所を通常の Python らしい表現へ順次戻す。
4. [ ] 上記の戻し作業は低優先で進め、各ステップで `tools/build_selfhost.py` と `tools/check_py2cpp_transpile.py` を通して回帰を防ぐ。

## 補助メモ

- 完了済みタスクと過去ログは `docs-jp/todo-old.md` に移管済み。
- 今後 `docs-jp/todo.md` は未完了タスクのみを保持する。
