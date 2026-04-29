<a href="../../en/todo/dart.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Dart backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-29

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- Dart emitter: `src/toolchain/emit/dart/`
- TS emitter（参考実装）: `src/toolchain/emit/ts/`
- Dart runtime: `src/runtime/dart/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-DART-FIXTURE-PARITY-161: Dart fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: 148/161 PASS。FAIL: `collections/reversed_basic`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `strings/str_methods_extended`, `typing/int8`, `typing/integer_promotion`, `typing/isinstance_pod_exact`, `typing/str_repr_containers`, `typing/union_return_errorcheck`。未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field`。

1. [x] [ID: P0-FIX161-DART-S1] 未実行 3 件を `runtime_parity_check_fast.py --targets dart --case-root fixture` で確定し、fail なら分類へ追加する
2. [x] [ID: P0-FIX161-DART-S2] reversed / trait / typed varargs / string methods / int promotion / isinstance / union runtime の fail を解消し、Dart fixture parity 161/161 PASS を確認する


### P1-HOST-CPP-EMITTER-DART: C++ emitter を dart で host する

C++ emitter（`toolchain.emit.cpp.cli`、16 モジュール）を dart に変換し、変換された emitter が C++ コードを正しく生成できることを確認する。C++ emitter の source は selfhost-safe 化済み。

1. [ ] [ID: P1-HOST-CPP-EMITTER-DART-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target dart -o work/selfhost/host-cpp/dart/` で変換 + build を通す
   - 進捗: 2026-04-29 現在、このコマンドは `error: unsupported target: dart` で開始前に失敗する。`pytra-cli.py -build` の target registry に dart を再接続してから、C++ emitter host 変換を再実行する。
   - 進捗: 2026-04-29 `--target dart` の build dispatch を subprocess emitter へ再接続し、runtime east キャッシュ生成後に上記 exact command を再実行。unsupported target は解消し、30 modules link 後に Dart emitter 側の `RuntimeError: lang=dart unsupported stmt kind: TupleUnpack` で停止するところまで進んだ。
2. [ ] [ID: P1-HOST-CPP-EMITTER-DART-S2] C++ emitter host parity PASS を確認し、結果を `.parity-results/emitter_host_dart.json` に書き込む（`gen_backend_progress.py` で emitter host マトリクスに反映される）

### P1-EMITTER-SELFHOST-DART: emit/dart/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.dart.cli` をエントリに単独で C++ build を通す。

1. [ ] [ID: P1-EMITTER-SELFHOST-DART-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/dart/cli.py --target cpp -o work/selfhost/emit/dart/` を実行し、変換が通るようにする
   - 進捗: 2026-04-29 に実行し、変換は未 PASS。`rm -rf work/selfhost/emit/dart && timeout 180s python3 src/pytra-cli.py -build src/toolchain/emit/dart/cli.py --target cpp -o work/selfhost/emit/dart/` は `error: build failed: expected ) but got "var __out: [Any] = []; "` で失敗する。
2. [ ] [ID: P1-EMITTER-SELFHOST-DART-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
3. [ ] [ID: P1-EMITTER-SELFHOST-DART-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する
