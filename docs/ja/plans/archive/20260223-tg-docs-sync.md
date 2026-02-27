# TASK GROUP: TG-DOCS-SYNC

最終更新: 2026-02-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: DOCS-SYNC-01`

背景:
- `docs-ja` を正本としているが、`todo/archive` の英訳同期手順が未整備で運用が属人化しやすい。

目的:
- `docs/ja/todo/archive/YYYYMMDD.md` を基点に、`docs/en/todo/archive/YYYYMMDD.md` へ同期する定常フローを定義する。

対象:
- 同期手順の明文化
- 反映単位（日時/ファイル）と更新責務の整理
- 同期漏れを機械的に検出する最小チェック導線の整備

非対象:
- 既存全文書の一括再翻訳

受け入れ基準:
- 手順どおりに日次同期を再現できる
- `docs-ja` と `docs` の差分把握が容易になる
- `docs/ja/todo/archive` の日付ファイル集合と `docs/en/todo/archive` のミラー集合を自動チェックできる

運用手順:
1. `python3 tools/sync_todo_history_translation.py` を実行し、`docs/en/todo/archive/YYYYMMDD.md` の不足分を作成する。
2. 生成された `pending` ファイルを英語翻訳し、`<!-- translation-status: done -->` へ更新する。
3. `python3 tools/sync_todo_history_translation.py --check` で同期漏れ（missing/extra/index欠落）がないことを確認する。
4. `git diff -- docs/ja/todo/archive docs/en/todo/archive` で差分単位を確認してコミットする。

確認コマンド:
- `python3 tools/sync_todo_history_translation.py --check`
- `git diff -- docs/ja/todo/archive docs/en/todo/archive`

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-22: `tools/sync_todo_history_translation.py` を追加し、`docs/en/todo/archive` の日付ファイル雛形と index 同期を自動化した。
