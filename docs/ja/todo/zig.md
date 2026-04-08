<a href="../../en/todo/zig.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Zig backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-08

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/zig/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/zig/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の Zig emitter: `src/toolchain/emit/zig/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Zig runtime: `src/runtime/zig/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-ZIG-COMMON-RENDERER-EXC: `with` / 例外 lowering を CommonRenderer へ押し戻す

文脈: [docs/ja/plans/p0-zig-rs-common-renderer-exceptions.md](../plans/p0-zig-rs-common-renderer-exceptions.md)

1. [x] [ID: P0-ZIG-CREXC-S1] Rust の `with` lowering を CommonRenderer 正本へ戻し、`with_statement` / `with_context_manager` parity を維持する
2. [x] [ID: P0-ZIG-CREXC-S2] Zig の `with` lowering を CommonRenderer 正本へ戻し、`with_statement` / `with_context_manager` parity を維持する
3. [x] [ID: P0-ZIG-CREXC-S3] CommonRenderer に exception strategy hook を追加し、Rust / Zig の `try` / `raise` を hook 実装へ分離する
4. [ ] [ID: P0-ZIG-CREXC-S4] Rust / Zig の `exception_types` / `try_raise` / `exception_bare_reraise` parity を維持したまま custom lowering を縮小する
   注: `TextIOWrapper` fallback の単純撤去は不可。先に `PyFile` 実体との型 lane 整理と `with ... as name` alias hoist を CommonRenderer 側へ寄せる。

### P0-ZIG-TOOLCHAIN-LEGACY: toolchain_ 依存を解消する

`src/toolchain/emit/zig/emitter.py` が旧 toolchain（`toolchain_`）の `runtime_symbol_index` を参照している。`toolchain_` は deprecated で今後削除される。

依存箇所: `from toolchain_.frontends.runtime_symbol_index import canonical_runtime_module_id, lookup_runtime_module_symbols`

1. [ ] [ID: P0-ZIG-LEGACY-S1] `runtime_symbol_index` の必要な機能を toolchain 側に移行するか、emitter 内で EAST3 メタデータから直接取得するように修正する
2. [ ] [ID: P0-ZIG-LEGACY-S2] `toolchain_` への import がゼロになることを確認する

### P0-ZIG-NEW-FIXTURE-PARITY: 新規追加 fixture / stdlib の parity 確認

今セッション（2026-04-01〜05）で追加・更新した fixture と stdlib の parity を確認する。

対象: `bytes_copy_semantics`, `negative_index_comprehensive`, `negative_index_out_of_range`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`(emit-only), `math_extended`(stdlib), `os_glob_extended`(stdlib)

1. [ ] [ID: P0-ZIG-NEWFIX-S1] 上記 fixture/stdlib の parity を確認する（対象 fixture のみ実行）
