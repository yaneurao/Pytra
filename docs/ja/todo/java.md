<a href="../../en/todo/java.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — JVM backend（Java / Scala / Kotlin）

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。
> Java / Scala / Kotlin は全て JVM ターゲットのため、このファイルで一括管理する。

最終更新: 2026-04-07

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/{java,scala,kotlin}/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/{java,scala,kotlin}/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

### Java
- 旧 toolchain1 の Java emitter: `src/toolchain/emit/java/`
- toolchain2 の Java emitter: `src/toolchain2/emit/java/`
- Java runtime: `src/runtime/java/`

### Scala
- 旧 toolchain1 の Scala emitter: `src/toolchain/emit/scala/`
- Scala runtime: `src/runtime/scala/`

### Kotlin
- 旧 toolchain1 の Kotlin emitter: `src/toolchain/emit/kotlin/`
- Kotlin runtime: `src/runtime/kotlin/`

### 共通
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-JVM-NEW-FIXTURE-PARITY: 新規追加 fixture / stdlib の parity 確認

今セッション（2026-04-01〜05）で追加・更新した fixture と stdlib の parity を確認する。

対象: `bytes_copy_semantics`, `negative_index_comprehensive`, `negative_index_out_of_range`, `callable_optional_none`, `str_find_index`, `eo_extern_opaque_basic`(emit-only), `math_extended`(stdlib), `os_glob_extended`(stdlib)

1. [x] [ID: P0-JVM-NEWFIX-S1] 上記 fixture/stdlib の parity を確認する（対象 fixture のみ実行） — Java/Scala/Kotlin の対象ケースを確認し、Java/Scala は parity を復旧、Kotlin は `kotlinc` 導入後に fixture/stdlib parity を確認済み

### P1-SCALA-EMITTER: Scala emitter を toolchain2 に新規実装する

1. [x] [ID: P1-SCALA-EMITTER-S1] `src/toolchain2/emit/scala/` に Scala emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/scala/` と TS emitter を参考にする
2. [x] [ID: P1-SCALA-EMITTER-S2] `src/runtime/scala/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義
3. [x] [ID: P1-SCALA-EMITTER-S3] fixture 全件の Scala emit 成功を確認する — emit/run 経路で fixture parity を確認済み
4. [x] [ID: P1-SCALA-EMITTER-S4] Scala runtime を toolchain2 の emit 出力と整合させる — `bytes/bytearray` ctor、`Path.joinpath`、math/path/glob namespace、`continue` lowering などを runtime/emitter 両面で整合済み
5. [x] [ID: P1-SCALA-EMITTER-S5] fixture の Scala run parity を通す（`scala`） — `runtime_parity_check_fast.py --case-root fixture --targets scala` の対象回帰を解消済み
6. [x] [ID: P1-SCALA-EMITTER-S6] stdlib の Scala parity を通す（`--case-root stdlib`） — `pathlib_extended`、`pytra_runtime_png`、`math_extended`、`os_glob_extended` を含め PASS
7. [x] [ID: P1-SCALA-EMITTER-S7] sample の Scala parity を通す（`--case-root sample`） — `runtime_parity_check_fast.py --case-root sample --targets scala` で `18/18 PASS`

### P1-KOTLIN-EMITTER: Kotlin emitter を toolchain2 に新規実装する

1. [x] [ID: P1-KOTLIN-EMITTER-S1] `src/toolchain2/emit/kotlin/` に Kotlin emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/kotlin/` と TS emitter を参考にする
2. [x] [ID: P1-KOTLIN-EMITTER-S2] `src/runtime/kotlin/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義
3. [x] [ID: P1-KOTLIN-EMITTER-S3] fixture 全件の Kotlin emit 成功を確認する — `kotlinc` 導入後に fixture 回帰ケースを通し、emit/compile/run 成功を確認済み
4. [x] [ID: P1-KOTLIN-EMITTER-S4] Kotlin runtime を toolchain2 の emit 出力と整合させる — `with`、`bytearray` ctor、`str.count/rfind/index`、`Path.joinpath`、exception/sorted surface を runtime/emitter で整合済み
5. [x] [ID: P1-KOTLIN-EMITTER-S5] fixture の Kotlin run parity を通す（`kotlinc` + `java -jar`） — `with_statement`、`with_context_manager`、`exception_types`、`str_count`、`str_find_index`、`float_constructor` などを PASS 確認済み
6. [x] [ID: P1-KOTLIN-EMITTER-S6] stdlib の Kotlin parity を通す（`--case-root stdlib`） — `pytra_runtime_png`、`pathlib_extended` を PASS 確認済み
7. [ ] [ID: P1-KOTLIN-EMITTER-S7] sample の Kotlin parity を通す（`--case-root sample`）

### P3-JAVA-SELFHOST: Java emitter で toolchain2 を Java に変換し build を通す

文脈: [docs/ja/plans/p3-java-selfhost.md](../plans/p3-java-selfhost.md)

1. [ ] [ID: P3-JAVA-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
2. [ ] [ID: P3-JAVA-SELFHOST-S1] toolchain2 全 .py を Java に emit し、build が通ることを確認する
3. [ ] [ID: P3-JAVA-SELFHOST-S2] build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P3-JAVA-SELFHOST-S3] selfhost 用 Java golden を配置し、回帰テストとして維持する
5. [ ] [ID: P3-JAVA-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root fixture` で fixture parity PASS
6. [ ] [ID: P3-JAVA-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root sample` で sample parity PASS
