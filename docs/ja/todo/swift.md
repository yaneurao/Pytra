<a href="../../en/todo/swift.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Swift backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-03

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/swift/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/swift/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の Swift emitter: `src/toolchain/emit/swift/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Swift runtime: `src/runtime/swift/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-SWIFT-NEW-FIXTURE-PARITY: 新規追加 fixture / stdlib の parity 確認

今セッション（2026-04-01〜05）で追加・更新した fixture と stdlib の parity を確認する。

対象: `bytes_copy_semantics`, `negative_index_comprehensive`, `negative_index_out_of_range`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`(emit-only), `math_extended`(stdlib), `os_glob_extended`(stdlib)

1. [ ] [ID: P0-SWIFT-NEWFIX-S1] 上記 fixture/stdlib の parity を確認する（対象 fixture のみ実行）

### P2-SWIFT-LINT: emitter hardcode lint の Swift 違反を解消する

1. [ ] [ID: P2-SWIFT-LINT-S1] `check_emitter_hardcode_lint.py --lang swift` で全カテゴリ 0 件になることを確認する

### P20-SWIFT-SELFHOST: Swift emitter で toolchain2 を Swift に変換し build を通す

1. [ ] [ID: P20-SWIFT-SELFHOST-S0] selfhost 対象コードの型注釈補完（他言語と共通）
2. [ ] [ID: P20-SWIFT-SELFHOST-S1] toolchain2 全 .py を Swift に emit し、build が通ることを確認する
3. [ ] [ID: P20-SWIFT-SELFHOST-S2] selfhost 用 Swift golden を配置する
4. [ ] [ID: P20-SWIFT-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang swift --emit-target swift --case-root fixture` で fixture parity PASS
5. [ ] [ID: P20-SWIFT-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang swift --emit-target swift --case-root sample` で sample parity PASS
