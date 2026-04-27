<a href="../../en/todo/powershell.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — PowerShell backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-27

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

### P0-PS1-FIXTURE-PARITY-161: PowerShell fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: 153/161 PASS。FAIL は未確定で、未実行: `collections/reversed_basic`, `collections/set_update`, `collections/sorted_set`, `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/isinstance_chain_narrowing`, `typing/isinstance_union_narrowing`, `typing/nullable_dict_field`。

1. [ ] [ID: P0-FIX161-PS1-S1] 未実行 8 件を `runtime_parity_check_fast.py --targets ps1 --case-root fixture` で確定する
2. [ ] [ID: P0-FIX161-PS1-S2] fail した collection / isinstance narrowing ケースを修正し、PowerShell fixture parity 161/161 PASS を確認する

### P1-EMITTER-SELFHOST-PS1: emit/powershell/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.powershell.cli` をエントリに単独で C++ build を通す。

1. [ ] [ID: P1-EMITTER-SELFHOST-PS1-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/powershell/cli.py --target cpp -o work/selfhost/emit/powershell/` を実行し、変換が通るようにする
2. [ ] [ID: P1-EMITTER-SELFHOST-PS1-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
3. [ ] [ID: P1-EMITTER-SELFHOST-PS1-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する


### P0-PS1-NEW-FIXTURE-PARITY: 新規追加 fixture / stdlib の parity 確認

今セッション（2026-04-01〜05）で追加・更新した fixture と stdlib の parity を確認する。

対象: `bytes_copy_semantics`, `negative_index_comprehensive`, `negative_index_out_of_range`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`(emit-only), `math_extended`(stdlib), `os_glob_extended`(stdlib)

1. [ ] [ID: P0-PS1-NEWFIX-S1] 上記 fixture/stdlib の parity を確認する（対象 fixture のみ実行）
