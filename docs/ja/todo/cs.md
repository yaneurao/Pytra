<a href="../../en/todo/cs.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C# backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-30

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の C# emitter: `src/toolchain/emit/cs/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の C# runtime: `src/runtime/cs/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P1-CS-EMITTER: C# emitter を toolchain2 に新規実装する

文脈: [docs/ja/plans/p1-cs-emitter.md](../plans/p1-cs-emitter.md)

1. [x] [ID: P1-CS-EMITTER-S1] `src/toolchain2/emit/cs/` に C# emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/cs/` と TS emitter（`src/toolchain2/emit/ts/`）を参考にする。C# 固有のノード（namespace、using、property、LINQ 等）だけ override として残す（2026-03-30: `emit_cs_module()`、`types.py`、`toolchain2/emit/profiles/cs.json`、`pytra-cli2 --target cs` の emit/build 経路を追加）
2. [x] [ID: P1-CS-EMITTER-S2] `src/runtime/cs/mapping.json` を作成し、runtime_call の写像を定義する。`types` テーブルも含める（spec-runtime-mapping.md §7）。`env.target` 必須エントリも忘れないこと（2026-03-30: `src/runtime/cs/mapping.json` を追加し、`env.target`、主要 built-in/runtime call、`types`、`implicit_promotions` を定義）
3. [ ] [ID: P1-CS-EMITTER-S3] fixture 全件の C# emit 成功を確認する（`runtime_parity_check_fast.py --targets cs` の既存経路で確認する。2026-03-30: `--category core` は 22/22 pass）
4. [ ] [ID: P1-CS-EMITTER-S4] C# runtime を toolchain2 の emit 出力と整合させる（旧 runtime の引き継ぎ or 再実装）
5. [ ] [ID: P1-CS-EMITTER-S5] fixture + sample の C# compile + run parity を通す（`mcs` + `mono` または `dotnet run`）
6. [ ] [ID: P1-CS-EMITTER-S6] stdlib の C# parity を通す（`--case-root stdlib`）

### P2-CS-LINT-FIX: C# emitter のハードコード違反を修正する

仕様: [spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1, §7

1. [ ] [ID: P2-CS-LINT-S1] `check_emitter_hardcode_lint.py` で C# の違反が 0 件になることを確認する

### P3-CS-SELFHOST: C# emitter で toolchain2 を C# に変換し build を通す

文脈: [docs/ja/plans/p3-cs-selfhost.md](../plans/p3-cs-selfhost.md)

1. [ ] [ID: P3-CS-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
2. [ ] [ID: P3-CS-SELFHOST-S1] toolchain2 全 .py を C# に emit し、build が通ることを確認する
3. [ ] [ID: P3-CS-SELFHOST-S2] build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P3-CS-SELFHOST-S3] selfhost 用 C# golden を配置し、回帰テストとして維持する
