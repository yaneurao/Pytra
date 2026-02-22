# TASK GROUP: TG-P3-SPEC-DRAFTS

最終更新: 2026-02-22

関連 TODO:
- `docs-jp/todo.md` の `ID: P3-SD-01`
- `docs-jp/todo.md` の `ID: P3-SD-02`

背景:
- `spec-make.md` と `spec-template.md` は一時的にリポジトリ直下へ置かれていたが、仕様書群としては `docs-jp/spec/` 配下で管理するのが一貫する。
- 2文書は現時点で「採用済み仕様」ではなく、実装との差分確認と採否整理が未完了の草案を含む。

目的:
- `docs-jp/spec/spec-make.md` と `docs-jp/spec/spec-template.md` の扱いを低優先バックログとして管理し、必要な仕様への統合作業を段階的に進める。

対象:
- 各文書の内容を実装現状と照合し、採用/保留/削除候補を明示する。
- 採用する内容は既存の正規仕様（`spec-runtime`, `spec-user`, `spec-east`, `spec-tools`, `how-to-use` など）へ移管する。
- `docs/` 側の翻訳ミラー同期が必要かを判断し、必要なら TODO へ分解する。

非対象:
- template 機能や新規 CLI の実装着手。
- 既存仕様を一括で書き換える大規模再編。

受け入れ基準:
- 2文書それぞれで「どの節をどこへ統合するか」が明確になっている。
- 実装と矛盾する記述を放置しない状態になる。
- 低優先タスクとして継続管理できる粒度（ID 単位）に分解されている。

決定ログ:
- 2026-02-22: `spec-make.md` / `spec-template.md` を `docs-jp/spec/` へ移動し、低優先 TODO (`P3-SD-01`, `P3-SD-02`) を追加する方針を確定。
