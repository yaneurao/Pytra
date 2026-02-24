# plans

このフォルダは、長期計画・設計ドラフト・調査メモの置き場です。

## ルール

- 記載内容は日本語で書く。
- ここには未完了タスクに紐づく計画のみを置き、正式な進捗管理は `docs-ja/todo/index.md` で行う。
- 具体的に着手する項目だけを `docs-ja/todo/index.md` に転記する。
- 各 plan は `todo` のタスク ID（例: `P1-COMP-01`）と 1 対 1 で紐づける。
- `todo` 側には、タスク ID と対応 plan ファイルパスを必ず併記する。
- 優先度上書きの指示形式は `docs-ja/plans/instruction-template.md` を使う。

## 完了時の運用（必須）

- 紐づく `todo` のタスク ID がすべて完了（`[x]`）した plan は、`docs-ja/plans/` に残さない。
- 完了した plan は `docs-ja/plans/archive/YYYYMMDD-<task-group>.md` へ移動する。
- `YYYYMMDD` は移動日（または完了確定日）を使う。
- `docs-ja/todo/archive/index.md` に、完了 plan へのリンクを 1 行追加する。
- 詳細な完了文脈は該当日の `docs-ja/todo/archive/YYYYMMDD.md` 側に記録する。

## 推奨テンプレート

```md
# TASK GROUP: <グループID>

最終更新: YYYY-MM-DD

関連 TODO:
- `docs-ja/todo/index.md` の `ID: ...`

背景:
目的:
対象:
- ...
非対象:
- ...
受け入れ基準:
- ...
確認コマンド:
- ...
決定ログ:
- YYYY-MM-DD: 初版作成。
```
