# TASK GROUP: TG-P3-SPEC-DRAFTS

最終更新: 2026-02-23

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
- 2026-02-22: `P3-SD-01` を実施。`spec-make.md` と実装を照合し、採用済み項目（multi-file `manifest.json` 契約、`tools/build_multi_cpp.py` ビルド導線）を `spec-dev` / `spec-tools` へ移管した。`./pytra --build` / `src/pytra/cli.py` / `tools/gen_makefile_from_manifest.py` は未実装として草案側に残す方針を明記。
- 2026-02-23: `P3-SD-02` を実施。`spec-template.md` と実装を照合し、採用/保留/非採用を区分した。採用項目（`TypeVar` は最小 shim）を `spec-pylib-modules` へ明文化し、記法の確定表現（「採用」）は非採用として「候補」へ修正した。

## P3-SD-01 照合結果（`spec-make.md`）

採用して既存仕様へ移管した節:
- §7 `manifest.json` 入力仕様
  - 移管先: `docs-jp/spec/spec-dev.md`（`3.0 複数ファイル出力と manifest/build`）
- §6 C++ build フロー（実装済み部分のみ）
  - 移管先: `docs-jp/spec/spec-dev.md`（`tools/build_multi_cpp.py` フロー）
- build 補助スクリプトの位置づけ
  - 移管先: `docs-jp/spec/spec-tools.md`（`tools/build_multi_cpp.py`, `tools/verify_multi_file_outputs.py`）

保留（草案維持）とした節:
- §4〜§5（`./pytra` ランチャー、`src/pytra/cli.py`、`--target cpp --build`）
- §8〜§10（`tools/gen_makefile_from_manifest.py` 前提の Makefile 生成契約）
- §11（段階導入のうち未実装フェーズ）

## P3-SD-02 照合結果（`spec-template.md`）

採用して既存仕様へ移管した節:
- §15 のうち `TypeVar` の現状実装（runtime shim）
  - 移管先: `docs-jp/spec/spec-pylib-modules.md`
  - 根拠: `src/pytra/std/typing.py` の `TypeVar(name: str) -> str`

保留（草案維持）とした節:
- §1〜§14（template 専用構文、実体化、エラー契約、生成量ガード、検証要件）
- §16（デコレータ連記記法そのものは候補として保持）

非採用とした節/表現:
- §16 の「`.py` 記法（採用）」という確定表現
  - 対応: 見出しを「`.py` 記法（候補）」へ変更
  - 理由: 現状 parser は `@dataclass` 以外のトップレベル decorator を template 機能として解釈しない。
