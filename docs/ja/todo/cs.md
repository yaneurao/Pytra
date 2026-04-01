<a href="../../en/todo/cs.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C# backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-31

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

### P3-CS-SELFHOST: C# emitter で toolchain2 を C# に変換し build を通す

文脈: [docs/ja/plans/p3-cs-selfhost.md](../plans/p3-cs-selfhost.md)

1. [ ] [ID: P3-CS-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
2. [ ] [ID: P3-CS-SELFHOST-S1] toolchain2 全 .py を C# に emit し、build が通ることを確認する
3. [ ] [ID: P3-CS-SELFHOST-S2] build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P3-CS-SELFHOST-S3] selfhost 用 C# golden を配置し、回帰テストとして維持する
5. [ ] [ID: P3-CS-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang cs --emit-target cs --case-root fixture` で fixture parity PASS
6. [ ] [ID: P3-CS-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang cs --emit-target cs --case-root sample` で sample parity PASS
