# TASK GROUP: TG-DOCS-SYNC

最終更新: 2026-02-22

関連 TODO:
- `docs-jp/todo.md` の `ID: DOCS-SYNC-01`

背景:
- `docs-jp` を正本としているが、`todo-history` の英訳同期手順が未整備で運用が属人化しやすい。

目的:
- `docs-jp/todo-history/YYYYMMDD.md` を基点に、`docs/todo-history/YYYYMMDD.md` へ同期する定常フローを定義する。

対象:
- 同期手順の明文化
- 反映単位（日時/ファイル）と更新責務の整理

非対象:
- 既存全文書の一括再翻訳

受け入れ基準:
- 手順どおりに日次同期を再現できる
- `docs-jp` と `docs` の差分把握が容易になる

確認コマンド:
- `git diff -- docs-jp/todo-history docs/todo-history`

決定ログ:
- 2026-02-22: 初版作成。
