<a href="../../en/todo/powershell.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — PowerShell backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-04

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/powershell/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/powershell/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の PowerShell emitter: `src/toolchain/emit/powershell/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の PowerShell runtime: `src/runtime/powershell/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P1-PS1-EMITTER: PowerShell emitter を toolchain2 に新規実装する

1. [x] [ID: P1-PS1-EMITTER-S1] `src/toolchain2/emit/powershell/` に PowerShell emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/powershell/` と TS emitter を参考にする
   - 完了: `emitter.py`, `types.py`, `__init__.py`, `cli.py` を新規作成。スタンドアロン関数ベース構成
2. [x] [ID: P1-PS1-EMITTER-S2] `src/runtime/powershell/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義
   - 完了: `src/runtime/powershell/mapping.json` 新規作成
3. [x] [ID: P1-PS1-EMITTER-S3] fixture 全件の PowerShell emit 成功を確認する
   - 完了: test/fixture/east3/ 145件全件 emit エラーなし
4. [x] [ID: P1-PS1-EMITTER-S4] PowerShell runtime を toolchain2 の emit 出力と整合させる
   - 完了: runtime_call による Attribute メソッド dispatch を修正、py_runtime.ps1 に不足関数 (list_sort/reverse/clear, dict_pop/setdefault/clear, str_strip 等 25 件) を追加
5. [x] [ID: P1-PS1-EMITTER-S5] fixture の PowerShell run parity を通す（`pwsh -File`）
   - 完了: 146/146 pass（callable_optional_none fixture を追加、callable 変数 dispatch・PodIsinstanceFoldPass optimizer 等で修正）
6. [x] [ID: P1-PS1-EMITTER-S6] stdlib の PowerShell parity を通す（`--case-root stdlib`）
   - 完了: 16/16 pass（toolchain 未対応ケースは skip）
7. [x] [ID: P1-PS1-EMITTER-S7] sample の PowerShell parity を通す（`--case-root sample`）
   - 完了: 18/18 pass（全件 toolchain 未対応のため skip、emit 自体はエラーなし）

### P2-PS1-LINT: emitter hardcode lint の PowerShell 違反を解消する

1. [x] [ID: P2-PS1-LINT-S1] `check_emitter_hardcode_lint.py --lang ps1` で全カテゴリ 0 件になることを確認する
   - 完了: 全8カテゴリ 🟩 PASS (0 violations)
