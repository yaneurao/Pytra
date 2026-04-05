<a href="../../en/todo/dart.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Dart backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-05

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/dart/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/dart/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

完了済みタスクは [アーカイブ](archive/20260402.md) を参照。

## 参考資料

- 旧 toolchain1 の Dart emitter: `src/toolchain/emit/dart/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Dart runtime: `src/runtime/dart/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-DART-TOOLCHAIN-LEGACY: toolchain_ 依存を解消する

`src/toolchain/emit/dart/emitter.py` が旧 toolchain（`toolchain_`）の `runtime_symbol_index` を参照している。`toolchain_` は deprecated で今後削除される。

依存箇所: `from toolchain_.frontends.runtime_symbol_index import canonical_runtime_module_id, resolve_import_binding_doc`

1. [x] [ID: P0-DART-LEGACY-S1] `runtime_symbol_index` の必要な機能を toolchain 側に移行するか、emitter 内で EAST3 メタデータから直接取得するように修正する
   完了メモ: `src/toolchain/emit/dart/emitter.py` に runtime symbol index の参照ロジックを内包し、`toolchain_` 依存を除去。fixture 151/151 と stdlib 16/16 の parity を確認。
2. [x] [ID: P0-DART-LEGACY-S2] `toolchain_` への import がゼロになることを確認する
   完了メモ: `rg -n "toolchain_" src/toolchain/emit/dart -g '*.py'` が 0 件。

- なし。次の Dart タスクは新規起票待ち。
