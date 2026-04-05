<a href="../../en/todo/julia.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Julia backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-04

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/julia/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/julia/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の Julia emitter: `src/toolchain/emit/julia/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Julia runtime: `src/runtime/julia/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-JULIA-NEW-FIXTURE-PARITY: 新規追加 fixture / stdlib の parity 確認

今セッション（2026-04-01〜05）で追加・更新した fixture と stdlib の parity を確認する。

対象: `bytes_copy_semantics`, `negative_index_comprehensive`, `negative_index_out_of_range`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`(emit-only), `math_extended`(stdlib), `os_glob_extended`(stdlib)

1. [ ] [ID: P0-JULIA-NEWFIX-S1] 上記 fixture/stdlib の parity を確認する（対象 fixture のみ実行）

### P2-JULIA-LINT: emitter hardcode lint の Julia 違反を解消する

1. [x] [ID: P2-JULIA-LINT-S1] `check_emitter_hardcode_lint.py --lang julia` で全カテゴリ 0 件になることを確認する
   - 2026-04-02: `python3 tools/check/check_emitter_hardcode_lint.py --lang julia` で全カテゴリ 0 件を確認
2. [ ] [ID: P2-JULIA-LINT-S2] `src/toolchain2/emit/julia/subset.py` の emitter guide 違反 hardcode を mapping / EAST3 metadata 正本へ移す
   - 2026-04-04: `subset.py` に attr-call method whitelist、owner type 名分岐、exception/class contract の文字列判定など guide 違反の hardcode が残っていることを再確認
   - 2026-04-04: `write_rgb_png` などの attr symbol 直書きは support checker から除去し、`resolved_runtime_call` / `runtime_call` metadata ベースで受理する方針に修正開始
   - 完了条件: `subset.py` に残る runtime/module/type 名 hardcode を `mapping.json` / `runtime_call_adapter_kind` / EAST3 metadata へ移し、`runtime_parity_check_fast.py --case-root fixture --targets julia` を PASS させたうえで guide 違反が説明可能な範囲まで減っていること
