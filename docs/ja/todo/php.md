<a href="../../en/todo/php.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — PHP backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-27

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/php/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/php/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
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

### P0-PHP-FIXTURE-PARITY-161: PHP fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: 154/161 PASS。FAIL: `collections/reversed_basic`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`。未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field`。

1. [x] [ID: P0-FIX161-PHP-S1] 未実行 3 件を `runtime_parity_check_fast.py --targets php --case-root fixture` で確定し、fail なら分類へ追加する
2. [x] [ID: P0-FIX161-PHP-S2] reversed / trait / typed varargs の fail を解消し、PHP fixture parity 161/161 PASS を確認する


### P1-HOST-CPP-EMITTER-PHP: C++ emitter を php で host する

C++ emitter（`toolchain.emit.cpp.cli`、16 モジュール）を php に変換し、変換された emitter が C++ コードを正しく生成できることを確認する。C++ emitter の source は selfhost-safe 化済み。

1. [ ] [ID: P1-HOST-CPP-EMITTER-PHP-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target php -o work/selfhost/host-cpp/php/` で変換 + build を通す
2. [ ] [ID: P1-HOST-CPP-EMITTER-PHP-S2] php 版 C++ emitter で fixture manifest を処理し、Python 版 emitter と parity 一致を確認する

### P1-EMITTER-SELFHOST-PHP: emit/php/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.php.cli` をエントリに単独で C++ build を通す。

1. [ ] [ID: P1-EMITTER-SELFHOST-PHP-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/php/cli.py --target cpp -o work/selfhost/emit/php/` を実行し、変換が通るようにする
2. [ ] [ID: P1-EMITTER-SELFHOST-PHP-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
3. [ ] [ID: P1-EMITTER-SELFHOST-PHP-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する


### P20-PHP-SELFHOST: PHP emitter で toolchain2 を PHP に変換し実行できるようにする

1. [ ] [ID: P20-PHP-SELFHOST-S0] selfhost 対象コードの型注釈補完（他言語と共通）
2. [ ] [ID: P20-PHP-SELFHOST-S1] toolchain2 全 .py を PHP に emit し、実行できることを確認する
3. [ ] [ID: P20-PHP-SELFHOST-S2] selfhost 用 PHP golden を配置する
4. [ ] [ID: P20-PHP-SELFHOST-S3] `run_selfhost_parity.py --selfhost-lang php --emit-target php --case-root fixture` で fixture parity PASS
5. [ ] [ID: P20-PHP-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang php --emit-target php --case-root sample` で sample parity PASS
