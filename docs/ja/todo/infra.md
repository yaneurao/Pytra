<a href="../../en/todo/infra.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — インフラ・ツール・仕様

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-03

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。

完了済みタスクは [アーカイブ](archive/20260403.md) を参照。

## 未完了タスク

### P10-LEGACY-TOOLCHAIN-REMOVAL: 旧 toolchain + pytra-cli.py を削除する

文脈: [docs/ja/plans/p10-legacy-toolchain-removal.md](../plans/p10-legacy-toolchain-removal.md)

全言語の toolchain2 emitter 実装（各言語の P1-*-EMITTER-S1）が完了した時点で、旧パイプラインを削除する。

削除対象:
- `src/toolchain/`（旧 emitter、旧 compile、旧 frontends、旧 misc）
- `src/pytra-cli.py`（旧 CLI。`src/pytra-cli2.py` が正本）
- 旧パイプラインを参照している test/spec/docs の記述

前提条件（全て S1 完了が必要）:
- [x] C++ / Rust / C# / TS-JS / Go / Java / Ruby / Lua / PHP / Nim / Dart
- [x] Scala / Kotlin（S1-S2 完了）
- [x] Swift（S1-S2 完了）
- [ ] Julia（S1 進行中、fixture 85/145）
- [ ] Zig（S1 未完了）
- [ ] PowerShell（S1 未着手）

1. [ ] [ID: P10-LEGACY-RM-S1] 全言語の P1-*-EMITTER-S1 完了を確認する（ゲート）
2. [ ] [ID: P10-LEGACY-RM-S2] `src/toolchain/` を削除する
3. [ ] [ID: P10-LEGACY-RM-S3] `src/pytra-cli.py` を削除し、`src/pytra-cli2.py` を `src/pytra-cli.py` にリネームする
4. [ ] [ID: P10-LEGACY-RM-S4] spec / tutorial / README の旧パイプライン参照を更新する
5. [ ] [ID: P10-LEGACY-RM-S5] `run_local_ci.py` 等のツールから旧パイプライン参照を削除する

### P20-DATA-DRIVEN-TESTS: パイプライン系テストのデータ駆動化

文脈: [docs/ja/plans/plan-emit-expect-data-driven-tests.md](../plans/plan-emit-expect-data-driven-tests.md)

ステータス: **保留中** — 既存テストが他 agent により変更中のため、安定してから Phase 1 に着手する。

`tools/unittest/` の 267 スクリプトのうち ~80件はパイプライン系（入力→parse/resolve/lower/emit→期待出力）で、JSON データで定義できる。残り ~190件（tooling/selfhost/link 等）は Python テストとして残す。

**Phase 1: emit 層で方式を確立**

1. [ ] [ID: P20-DDT-S1] `test/cases/emit/cpp/` に JSON テストケース 5〜10 件を作成する
2. [ ] [ID: P20-DDT-S2] `tools/unittest/test_emit_cases.py` を実装する（pytest parametrize で JSON 走査）
3. [ ] [ID: P20-DDT-S3] `test_common_renderer.py` の対応テストを JSON に移行し、元メソッドを削除する

**Phase 2: パイプライン層に横展開**

4. [ ] [ID: P20-DDT-S4] `test/cases/{east1,east2,east3}/` に JSON テストケースを作成する
5. [ ] [ID: P20-DDT-S5] `tools/unittest/test_pipeline_cases.py` を実装する
6. [ ] [ID: P20-DDT-S6] `tools/unittest/ir/` と `tools/unittest/toolchain2/` の対応テストを段階的に JSON に移行する

**Phase 3: smoke テストの統合**

7. [ ] [ID: P20-DDT-S7] `tools/unittest/emit/<lang>/test_py2*_smoke.py` (~20件) を JSON に移行する
8. [ ] [ID: P20-DDT-S8] `tools/unittest/common/test_pylib_*.py` (~10件) を JSON に移行する
9. [ ] [ID: P20-DDT-S9] 空になったスクリプトを削除する

### 保留中タスク

- P20-INT32 は [plans/p4-int32-default.md](../plans/p4-int32-default.md) に保留中。再開時にここへ戻す。
