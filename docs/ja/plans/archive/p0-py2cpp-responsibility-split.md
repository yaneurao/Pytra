# TASK GROUP: TG-P0-PY2CPP-SPLIT

最終更新: 2026-02-24

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PY2CPP-SPLIT-01` 〜 `P0-PY2CPP-SPLIT-01-S7`

背景:
- `src/py2cpp.py` は CLI であるべきだが、現状は emitter 本体・依存解析導線・header 生成・multi-file 出力・runtime 出力配線などを同居させたモノリスになっている。
- 既に `P0-CPP-EAST2-01` / `P0-EAST1-BUILD-01` / `P0-DEP-EAST1-01` / `P0-CPP-EMITTER-01` で高優先の構造改善を開始しており、これを受けて残責務も分離する必要がある。

目的:
- `py2cpp.py` を「CLI / 引数処理 / 高位オーケストレーション」のみに縮退し、C++ backend 実装責務を専用モジュールへ分割する。

対象:
- `src/py2cpp.py` の profile/type-map/hooks ロード実装。
- header 生成ロジック。
- multi-file 出力と manifest 生成ロジック。
- runtime emit 用パス/namespace 補助ロジック。
- `transpile_cli` helper 再エクスポート層（`_HELPER_GROUPS`）。

非対象:
- C++ 生成意味論の変更。
- 各最優先 P0 タスク（EAST2 廃止・EAST1 build 責務化・依存解析責務化・CppEmitter 抽出）自体の置換。

受け入れ基準:
- `py2cpp.py` が CLI/配線に集中し、backend 本体ロジックを保持しない。
- 分離先モジュールの責務境界が `spec-dev` に反映される。
- `check_py2cpp_transpile` / smoke / 必要な unit test が通過する。

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py'`
- `python3 tools/check_todo_priority.py`

決定ログ:
- 2026-02-24: ユーザー指示により、`py2cpp.py` の残責務を段階分離する `P0` タスク群を追加。
- 2026-02-24: `src/hooks/cpp/profile/cpp_profile.py` を追加し、`load_cpp_profile` 系（profile/ルール/type-map/hooks）を移譲。`py2cpp.py` と `cpp_emitter.py` には後方互換の委譲 API を残し、責務を `profile` モジュールへ集中。
- 2026-02-24: `src/hooks/cpp/header/cpp_header.py` を追加し、`build_cpp_header_from_east` と header 型変換・既定値・include guard 生成ロジックを分離。`py2cpp.py` では `build_cpp_header_from_east` を `_build_cpp_header_from_east` 経由の wrapper として維持。
- 2026-02-25: `src/hooks/cpp/multifile/cpp_multifile.py` を追加し、`_write_multi_file_cpp` と manifest 生成責務を移譲。`py2cpp.py` 側は wrapper のみ残す構成へ変更。
- 2026-02-26: `src/py2cpp.py` の `_HELPER_GROUPS` を削除し、`pytra.compiler.transpile_cli` の helper 群を明示 import へ移行。`py2cpp.py` は `dump_deps_graph_text_common` を含む互換 wrapper を維持し、境界チェックを継続する構成へ変更。
- 2026-02-27: `P0-PY2CPP-SPLIT-01-S7` 完了。`src/hooks/cpp/runtime_emit/__init__.py` で `_join_runtime_path` 等の互換エイリアスを追加し、`src/py2cpp.py` import 断絶を解消。`python3 tools/check_py2cpp_boundary.py` / `python3 tools/check_py2cpp_transpile.py` / `python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py'` を実行し、責務回帰ガードを固定。
