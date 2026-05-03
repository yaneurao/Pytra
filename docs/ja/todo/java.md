<a href="../../en/todo/java.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — JVM backend（Java / Scala / Kotlin）

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。
> Java / Scala / Kotlin は全て JVM ターゲットのため、このファイルで一括管理する。

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

### Java
- Java emitter: `src/toolchain/emit/java/`
- Java runtime: `src/runtime/java/`

### Scala
- Scala emitter: `src/toolchain/emit/scala/`
- Scala runtime: `src/runtime/scala/`

### Kotlin
- Kotlin emitter: `src/toolchain/emit/kotlin/`
- Kotlin runtime: `src/runtime/kotlin/`

### 共通
- TS emitter（参考実装）: `src/toolchain/emit/ts/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-JVM-FIXTURE-PARITY-161: Java / Scala / Kotlin fixture parity を 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

現状: Java 152/161、Scala 139/161、Kotlin 141/161 PASS。共通未実行: `control/for_tuple_iter`, `typing/for_over_return_value`, `typing/nullable_dict_field`。Java FAIL: `collections/reversed_basic`, `control/exception_bare_reraise`, `oop/trait_basic`, `oop/trait_with_inheritance`, `signature/ok_typed_varargs_representative`, `typing/callable_optional_none`。Scala/Kotlin は import wiring、trait、optional/isinstance/union、string methods、`eo_extern_opaque_basic` などが追加で fail。

1. [x] [ID: P0-FIX161-JAVA-S1] Java の未実行 3 件と既知 fail 6 件を修正し、Java fixture parity 161/161 PASS を確認する
2. [x] [ID: P0-FIX161-SCALA-S1] Scala の未実行 3 件と既知 fail 19 件を修正し、Scala fixture parity 161/161 PASS を確認する
3. [x] [ID: P0-FIX161-KOTLIN-S1] Kotlin の未実行 3 件と既知 fail 17 件を修正し、Kotlin fixture parity 161/161 PASS を確認する


### P1-HOST-CPP-EMITTER-JVM: C++ emitter を Java / Scala / Kotlin で host する

C++ emitter（`toolchain.emit.cpp.cli`、16 モジュール）を各 JVM 言語に変換し、変換された emitter が C++ コードを正しく生成できることを確認する。C++ emitter の source は selfhost-safe 化済み。

1. [x] [ID: P1-HOST-CPP-EMITTER-JAVA-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/cpp/cli.py --target java -o work/selfhost/host-cpp/java/` で変換 + javac build を通す
   - 完了: 2026-05-03 に `tools/run/run_emitter_host_parity.py --host-lang java --hosted-emitter cpp --case-root fixture --timeout-sec 3600` 内の Java host build が PASS。
2. [x] [ID: P1-HOST-CPP-EMITTER-JAVA-S2] `python3 tools/run/run_emitter_host_parity.py --host-lang java --hosted-emitter cpp --case-root fixture` で C++ emitter host parity PASS を確認する（結果は `.parity-results/emitter_host_java.json` に自動書き込み）
   - 完了: 2026-05-03 に `.parity-results/emitter_host_java.json` が `build_status=ok`, `parity_status=ok`, `parity_fixture_pass=1` を記録。
3. [x] [ID: P1-HOST-CPP-EMITTER-SCALA-S1] `--target scala` で変換 + scalac build を通す
   - 完了: 2026-05-03 に `tools/run/run_emitter_host_parity.py --host-lang scala --hosted-emitter cpp --case-root fixture --timeout-sec 3600` 内の Scala host build が PASS。
4. [x] [ID: P1-HOST-CPP-EMITTER-SCALA-S2] `python3 tools/run/run_emitter_host_parity.py --host-lang scala --hosted-emitter cpp --case-root fixture` で C++ emitter host parity PASS を確認する（結果は `.parity-results/emitter_host_scala.json` に自動書き込み）
   - 完了: 2026-05-03 に `.parity-results/emitter_host_scala.json` が `build_status=ok`, `parity_status=ok`, `parity_fixture_pass=1` を記録。
5. [x] [ID: P1-HOST-CPP-EMITTER-KOTLIN-S1] `--target kotlin` で変換 + kotlinc build を通す
   - 完了: 2026-05-03 に Kotlin hosted C++ emitter の生成物を `kotlinc` build PASS まで復旧。`meta.emit_context.module_id` / `linked_program_v1.module_id` を使った module id 解決、selfhost 用 runtime alias、nullable/string/Path/Json/LinkedModule lowering 補正を追加した。
6. [x] [ID: P1-HOST-CPP-EMITTER-KOTLIN-S2] `python3 tools/run/run_emitter_host_parity.py --host-lang kotlin --hosted-emitter cpp --case-root fixture` で C++ emitter host parity PASS を確認する（結果は `.parity-results/emitter_host_kotlin.json` に自動書き込み）
   - 完了: 2026-05-03 に `PYTHONPYCACHEPREFIX=work/tmp/pycache timeout 3600s python3 tools/run/run_emitter_host_parity.py --host-lang kotlin --hosted-emitter cpp --case-root fixture --timeout-sec 3600` が `[OK] kotlin hosted cpp emitter parity`。`.parity-results/emitter_host_kotlin.json` は `build_status=ok`, `parity_status=ok`, `parity_fixture_pass=1`。

### P1-EMITTER-SELFHOST-JAVA: emit/java/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.java.cli` をエントリに単独で C++ build を通す。

1. [ ] [ID: P1-EMITTER-SELFHOST-JAVA-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/java/cli.py --target cpp -o work/selfhost/emit/java/` を実行し、変換が通るようにする
   - 進捗: 2026-04-29 に実行し、C++ 出力は途中まで進むが完走せず。`timeout 3600s python3 src/pytra-cli.py -build src/toolchain/emit/java/cli.py --target cpp -o work/selfhost/emit/java/` は終了コード 124。停止時点で `work/selfhost/emit/java/` は 30 ファイルの部分出力（うち C++ 11 件）に留まり、selfhost emitter のエントリ一式生成まで到達しない。
2. [ ] [ID: P1-EMITTER-SELFHOST-JAVA-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
3. [ ] [ID: P1-EMITTER-SELFHOST-JAVA-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する

### P1-EMITTER-SELFHOST-SCALA: emit/scala/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

1. [x] [ID: P1-EMITTER-SELFHOST-SCALA-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/scala/cli.py --target cpp -o work/selfhost/emit/scala/` を実行し、変換が通るようにする
   - 完了: 2026-04-29 `rm -rf work/selfhost/emit/scala && timeout 180s python3 src/pytra-cli.py -build src/toolchain/emit/scala/cli.py --target cpp -o work/selfhost/emit/scala/` で変換 PASS。31 files を出力。
2. [ ] [ID: P1-EMITTER-SELFHOST-SCALA-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
   - 進捗: 2026-04-29 `g++ -std=c++20 -O0` は未 PASS。先頭ブロッカーは `CommonRenderer.profile` の `dict[str, JsonVal]` vs `dict[str, object]` 型不一致、`const Object<list[...]>` を mutable 参照へ渡す const 不一致、`Optional[str]` を `_validate_enum(str, ...)` へ渡す lowering、`run_emit_cli` への `list<str>` vs `Object<list<str>>` 不一致、`JsonVal` への `py_dict_get`、`str.isupper` 未対応。
3. [ ] [ID: P1-EMITTER-SELFHOST-SCALA-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する

### P1-EMITTER-SELFHOST-KOTLIN: emit/kotlin/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

1. [x] [ID: P1-EMITTER-SELFHOST-KOTLIN-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/kotlin/cli.py --target cpp -o work/selfhost/emit/kotlin/` を実行し、変換が通るようにする
   - 完了: 2026-04-29 `rm -rf work/selfhost/emit/kotlin && timeout 180s python3 src/pytra-cli.py -build src/toolchain/emit/kotlin/cli.py --target cpp -o work/selfhost/emit/kotlin/` で変換 PASS。31 files を出力。
2. [ ] [ID: P1-EMITTER-SELFHOST-KOTLIN-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
   - 進捗: 2026-04-29 `g++ -std=c++20 -O0` は未 PASS。先頭ブロッカーは `CommonRenderer.profile` の `dict[str, JsonVal]` vs `dict[str, object]` 型不一致、`const Object<list[...]>` を mutable 参照へ渡す const 不一致、`Optional[str]` を `_validate_enum(str, ...)` へ渡す lowering、`run_emit_cli` への `list<str>` vs `Object<list<str>>` 不一致、`JsonVal` と `str` の比較/文字列関数呼び出し、`set<object>` の `std::hash<Object<void>>` 不足、`str.isupper` 未対応。
3. [ ] [ID: P1-EMITTER-SELFHOST-KOTLIN-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する


### P3-JAVA-SELFHOST: Java emitter で toolchain2 を Java に変換し build を通す

文脈: [docs/ja/plans/p3-java-selfhost.md](../plans/p3-java-selfhost.md)

1. [ ] [ID: P3-JAVA-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
2. [ ] [ID: P3-JAVA-SELFHOST-S1] toolchain2 全 .py を Java に emit し、build が通ることを確認する
3. [ ] [ID: P3-JAVA-SELFHOST-S2] build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P3-JAVA-SELFHOST-S3] selfhost 用 Java golden を配置し、回帰テストとして維持する
5. [ ] [ID: P3-JAVA-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root fixture` で fixture parity PASS
6. [ ] [ID: P3-JAVA-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root sample` で sample parity PASS
