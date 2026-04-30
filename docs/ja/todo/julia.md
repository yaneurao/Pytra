<a href="../../en/todo/julia.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Julia backend

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

- Julia emitter: `src/toolchain/emit/julia/`
- TS emitter（参考実装）: `src/toolchain/emit/ts/`
- Julia runtime: `src/runtime/julia/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-JULIA-FIXTURE-PARITY-161: Julia fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: 156/161 PASS。FAIL: `collections/reversed_basic`, `signature/ok_typed_varargs_representative`。未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field`。

1. [x] [ID: P0-FIX161-JULIA-S1] 未実行 3 件を `runtime_parity_check_fast.py --targets julia --case-root fixture` で確定し、fail なら分類へ追加する
2. [x] [ID: P0-FIX161-JULIA-S2] reversed / typed varargs の fail を解消し、Julia fixture parity 161/161 PASS を確認する


### P1-HOST-CPP-EMITTER-JULIA: C++ emitter を julia で host する

C++ emitter（`toolchain.emit.cpp.cli`、16 モジュール）を julia に変換し、変換された emitter が C++ コードを正しく生成できることを確認する。C++ emitter の source は selfhost-safe 化済み。

1. [ ] [ID: P1-HOST-CPP-EMITTER-JULIA-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target julia -o work/selfhost/host-cpp/julia/` で変換 + build を通す
   - 進捗: 2026-04-29 に実行し、変換段階で FAIL。`build: parsed/resolved/compiled/optimized/linked 18 files / 33 modules` までは通るが、Julia emitter が `julia subset: unsupported expr kind: Name` で停止する。発生箇所は `src/toolchain/emit/julia/subset.py` の class method 内 return 式 render。
2. [ ] [ID: P1-HOST-CPP-EMITTER-JULIA-S2] `python3 tools/run/run_emitter_host_parity.py --host-lang julia --hosted-emitter cpp --case-root fixture` で C++ emitter host parity PASS を確認する（結果は `.parity-results/emitter_host_julia.json` に自動書き込み）
   - 進捗: 2026-04-29 時点では S1 が変換失敗のため未実行。参考として `PATH=/usr/local/bin:... python3 tools/run/run_selfhost_parity.py --selfhost-lang julia --emit-target cpp --case-root fixture` も実行し、同じ `unsupported expr kind: Name` を `.parity-results/selfhost_julia.json` に build_failed として記録済み。

### P1-EMITTER-SELFHOST-JULIA: emit/julia/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.julia.cli` をエントリに単独で C++ build を通す。

1. [x] [ID: P1-EMITTER-SELFHOST-JULIA-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/julia/cli.py --target cpp -o work/selfhost/emit/julia/` を実行し、変換が通るようにする
   - 2026-04-16: 完了。13 module を parse→resolve→compile→optimize→link→emit まで通し、42 本の C++ を `work/selfhost/emit/julia/` に生成。
   - 付随: linker の `_attach_method_signature_hints` / `_attach_function_signature_hints` で相互参照メソッドの deep-copy が指数的に肥大する問題を発見。snapshot 化して修正。`julia/subset.py` 単体で 5.2GB になっていた linked east3 が 13MB に落ち着いた（全 backend 共通）。
   - 付随: `toolchain/link/linker.py` に `from pytra.typing import cast` を再導入（他 instance の diff で消えていた）。
   - 付随: selfhost source 側の調整: `julia/subset.py` の starred expr と `collections.abc` を除去、`common/cli_runner.py` で Callable alias を PEP 695 形式に移行し、empty-dict 代入を JsonVal で通る形に書き直し。
2. [x] [ID: P1-EMITTER-SELFHOST-JULIA-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
   - 2026-04-28: `python3 src/pytra-cli.py -build src/toolchain/emit/julia/cli.py --target cpp -o work/selfhost/emit/julia/` 後、生成 C++ と C++ runtime を `g++ -std=c++20 -O0` でリンクし、`work/selfhost/emit/julia/emitter_julia_cpp` 生成まで確認。
3. [x] [ID: P1-EMITTER-SELFHOST-JULIA-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する
   - 2026-04-28: `test/fixture/source/py/core/add.py` から生成した `work/tmp/build_add/linked/manifest.json` を対象に、`PYTHONPATH=src python3 -m toolchain.emit.julia.cli ...` と `work/selfhost/emit/julia/emitter_julia_cpp ...` の出力を `diff -ru work/selfhost/parity/julia/python_cli work/selfhost/parity/julia/compiled` で比較し一致を確認。
