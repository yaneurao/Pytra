# TASK GROUP: TG-P1-CPP-REDUCE

最終更新: 2026-02-22

関連 TODO:
- `docs-jp/todo.md` の `ID: P1-CPP-REDUCE-01`

背景:
- `py2cpp.py` の肥大化により、変更影響範囲が広くレビュー・回帰確認コストが高い。

目的:
- `py2cpp.py` を C++ 固有責務へ段階縮退し、共通処理は共通層へ移す。

対象:
- `CodeEmitter` 側へ移管可能なロジック
- CLI 層の責務分離

非対象:
- selfhost 安定性を犠牲にする大規模一括整理

受け入れ基準:
- `py2cpp.py` 行数と分岐数が段階減少
- 主要テストと selfhost 検証が維持

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/build_selfhost.py`

決定ログ:
- 2026-02-22: 初版作成。
