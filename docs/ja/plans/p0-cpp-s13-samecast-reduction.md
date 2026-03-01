# P0: sample/13 同型 cast 連鎖の縮退

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S13-SAMECAST-CUT-01`

背景:
- sample/13 の C++ 出力に `int64(py_to<int64>(...))` など同型 cast 連鎖が残る。
- 既知型経路でも dynamic cast 文字列が残って可読性を悪化させる。

目的:
- 型既知経路の `int64(py_to<int64>(...))` / 同種 no-op cast を削減し、直接利用に寄せる。

対象:
- `src/pytra/compiler/east_parts/east3_opt_passes/*`（必要なら cast 縮退 pass）
- `src/hooks/cpp/emitter/expr.py` / `type_bridge.py`（最終ガード）
- `test/unit/test_py2cpp_codegen_issues.py`

非対象:
- `object/Any/unknown` 経路の cast 契約変更
- runtime `py_to` API 仕様変更

受け入れ基準:
- sample/13 の同型 cast 連鎖が縮退する。
- unknown 経路は fail-closed で維持される。
- `check_py2cpp_transpile` と unit が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

決定ログ:
- 2026-03-01: ユーザー要望により、sample/13 同型 cast 縮退を独立 P0 として起票。

## 分解

- [ ] [ID: P0-CPP-S13-SAMECAST-CUT-01-S1-01] sample/13 の同型 cast パターンと縮退適用条件を固定する。
- [ ] [ID: P0-CPP-S13-SAMECAST-CUT-01-S2-01] EAST3 または C++ emitter で同型 cast 縮退を実装する。
- [ ] [ID: P0-CPP-S13-SAMECAST-CUT-01-S3-01] 回帰を追加し、transpile/check を通す。
