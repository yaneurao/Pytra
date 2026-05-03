<a href="../../en/todo/cs.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C# backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-29

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/cs/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/cs/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の C# emitter: `src/toolchain/emit/cs/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の C# runtime: `src/runtime/cs/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-CS-FIXTURE-PARITY-161: C# fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: 135/161 PASS。FAIL: `collections/iterable`, `collections/reversed_basic`, `collections/slice_basic`, `control/nested_closure_def`, `control/yield_generator_min`, `core/class_body_pass`, `core/class_tuple_assign`, `core/lambda_as_arg`, `core/lambda_basic`, `core/lambda_capture_multiargs`, `core/lambda_ifexp`, `core/lambda_local_state`, `core/obj_attr_space`, `core/pass_through_comment`, `imports/bom_from_import`, `imports/from_import_symbols`, `imports/from_pytra_std_import_math`, `imports/type_ignore_from_import`, `signature/ok_lambda_default`, `typing/callable_higher_order`, `typing/callable_optional_none`, `typing/int8`, `typing/tuple_unpack_variants`。未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field`。

1. [x] [ID: P0-FIX161-CS-S1] 未実行 3 件を `runtime_parity_check_fast.py --targets cs --case-root fixture` で確定し、fail なら分類へ追加する
2. [x] [ID: P0-FIX161-CS-S2] lambda/closure、tuple unpack、import wiring、callable、int8、collection 系 fail を解消し、C# fixture parity 161/161 PASS を確認する


### P1-HOST-CPP-EMITTER-CS: C++ emitter を cs で host する

C++ emitter（`toolchain.emit.cpp.cli`、16 モジュール）を cs に変換し、変換された emitter が C++ コードを正しく生成できることを確認する。C++ emitter の source は selfhost-safe 化済み。

1. [x] [ID: P1-HOST-CPP-EMITTER-CS-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target cs -o work/selfhost/host-cpp/cs/` で変換 + build を通す
   - 完了: 2026-05-03 に C# hosted C++ emitter の生成物を `dotnet build` PASS まで復旧。module class 名衝突、import 型 qualification、Callable 型、dataclass `field(default_factory=...)`、JSON nullable scalar、Path runtime mapping、C# local function modifier を修正した。
2. [x] [ID: P1-HOST-CPP-EMITTER-CS-S2] `python3 tools/run/run_emitter_host_parity.py --host-lang cs --hosted-emitter cpp --case-root fixture` で C++ emitter host parity PASS を確認する（結果は `.parity-results/emitter_host_cs.json` に自動書き込み）
   - 完了: 2026-05-03 に `PYTHONPYCACHEPREFIX=work/tmp/pycache timeout 3600s python3 tools/run/run_emitter_host_parity.py --host-lang cs --hosted-emitter cpp --case-root fixture --timeout-sec 3600` が `[OK] cs hosted cpp emitter parity`。`.parity-results/emitter_host_cs.json` は `build_status=ok`, `parity_status=ok`, `parity_fixture_pass=1`。

### P1-EMITTER-SELFHOST-CS: emit/cs/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.cs.cli` をエントリに単独で C++ build を通す。

1. [ ] [ID: P1-EMITTER-SELFHOST-CS-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cs/cli.py --target cpp -o work/selfhost/emit/cs/` を実行し、変換が通るようにする
   - 進捗: 2026-04-29 に実行し、C++ 出力は途中まで進むが完走せず。`timeout 3600s python3 src/pytra-cli.py -build src/toolchain/emit/cs/cli.py --target cpp -o work/selfhost/emit/cs/` は終了コード 124。停止時点で `work/selfhost/emit/cs/` は 36 ファイルの部分出力（うち C++ 14 件）に留まり、selfhost emitter のエントリ一式生成まで到達しない。
2. [ ] [ID: P1-EMITTER-SELFHOST-CS-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
3. [ ] [ID: P1-EMITTER-SELFHOST-CS-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する


### P3-CS-SELFHOST: C# emitter で toolchain2 を C# に変換し build を通す

文脈: [docs/ja/plans/p3-cs-selfhost.md](../plans/p3-cs-selfhost.md)

1. [ ] [ID: P3-CS-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
2. [ ] [ID: P3-CS-SELFHOST-S1] toolchain2 全 .py を C# に emit し、build が通ることを確認する
3. [ ] [ID: P3-CS-SELFHOST-S2] build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P3-CS-SELFHOST-S3] selfhost 用 C# golden を配置し、回帰テストとして維持する
5. [ ] [ID: P3-CS-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang cs --emit-target cs --case-root fixture` で fixture parity PASS
6. [ ] [ID: P3-CS-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang cs --emit-target cs --case-root sample` で sample parity PASS
