<a href="../../en/todo/powershell.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — PowerShell backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-05-04

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

1. [x] [ID: P0-FIX161-PS1-S1] 未実行 8 件を `runtime_parity_check_fast.py --targets ps1 --case-root fixture` で確定する
2. [x] [ID: P0-FIX161-PS1-S2] fail した collection / isinstance narrowing ケースを修正し、PowerShell fixture parity 161/161 PASS を確認する


### P1-HOST-CPP-EMITTER-PS1: C++ emitter を powershell で host する

C++ emitter（`toolchain.emit.cpp.cli`、16 モジュール）を powershell に変換し、変換された emitter が C++ コードを正しく生成できることを確認する。C++ emitter の source は selfhost-safe 化済み。

1. [x] [ID: P1-HOST-CPP-EMITTER-PS1-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target powershell -o work/selfhost/host-cpp/powershell/` で変換 + build を通す
   - 完了: 2026-05-04 `tools/run/run_emitter_host_parity.py --host-lang powershell --hosted-emitter cpp --case-root fixture --timeout-sec 3600` の host build 段階で PowerShell 変換 PASS。実行環境は Dockerfile 仕様の `/tmp/pwsh` fallback を runner 側で解決。
2. [x] [ID: P1-HOST-CPP-EMITTER-PS1-S2] `python3 tools/run/run_emitter_host_parity.py --host-lang powershell --hosted-emitter cpp --case-root fixture` で C++ emitter host parity PASS を確認する（結果は `.parity-results/emitter_host_powershell.json` に自動書き込み）
   - 完了: 2026-05-04 `PYTHONPYCACHEPREFIX=work/tmp/pycache timeout 3600s python3 tools/run/run_emitter_host_parity.py --host-lang powershell --hosted-emitter cpp --case-root fixture --timeout-sec 3600` で PASS。`.parity-results/emitter_host_powershell.json` は `parity_status: ok`。

### P1-EMITTER-SELFHOST-PS1: emit/powershell/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.powershell.cli` をエントリに単独で C++ build を通す。

1. [x] [ID: P1-EMITTER-SELFHOST-PS1-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/powershell/cli.py --target cpp -o work/selfhost/emit/powershell/` を実行し、変換が通るようにする
   - 完了: 2026-04-29 `rm -rf work/selfhost/emit/powershell && timeout 180s python3 src/pytra-cli.py -build src/toolchain/emit/powershell/cli.py --target cpp -o work/selfhost/emit/powershell/` で変換 PASS。26 files を出力。
2. [ ] [ID: P1-EMITTER-SELFHOST-PS1-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
   - 進捗: 2026-04-29 `g++ -std=c++20 -O0` は未 PASS。先頭ブロッカーは `frozenset[str]` の C++ 型未生成、`run_emit_cli` への `list<str>` vs `Object<list<str>>` 不一致、`JsonVal` の型絞り不足（`JsonVal > double` / `JsonVal` を `str` 引数へ渡す等）、`str.rsplit` 未対応。
3. [ ] [ID: P1-EMITTER-SELFHOST-PS1-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する


### P0-PS1-NEW-FIXTURE-PARITY: 新規追加 fixture / stdlib の parity 確認

今セッション（2026-04-01〜05）で追加・更新した fixture と stdlib の parity を確認する。

対象: `bytes_copy_semantics`, `negative_index_comprehensive`, `negative_index_out_of_range`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`(emit-only), `math_extended`(stdlib), `os_glob_extended`(stdlib)

1. [ ] [ID: P0-PS1-NEWFIX-S1] 上記 fixture/stdlib の parity を確認する（対象 fixture のみ実行）
