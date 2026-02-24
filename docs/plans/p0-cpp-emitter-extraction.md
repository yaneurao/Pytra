# TASK GROUP: TG-P0-CPP-EMITTER-EXTRACTION

最終更新: 2026-02-24

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-CPP-EMITTER-01` 〜 `P0-CPP-EMITTER-01-S4`

背景:
- 現在 `CppEmitter` 本体が `src/py2cpp.py` に同居しており、CLI/配線と出力本体の責務が混在している。
- 他言語（`py2rs.py` など）は CLI が薄く、emitter 本体は `hooks/<lang>/emitter` に分離されているため、C++ だけ構造が不整合になっている。
- ユーザー指示として「emitter 本体を `py2cpp.py` から分離する」が確定している。

目的:
- `CppEmitter` 本体を `hooks/cpp/emitter` へ移し、`py2cpp.py` を CLI/入出力/オーケストレーションに限定する。

対象:
- `src/py2cpp.py` にある `class CppEmitter` と関連補助ロジック。
- `src/hooks/cpp/emitter/`（新設）への移管。
- `py2cpp` 入口 API（`transpile_to_cpp` など）の再配線。

非対象:
- C++ 生成仕様の意味変更。
- EAST1/EAST2/EAST3 仕様の追加変更。

受け入れ基準:
- `CppEmitter` 本体は `src/hooks/cpp/emitter/cpp_emitter.py` に存在する。
- `src/py2cpp.py` は CLI と公開 API の薄いラッパに縮退する。
- 既存 `tools/check_py2cpp_transpile.py` / smoke が通り、出力回帰がない。
- `spec-dev` に C++ backend 構成（CLI と emitter 分離）が反映される。

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 -m unittest test.unit.test_py2cpp_smoke`
- `python3 tools/check_todo_priority.py`

決定ログ:
- 2026-02-24: ユーザー指示により、`py2cpp.py` から `CppEmitter` 本体を抽出する `P0` タスクを追加。
- 2026-02-24: [ID: P0-CPP-EMITTER-01-S1] `src/hooks/cpp/emitter/cpp_emitter.py` へ `CppEmitter` クラスを移設し、`py2cpp.py` 側は import + `install_py2cpp_runtime_symbols(globals())` を経由する構成へ変更。
- 2026-02-24: [ID: P0-CPP-EMITTER-01-S2] `src/hooks/cpp/emitter/__init__.py` を API 入口として整備し、`py2cpp.py` 側を `hooks.cpp.emitter` 経由で参照可能にした。
- 2026-02-25: [ID: P0-CPP-EMITTER-01-S3] `src/py2cpp.py` 側を整理し、`CppEmitter` クラスが同居しないことを明確化。
- 2026-02-25: [ID: P0-CPP-EMITTER-01-S4] 分離状態を固定するため、`test/unit/test_py2cpp_smoke.py` と `tools/check_py2cpp_helper_guard.py` を更新し、実装本体が `src/hooks/cpp/emitter/cpp_emitter.py` にのみ存在する回帰ガードを追加。
