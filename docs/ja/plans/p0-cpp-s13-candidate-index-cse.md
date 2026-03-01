# P0: sample/13 `candidates` 選択式の CSE/hoist

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S13-CANDIDATE-CSE-01`

背景:
- sample/13 の `sel` 抽出で `(x * 17 + y * 29 + len(stack) * 13) % len(candidates)` と `py_at(candidates, idx)` が要素ごとに繰り返されている。
- 同一式の多重展開により可読性と実行効率が悪化する。

目的:
- 同一 index 計算と同一要素参照を一時変数へ hoist し、`sel` 展開を 1 回参照にする。

対象:
- `src/hooks/cpp/emitter/stmt.py` / 必要に応じて EAST3 optimizer pass
- `test/unit/test_py2cpp_codegen_issues.py`

非対象:
- 一般 CSE の全面導入
- sample/13 以外の包括的最適化保証

受け入れ基準:
- sample/13 で index 計算が 1 回化され、`candidates[...]` / `py_at(candidates, ...)` の重複が減る。
- `sel` 展開が単一取得からの `get<0..3>` になる。
- 既存回帰を壊さない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

決定ログ:
- 2026-03-01: ユーザー要望により、sample/13 の `candidates` 選択式重複を独立 P0 として起票。

## 分解

- [ ] [ID: P0-CPP-S13-CANDIDATE-CSE-01-S1-01] `sel` 周辺の重複式パターンと適用条件（fail-closed）を定義する。
- [ ] [ID: P0-CPP-S13-CANDIDATE-CSE-01-S2-01] index/要素取得の hoist を実装し、重複出力を削減する。
- [ ] [ID: P0-CPP-S13-CANDIDATE-CSE-01-S3-01] sample/13 回帰を追加し、transpile/check を通す。
