<a href="../../en/todo/nim.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Nim backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-02

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/nim/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/nim/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の Nim emitter: `src/toolchain/emit/nim/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Nim runtime: `src/runtime/nim/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P1-NIM-EMITTER: Nim emitter を toolchain2 に新規実装する

文脈: [docs/ja/plans/p1-nim-emitter.md](../plans/p1-nim-emitter.md)

1. [x] [ID: P1-NIM-EMITTER-S1] `src/toolchain2/emit/nim/` に Nim emitter を新規実装する — CommonRenderer + override 構成。emitter.py, types.py, __init__.py, profiles/nim.json を作成。完了: 2026-03-31
2. [x] [ID: P1-NIM-EMITTER-S2] `src/runtime/nim/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions`, `skip_modules` を定義。完了: 2026-03-31
3. [x] [ID: P1-NIM-EMITTER-S3] fixture 全件の Nim emit 成功を確認する — 129/131 成功（残り2件は parser 側の trait 未対応）。完了: 2026-03-31
4. [x] [ID: P1-NIM-EMITTER-S4] Nim runtime を toolchain2 の emit 出力と整合させる — py_print, str methods, container helpers, assert framework 等を追加。完了: 2026-03-31
5. [ ] [ID: P1-NIM-EMITTER-S5] fixture + sample の Nim compile + run parity を通す（`nim c -r`）— Nim コンパイラ要
6. [ ] [ID: P1-NIM-EMITTER-S6] stdlib の Nim parity を通す（`--case-root stdlib`）— Nim コンパイラ要

### P2-NIM-LINT-FIX: Nim emitter のハードコード違反を修正する

1. [x] [ID: P2-NIM-LINT-S1] `check_emitter_hardcode_lint.py` で Nim の違反が 0 件になることを確認する — 完了: 2026-04-02 (`--lang nim --include-runtime --no-write` で 0 件)

### P20-NIM-SELFHOST: Nim emitter で toolchain2 を Nim に変換し実行できるようにする

1. [ ] [ID: P20-NIM-SELFHOST-S0] selfhost 対象コードの型注釈補完（他言語と共通）
2. [ ] [ID: P20-NIM-SELFHOST-S1] toolchain2 全 .py を Nim に emit し、compile + 実行できることを確認する
3. [ ] [ID: P20-NIM-SELFHOST-S2] selfhost 用 Nim golden を配置する
4. [ ] [ID: P20-NIM-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang nim --emit-target nim --case-root fixture` で fixture parity PASS
5. [ ] [ID: P20-NIM-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang nim --emit-target nim --case-root sample` で sample parity PASS
