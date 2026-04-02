<a href="../../en/todo/php.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — PHP backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-02

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の PHP emitter: `src/toolchain/emit/php/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の PHP runtime: `src/runtime/php/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P1-PHP-EMITTER: PHP emitter を toolchain2 に新規実装する

文脈: [docs/ja/plans/p1-php-emitter.md](../plans/p1-php-emitter.md)

1. [x] [ID: P1-PHP-EMITTER-S1] `src/toolchain2/emit/php/` に PHP emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/php/` と TS emitter を参考にする。PHP 固有（`$` 変数、`->` アクセス、`array()` 等）だけ override — 完了: emitter.py, types.py, profiles/php.json を作成
2. [x] [ID: P1-PHP-EMITTER-S2] `src/runtime/php/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義 — 完了
3. [x] [ID: P1-PHP-EMITTER-S3] fixture 全件の PHP emit 成功を確認する — 完了: 1362 件全件 emit 成功（エラー 0 件）
4. [x] [ID: P1-PHP-EMITTER-S4] PHP runtime を toolchain2 の emit 出力と整合させる — 完了: 既存 PHP runtime と整合済み、parity check に PHP target を追加
5. [ ] [ID: P1-PHP-EMITTER-S5] fixture + sample の PHP run parity を通す（`php`） — 進捗: fixture `140/140 PASS`。sample は helper callable / `break` / runtime helper 不足を解消し、`18_mini_language_interpreter` などの run failure を除去。残りは主に PNG/GIF artifact mismatch
6. [x] [ID: P1-PHP-EMITTER-S6] stdlib の PHP parity を通す（`--case-root stdlib`） — 完了: `runtime_parity_check_fast.py --targets php --case-root stdlib --east3-opt-level 1` で `16/16 PASS`

### P2-PHP-LINT-FIX: PHP emitter のハードコード違反を修正する

1. [x] [ID: P2-PHP-LINT-S1] `check_emitter_hardcode_lint.py` で PHP の違反が 0 件になることを確認する — 完了: `check_emitter_hardcode_lint.py --lang php` で 0 件

### P20-PHP-SELFHOST: PHP emitter で toolchain2 を PHP に変換し実行できるようにする

1. [ ] [ID: P20-PHP-SELFHOST-S0] selfhost 対象コードの型注釈補完（他言語と共通）
2. [ ] [ID: P20-PHP-SELFHOST-S1] toolchain2 全 .py を PHP に emit し、実行できることを確認する
3. [ ] [ID: P20-PHP-SELFHOST-S2] selfhost 用 PHP golden を配置する
4. [ ] [ID: P20-PHP-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang php --emit-target php --case-root fixture` で fixture parity PASS
5. [ ] [ID: P20-PHP-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang php --emit-target php --case-root sample` で sample parity PASS
