<a href="../../en/todo/zig.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Zig backend

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

- Zig emitter: `src/toolchain/emit/zig/`
- TS emitter（参考実装）: `src/toolchain/emit/ts/`
- Zig runtime: `src/runtime/zig/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-ZIG-FIXTURE-PARITY-161: Zig fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: 150/161 PASS。FAIL: `control/finally`, `signature/ok_typed_varargs_representative`, `typing/bytearray_basic`, `typing/callable_optional_none`, `typing/isinstance_narrowing`, `typing/isinstance_union_narrowing`, `typing/union_basic`, `typing/union_dict_items`。未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field`。spot check では `exception_style` profile mismatch も観測済み。

1. [x] [ID: P0-FIX161-ZIG-S1] 未実行 3 件を `runtime_parity_check_fast.py --targets zig --case-root fixture` で確定し、fail なら分類へ追加する
2. [x] [ID: P0-FIX161-ZIG-S2] exception_style profile mismatch、finally、typed varargs、bytearray、callable optional、isinstance、union の fail を解消し、Zig fixture parity 161/161 PASS を確認する


### P1-HOST-CPP-EMITTER-ZIG: C++ emitter を zig で host する

C++ emitter（`toolchain.emit.cpp.cli`、16 モジュール）を zig に変換し、変換された emitter が C++ コードを正しく生成できることを確認する。C++ emitter の source は selfhost-safe 化済み。

1. [ ] [ID: P1-HOST-CPP-EMITTER-ZIG-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target zig -o work/selfhost/host-cpp/zig/` で変換 + build を通す
   - 進捗: 2026-04-29 に実行し、変換前に FAIL。`--target` の available 一覧には `zig` が出るが、実際には `error: unsupported target: zig (available: cpp, go, rs, cs, java, scala, kotlin, ts, js, nim, swift, julia, powershell, zig)` で停止する。target wiring が一覧と実行 dispatch で不整合。
   - 進捗: 2026-04-29 `--target zig` の build dispatch を subprocess emitter へ再接続し、runtime east キャッシュ生成後に上記 exact command を再実行。unsupported target は解消し、30 modules link 後に Zig emitter 側の `RuntimeError: lang=zig unsupported stmt kind: TupleUnpack` で停止するところまで進んだ。
2. [ ] [ID: P1-HOST-CPP-EMITTER-ZIG-S2] C++ emitter host parity PASS を確認し、結果を `.parity-results/emitter_host_zig.json` に書き込む（`gen_backend_progress.py` で emitter host マトリクスに反映される）
   - 進捗: 2026-04-29 時点では S1 が変換前に失敗するため未実行。参考として `python3 tools/run/run_selfhost_parity.py --selfhost-lang zig --emit-target cpp --case-root fixture` も実行し、同じ `--target zig` unsupported を `.parity-results/selfhost_zig.json` に build_failed として記録済み。

### P1-EMITTER-SELFHOST-ZIG: emit/zig/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.zig.cli` をエントリに単独で C++ build を通す。

1. [ ] [ID: P1-EMITTER-SELFHOST-ZIG-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/zig/cli.py --target cpp -o work/selfhost/emit/zig/` を実行し、変換が通るようにする
   - 進捗: 2026-04-29 に実行し、変換は未 PASS。`rm -rf work/selfhost/emit/zig && timeout 180s python3 src/pytra-cli.py -build src/toolchain/emit/zig/cli.py --target cpp -o work/selfhost/emit/zig/` は parse/resolve 後に `unsupported_syntax: starred call arg requires fixed tuple, got unknown` で失敗する。
2. [ ] [ID: P1-EMITTER-SELFHOST-ZIG-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
3. [ ] [ID: P1-EMITTER-SELFHOST-ZIG-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する
