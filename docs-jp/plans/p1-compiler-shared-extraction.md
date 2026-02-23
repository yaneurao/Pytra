# TASK GROUP: TG-P1-COMP-SHARED

最終更新: 2026-02-23

関連 TODO:
- `docs-jp/todo.md` の `ID: P1-COMP-01` 〜 `P1-COMP-10`

背景:
- import グラフ解析や module index 構築など全言語共通処理が `py2cpp.py` に偏在している。
- 将来的な目標は「全言語で selfhost 可能な変換能力」であり、特定言語実装（`py2cpp.py`）への汎用処理偏在は拡張時のボトルネックになる。

目的:
- 共通解析を `src/pytra/compiler/` の API へ抽出し、各 `py2*` CLI で再利用可能にする。
- `py2cpp.py` は C++ 固有責務へ限定し、他言語 selfhost 導線でも再利用できる共通実装を優先する。

対象:
- import グラフ解析
- module EAST map / symbol index / type schema 構築
- deps dump API
- `CodeEmitter` と parser の責務境界明文化

非対象:
- 言語固有のコード生成最適化
- runtime 出力形式の変更

受け入れ基準:
- 共通解析 API が `py2cpp` 以外から利用可能
- `py2cpp.py` は C++ 固有責務中心に縮退
- 境界定義（CodeEmitter / parser / compiler共通層）が文書化される
- `py2cpp.py` 由来の汎用 helper が `src/pytra/compiler/` へ移管され、少なくとも 1 つ以上の非 C++ `py2*` で再利用される
- 新規の汎用処理は `py2cpp.py` ではなく共通層へ追加する運用ルールが定義され、回帰チェックで担保される

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 test/unit/test_py2cpp_features.py`

`P1-COMP-08` 移行計画（他言語 CLI の共通解析 API 採用）:

1. Phase 0（API 固定化）
   - `src/pytra/compiler/` に共通解析 API の入口を定義する。
   - 最低限の提供単位は `import_graph` / `module_east_map` / `symbol_index` / `type_schema` / `deps_dump` とする。
   - CLI から見える戻り値型（dict スキーマ）を固定し、`py2cpp` 実装を参照実装として扱う。
2. Phase 1（`py2rs.py` 先行適用）
   - `py2rs.py` から `py2cpp.py` 固有 helper 直呼びを禁止し、共通 API 経由で module 解析結果を受け取る。
   - 既存出力との差分を `tools/check_py2rs_transpile.py` で確認する。
3. Phase 2（`py2cs.py` / `py2js.py` / `py2ts.py` へ展開）
   - 3 言語の CLI で同一 API を使い、import 解決の前段を共通化する。
   - `meta.import_bindings` 利用前の解析処理（FS 依存部分）を共通層へ移す。
4. Phase 3（preview 言語 `py2go.py` / `py2java.py` / `py2swift.py` / `py2kotlin.py` へ展開）
   - 失敗時の診断形式（解析失敗 / 変換失敗）を共通化し、言語別 CLI は表示責務に限定する。
   - 各 `tools/check_py2<lang>_transpile.py` が同一前処理 API を使う状態まで寄せる。
5. Phase 4（旧経路の縮退）
   - `py2cpp.py` を含む各 CLI から重複した project 解析コードを削除する。
   - 共通 API 層に回帰テストを追加し、CLI 層は配線テスト中心へ移行する。

完了条件:
- 非 C++ の各 CLI が、project 解析を `src/pytra/compiler/` 共通 API 経由で実行する。
- `py2cpp.py` 側に残る project 解析実装は C++ 固有補助を除き撤去される。
- 既存の transpile チェック（`tools/check_py2*.py`）が回帰なく通過する。

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-22: `P1-COMP-06` / `P1-COMP-07` として、`docs-jp/spec/spec-dev.md` に `CodeEmitter`・EAST parser・compiler共通層の責務境界を明文化した。
- 2026-02-22: `P1-COMP-08` として、`py2rs.py` を起点に他言語 CLI へ共通解析 API を段階適用する 5 フェーズ移行計画を追加した。
- 2026-02-23: 全言語 selfhost を長期目標として再確認し、`py2cpp.py` への汎用 helper 集積を抑制する方針を `P1-COMP-09` / `P1-COMP-10` として追加した。
- 2026-02-23: `P1-COMP-09` の小パッチとして、`src/py2cpp.py` の文字列リスト整列 helper を `src/pytra/compiler/transpile_cli.py::sort_str_list_copy` へ移管した。selfhost 展開で同 helper が欠落しないよう `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去対象と support block 抽出名リストを更新し、`test/unit/test_prepare_selfhost_source.py` / `test/unit/test_py2cpp_features.py` で回帰を固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` の区切り結合 helper `_join_str_list` も `src/pytra/compiler/transpile_cli.py::join_str_list` へ移管した。`py2cpp` 内の呼び出しを共通 helper へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `join_str_list` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` の区切り分割 helper `_split_infix_once` も `src/pytra/compiler/transpile_cli.py::split_infix_once` へ移管した。`py2cpp` 側の呼び出しを共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `split_infix_once` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` の単発文字列置換 helper `_replace_first` も `src/pytra/compiler/transpile_cli.py::replace_first` へ移管した。`py2cpp` 側の include 注入系処理は共通 helper 呼び出しへ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `replace_first` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` の親ディレクトリ解決 helper `_path_parent_text` も `src/pytra/compiler/transpile_cli.py::path_parent_text` へ移管した。`py2cpp` 側の呼び出し（import graph / multi-file 出力 / CLI 出力先の親ディレクトリ解決）を共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `path_parent_text` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` のディレクトリ生成 helper `_mkdirs_for_cli` も `src/pytra/compiler/transpile_cli.py::mkdirs_for_cli` へ移管した。`py2cpp` 側の出力前ディレクトリ作成処理を共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `mkdirs_for_cli` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` のテキスト書き出し helper `_write_text_file` も `src/pytra/compiler/transpile_cli.py::write_text_file` へ移管した。`py2cpp` 側の出力処理（multi-file prelude/manifest、runtime/header、`-o/--dump-*`）を共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `write_text_file` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` の行数集計 helper `_count_text_lines` も `src/pytra/compiler/transpile_cli.py::count_text_lines` へ移管した。`py2cpp` 側の `max_generated_lines` ガード集計を共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `count_text_lines` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` の空白トークン分割 helper `_split_ws_tokens` も `src/pytra/compiler/transpile_cli.py::split_ws_tokens` へ移管した。`py2cpp` 側の import エラー詳細抽出（`from/import` 行トークン化）を共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `split_ws_tokens` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` の重複排除追加 helper `_append_unique_non_empty` も `src/pytra/compiler/transpile_cli.py::append_unique_non_empty` へ移管した。`py2cpp` 側の include/module/symbol/import graph 収集で同 helper 呼び出しを共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `append_unique_non_empty` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` のトップレベル CSV 分割 helper `_split_top_level_csv` も `src/pytra/compiler/transpile_cli.py::split_top_level_csv` へ移管した。`py2cpp` 側の関数シグネチャ抽出・`TypeVar`/`Union` 解析で同 helper 呼び出しを共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `split_top_level_csv` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` の辞書既定値取得 helper `_dict_str_get` も `src/pytra/compiler/transpile_cli.py::dict_str_get` へ移管した。`py2cpp` 側の CLI 解析結果 `dict[str, str]` 読取を共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `dict_str_get` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` の runtime 関数名判定 helper `_looks_like_runtime_function_name` も `src/pytra/compiler/transpile_cli.py::looks_like_runtime_function_name` へ移管した。`py2cpp` 側の module attr call map 判定を共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `looks_like_runtime_function_name` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` の import ローカル束縛名 helper `_local_binding_name` も `src/pytra/compiler/transpile_cli.py::local_binding_name` へ移管した。`py2cpp` 側の import/import-from 解析を共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `local_binding_name` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` の import graph issue 分解 helper `_split_graph_issue_entry` も `src/pytra/compiler/transpile_cli.py::split_graph_issue_entry` へ移管した。`py2cpp` 側の `file: module` 解析を共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `split_graph_issue_entry` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
- 2026-02-23: `P1-COMP-09` の継続として、`src/py2cpp.py` の型引数分割 helper `_split_type_args` も `src/pytra/compiler/transpile_cli.py::split_type_args` へ移管した。`py2cpp` 側の header 型 lower（`list[...]` / `dict[...]`）を共通 helper 経由へ統一し、selfhost 用 `tools/prepare_selfhost_source.py` の `transpile_cli` import 除去ターゲットと support block 抽出対象へ `split_type_args` を追加した。`test/unit/test_prepare_selfhost_source.py` と `test/unit/test_py2cpp_features.py` の回帰を更新して固定した。
