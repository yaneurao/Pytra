<a href="../../en/todo/dart.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Dart backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-02

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/dart/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/dart/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の Dart emitter: `src/toolchain/emit/dart/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Dart runtime: `src/runtime/dart/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P1-DART-EMITTER: Dart emitter を toolchain2 に新規実装する

1. [x] [ID: P1-DART-EMITTER-S1] `src/toolchain2/emit/dart/` に Dart emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/dart/` と TS emitter を参考にする — 2026-04-02: toolchain2 側の `emit_dart_module()` 入口、Dart profile、parity 接続、smoke test を追加
2. [x] [ID: P1-DART-EMITTER-S2] `src/runtime/dart/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義 — 2026-04-02: Dart mapping.json を追加し validation 通過
3. [ ] [ID: P1-DART-EMITTER-S3] fixture 全件の Dart emit 成功を確認する — 2026-04-02: control / typing は PASS。`ok_typed_varargs_representative` は emitter 既知の未対応（typed `*args`）として parity skip に整理
4. [ ] [ID: P1-DART-EMITTER-S4] Dart runtime を toolchain2 の emit 出力と整合させる
5. [ ] [ID: P1-DART-EMITTER-S5] fixture の Dart run parity を通す（`dart run`） — 2026-04-02: 既知 unsupported 1 件を除く fixture parity は PASS
6. [x] [ID: P1-DART-EMITTER-S6] stdlib の Dart parity を通す（`--case-root stdlib`） — 2026-04-02: 16/16 PASS
7. [x] [ID: P1-DART-EMITTER-S7] sample の Dart parity を通す（`--case-root sample`） — 2026-04-02: 18/18 PASS

### P2-DART-LINT: emitter hardcode lint の Dart 違反を解消する

1. [x] [ID: P2-DART-LINT-S1] `check_emitter_hardcode_lint.py --lang dart` で全カテゴリ 0 件になることを確認する — 2026-04-02: 8/8 カテゴリ PASS
