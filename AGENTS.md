# エージェント運用ルール

## docs-jp の基本方針

- 作業開始時に `docs-jp/spec-codex.md` を読み、記載ルールに従う。
- `docs-jp/` を正（source of truth）とし、`docs/` は翻訳ミラーとして扱う。
- `docs-jp/` 配下に新規ファイルを作成する場合は、同一ターンでの明示依頼があるときのみ許可する。
- 未完了タスクは `docs-jp/todo.md` にのみ記載する。
- 完了済みは `docs-jp/todo-old.md` と `docs-jp/todo-history/YYYYMMDD.md` へ移す。

## 長期計画メモの置き場

- 長期計画・設計ドラフト・調査メモは `docs-jp/plans/` に保存する。
- `docs-jp/plans/` の内容は日本語で記述する。
- 実行可能な未完了タスクに落ちた項目だけを `docs-jp/todo.md` に転記する。

## ガード運用

- docs を触ったコミット前に `python3 tools/check_docs_jp_guard.py` を実行する。
- `tools/check_docs_jp_guard.py` は `docs-jp/` 配下の未管理ファイルを検出したら失敗する。
