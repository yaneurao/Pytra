<a href="../../en/todo/java.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — JVM backend（Java / Scala / Kotlin）

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。
> Java / Scala / Kotlin は全て JVM ターゲットのため、このファイルで一括管理する。

最終更新: 2026-04-27

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

1. [ ] [ID: P0-FIX161-JAVA-S1] Java の未実行 3 件と既知 fail 6 件を修正し、Java fixture parity 161/161 PASS を確認する
2. [ ] [ID: P0-FIX161-SCALA-S1] Scala の未実行 3 件と既知 fail 19 件を修正し、Scala fixture parity 161/161 PASS を確認する
3. [ ] [ID: P0-FIX161-KOTLIN-S1] Kotlin の未実行 3 件と既知 fail 17 件を修正し、Kotlin fixture parity 161/161 PASS を確認する

### P1-EMITTER-SELFHOST-JAVA: emit/java/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

各 backend emitter は subprocess で独立起動する自己完結プログラム。pytra-cli.py 全体の selfhost とは切り離し、`toolchain.emit.java.cli` をエントリに単独で C++ build を通す。

1. [ ] [ID: P1-EMITTER-SELFHOST-JAVA-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/java/cli.py --target cpp -o work/selfhost/emit/java/` を実行し、変換が通るようにする
2. [ ] [ID: P1-EMITTER-SELFHOST-JAVA-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
3. [ ] [ID: P1-EMITTER-SELFHOST-JAVA-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する

### P1-EMITTER-SELFHOST-SCALA: emit/scala/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

1. [ ] [ID: P1-EMITTER-SELFHOST-SCALA-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/scala/cli.py --target cpp -o work/selfhost/emit/scala/` を実行し、変換が通るようにする
2. [ ] [ID: P1-EMITTER-SELFHOST-SCALA-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
3. [ ] [ID: P1-EMITTER-SELFHOST-SCALA-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する

### P1-EMITTER-SELFHOST-KOTLIN: emit/kotlin/cli.py を単独で selfhost C++ build に通す

文脈: [docs/ja/plans/p1-emitter-selfhost-per-backend.md](../plans/p1-emitter-selfhost-per-backend.md)

1. [ ] [ID: P1-EMITTER-SELFHOST-KOTLIN-S1] `python3 src/pytra-cli.py -build src/toolchain/emit/kotlin/cli.py --target cpp -o work/selfhost/emit/kotlin/` を実行し、変換が通るようにする
2. [ ] [ID: P1-EMITTER-SELFHOST-KOTLIN-S2] 生成された C++ を `g++ -std=c++20 -O0` でコンパイルを通す（source 側の型注釈不整合を修正）
3. [ ] [ID: P1-EMITTER-SELFHOST-KOTLIN-S3] コンパイル済み emitter で既存 fixture の manifest を処理し、Python 版 emitter と parity 一致を確認する


### P3-JAVA-SELFHOST: Java emitter で toolchain2 を Java に変換し build を通す

文脈: [docs/ja/plans/p3-java-selfhost.md](../plans/p3-java-selfhost.md)

1. [ ] [ID: P3-JAVA-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
2. [ ] [ID: P3-JAVA-SELFHOST-S1] toolchain2 全 .py を Java に emit し、build が通ることを確認する
3. [ ] [ID: P3-JAVA-SELFHOST-S2] build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P3-JAVA-SELFHOST-S3] selfhost 用 Java golden を配置し、回帰テストとして維持する
5. [ ] [ID: P3-JAVA-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root fixture` で fixture parity PASS
6. [ ] [ID: P3-JAVA-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root sample` で sample parity PASS
