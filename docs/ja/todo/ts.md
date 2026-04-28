<a href="../../en/todo/ts.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — TypeScript / JavaScript backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-27 (TS担当)

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 現状

- toolchain2 に TS/JS emitter は未実装（`src/toolchain2/emit/ts/`, `src/toolchain2/emit/js/` が存在しない）
- runtime は `src/runtime/ts/`, `src/runtime/js/` に存在する（旧 toolchain1 時代の実装）
- 旧 toolchain1 の TS/JS emitter は `src/toolchain/emit/ts/`, `src/toolchain/emit/js/` に存在するが、toolchain2 への移行が必要

## 設計方針

TypeScript emitter を先に実装し、JavaScript は型注釈の出力を抑制するフラグで対応する。

- EAST3 には完全な型情報がある。TS emitter はこれを素直に型注釈付きで出力する
- JS モードは同じ emitter で型注釈を省略するだけ（`--strip-types` または `--target js`）
- emitter を2本作る必要はない。TS emitter 1本 + フラグで JS/TS の両方をカバーする

## 未完了タスク

### P0-TSJS-FIXTURE-PARITY-161: TypeScript / JavaScript fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: JS 151/161 PASS、TS 150/161 PASS。JS FAIL: `collections/dict_mutation_methods`, `collections/list_mutation_methods`, `collections/reversed_basic`, `collections/set_mutation_methods`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`。TS はこれに `typing/bytearray_basic` が加わる。共通未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field`。

1. [x] [ID: P0-FIX161-TSJS-S1] 未実行 3 件を `runtime_parity_check_fast.py --targets js,ts --case-root fixture` で確定し、fail なら分類へ追加する
2. [x] [ID: P0-FIX161-TSJS-S2] mutation methods / reversed / trait / typed varargs / bytearray の fail を解消し、JS と TS の fixture parity 161/161 PASS を確認する

### P1-EMITTER-SELFHOST-TS: emit/ts/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.ts.cli` をエントリに単独で C++ build を通す。js は ts と同じ emitter (strip_types フラグ) のため、ts で完了すれば js もカバーされる。

1. [x] [ID: P1-EMITTER-SELFHOST-TS-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/ts/cli.py --target cpp -o work/selfhost/emit/ts/` を実行し、変換が通るようにする
   - 2026-04-16: ts/emitter.py の `object` 型注釈（`_wrap_pyprint_arg`, `_is_none_constant`, `_get_ts_rt`, `_elem_to_ts_type`, `_union_subscript_members`, `_container_type_alias`）を `JsonVal` に変更。ts/cli.py を自己完結化し、typing.Callable を含む cli_runner.py に依存しないよう parse/load/module_id ロジックをインライン化。38 cpp ファイルの emit が通った。
2. [ ] [ID: P1-EMITTER-SELFHOST-TS-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
   - 2026-04-16: 現状 blocker は emit/common/code_emitter.py に残る cpp emitter 側の未対応パターン。具体的には (a) `for alias in dict_var:` を subscript `dict[pair]` と誤変換、(b) `__file__` 参照が C++ `__FILE__` に解決されない、(c) `isinstance(info, dict)` narrowing 後の `info.get("module")` 型推論が JsonVal のまま。いずれも cpp emitter 側の改修が必要で、P20-CPP-SELFHOST (cpp.md) と重なる範囲。TS 担当のスコープ外のため待機。
3. [ ] [ID: P1-EMITTER-SELFHOST-TS-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する


### P12-TS-SELFHOST: TS emitter で toolchain2 を TypeScript に変換し tsc build を通す

前提: P8-TS-EMITTER 完了後に着手。

1. [ ] [ID: P12-TS-SELFHOST-S0] selfhost 対象コード（`src/toolchain/` 全 .py、toolchain2 はリネーム済み）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（P4/P6/P9 と共通。先に完了した側の成果を共有）
   - 2026-04-16: ts emitter 側の前提対応として、`_emit_constant` で `\r` と `\t` もエスケープするよう修正（tsc が "Unterminated string literal" で失敗していた）。parser.py の `out.append("\r")` などで顕在化。
2. [ ] [ID: P12-TS-SELFHOST-S1] toolchain 全 .py を TS に emit し、tsc build が通ることを確認する
   - 2026-04-16: emit そのものは `python3 -m toolchain.emit.ts.cli <manifest> -o <out>` で通る（33 ファイル + runtime コピー前）。pytra-cli の `_emit_ts` はまだ "selfhost-safe dynamic load is unavailable" で stub。subprocess 経由で toolchain.emit.ts.cli を呼ぶように差し替える必要がある（他の pytra-cli 改修と同時に整理待ち）。tsc の残 blocker 抜粋: (a) runtime ファイル命名不整合（`py_runtime.ts` が `pytra_built_in_py_runtime.ts` として import される）、(b) `node:fs` / `node:path` / `process` — @types/node 未導入、(c) `CompletedProcess` / `pyrun` / `BuiltinRegistry` / `ResolveResult` / `pyargv` / `pyexit` 等の runtime 未 export、(d) 関数呼び出しで default args を考慮しない argument 数チェック失敗（`Expected 7 arguments, but got 5` など）、(e) `MapIterator.map` / `entries()` の TS 標準適合性。
3. [ ] [ID: P12-TS-SELFHOST-S2] tsc build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P12-TS-SELFHOST-S3] selfhost 用 TS golden を配置し、回帰テストとして維持する
5. [ ] [ID: P12-TS-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang ts --emit-target ts --case-root fixture` で fixture parity PASS
6. [ ] [ID: P12-TS-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang ts --emit-target ts --case-root sample` で sample parity PASS
