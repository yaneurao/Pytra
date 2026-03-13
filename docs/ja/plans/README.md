# plans

このフォルダは、長期計画・設計ドラフト・調査メモの置き場です。

## live plan の見方

- `plans/` 直下の canonical entrypoint は raw のファイル一覧ではなく、この `README.md` とする。
- `active` は `docs/ja/todo/index.md` の未完了タスクから直接参照されている live plan に限る。
- `backlog` は live の `p*-*.md` で、TODO 未登録かつ、未完了 backlog か live status/report sink として残してよいものとする。
- `stale-complete` は live の `p*-*.md` で、TODO 未登録、checklist 完了、かつ live status/report sink でもないものとする。これは `plans/` 直下へ残さず archive へ移す。

2026-03-14 時点の active live plan:
- `p1-nes3-not-implemented-error-cpp-support.md`
- `p1-nes3-bytes-member-truthiness-cpp-support.md`
- `p1-nes3-list-default-factory-rc-list-cpp-support.md`
- `p1-nes3-path-alias-pkg-cpp-support.md`
- `p1-nes3-apu-const-pkg-cpp-support.md`
- `p1-nes3-bus-port-pkg-cpp-support.md`
- `p2-cpp-legacy-core-compat-retire.md`
- `p2-multilang-extern-runtime-realign.md`
- `p2-backend-contract-coverage-100.md`
- `p2-cpp-pyruntime-upstream-fallback-shrink.md`

## ルール

- 記載内容は日本語で書く。
- ここには未完了タスクに紐づく計画のみを置き、正式な進捗管理は `docs/ja/todo/index.md` で行う。
- 具体的に着手する項目だけを `docs/ja/todo/index.md` に転記する。
- 各 plan は `todo` のタスク ID（例: `P1-COMP-01`）と 1 対 1 で紐づける。
- `todo` 側には、タスク ID と対応 plan ファイルパスを必ず併記する。
- readiness report のような補助レポートを `plans/` に置く場合も、対応する plan から必ずリンクする。
- 優先度上書きの指示形式は `docs/ja/plans/instruction-template.md` を使う。
- TODO 未登録の draft を live `plans/` に置く場合は backlog とみなし、raw のファイル一覧ではなくこの README の分類基準で扱う。
- 新しい backlog draft は `関連 TODO:` に `なし（backlog draft / TODO 未登録）` を明記してよい。TODO へ昇格した時点で対応 ID に差し替える。

## 完了時の運用（必須）

- 紐づく `todo` のタスク ID がすべて完了（`[x]`）した plan は、`docs/ja/plans/` に残さない。
- 完了した plan は `docs/ja/plans/archive/YYYYMMDD-<task-group>.md` へ移動する。
- `YYYYMMDD` は移動日（または完了確定日）を使う。
- `docs/ja/todo/archive/index.md` に、完了 plan へのリンクを 1 行追加する。
- 詳細な完了文脈は該当日の `docs/ja/todo/archive/YYYYMMDD.md` 側に記録する。

## Archive Handoff Checklist

- 親 task と子 task を `docs/ja/todo/index.md` 上で全て `[x]` にしたら、live plan を `docs/ja/plans/archive/YYYYMMDD-<slug>.md` へ移動する。
- `docs/ja/todo/index.md` から完了 task を削除し、`docs/ja/todo/archive/YYYYMMDD.md` に完了 section を追加する。
- `docs/ja/todo/archive/index.md` に archive plan へのリンクを追加する。
- `docs/en/` mirror の plan / TODO / archive も同じ handoff を反映する。
- `plans/README.md` の active live plan 一覧から完了 plan を外し、backlog / stale-complete の分類基準が崩れていないことを確認する。
- handoff 後に `python3 tools/check_todo_priority.py` と `git diff --check` を実行する。

## 推奨テンプレート

```md
# TASK GROUP: <グループID>

最終更新: YYYY-MM-DD

関連 TODO:
- `docs/ja/todo/index.md` の `ID: ...`

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
