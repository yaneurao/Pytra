<a href="../../en/todo/java.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — JVM backend（Java / Scala / Kotlin）

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。
> Java / Scala / Kotlin は全て JVM ターゲットのため、このファイルで一括管理する。

最終更新: 2026-04-02

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

### P1-SCALA-EMITTER: Scala emitter を toolchain2 に新規実装する

1. [ ] [ID: P1-SCALA-EMITTER-S1] `src/toolchain2/emit/scala/` に Scala emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/scala/` と TS emitter を参考にする
2. [ ] [ID: P1-SCALA-EMITTER-S2] `src/runtime/scala/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義
3. [ ] [ID: P1-SCALA-EMITTER-S3] fixture 全件の Scala emit 成功を確認する
4. [ ] [ID: P1-SCALA-EMITTER-S4] Scala runtime を toolchain2 の emit 出力と整合させる
5. [ ] [ID: P1-SCALA-EMITTER-S5] fixture の Scala run parity を通す（`scala`）
6. [ ] [ID: P1-SCALA-EMITTER-S6] stdlib の Scala parity を通す（`--case-root stdlib`）
7. [ ] [ID: P1-SCALA-EMITTER-S7] sample の Scala parity を通す（`--case-root sample`）

### P1-KOTLIN-EMITTER: Kotlin emitter を toolchain2 に新規実装する

1. [ ] [ID: P1-KOTLIN-EMITTER-S1] `src/toolchain2/emit/kotlin/` に Kotlin emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/kotlin/` と TS emitter を参考にする
2. [ ] [ID: P1-KOTLIN-EMITTER-S2] `src/runtime/kotlin/mapping.json` を作成する — `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` を定義
3. [ ] [ID: P1-KOTLIN-EMITTER-S3] fixture 全件の Kotlin emit 成功を確認する
4. [ ] [ID: P1-KOTLIN-EMITTER-S4] Kotlin runtime を toolchain2 の emit 出力と整合させる
5. [ ] [ID: P1-KOTLIN-EMITTER-S5] fixture の Kotlin run parity を通す（`kotlinc` + `java -jar`）
6. [ ] [ID: P1-KOTLIN-EMITTER-S6] stdlib の Kotlin parity を通す（`--case-root stdlib`）
7. [ ] [ID: P1-KOTLIN-EMITTER-S7] sample の Kotlin parity を通す（`--case-root sample`）

### P2-JVM-LINT: emitter hardcode lint の Scala / Kotlin 違反を解消する

1. [ ] [ID: P2-JVM-LINT-S1] `check_emitter_hardcode_lint.py --lang scala` で全カテゴリ 0 件になることを確認する
2. [ ] [ID: P2-JVM-LINT-S2] `check_emitter_hardcode_lint.py --lang kotlin` で全カテゴリ 0 件になることを確認する

### P3-JAVA-SELFHOST: Java emitter で toolchain2 を Java に変換し build を通す

文脈: [docs/ja/plans/p3-java-selfhost.md](../plans/p3-java-selfhost.md)

1. [ ] [ID: P3-JAVA-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
2. [ ] [ID: P3-JAVA-SELFHOST-S1] toolchain2 全 .py を Java に emit し、build が通ることを確認する
3. [ ] [ID: P3-JAVA-SELFHOST-S2] build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P3-JAVA-SELFHOST-S3] selfhost 用 Java golden を配置し、回帰テストとして維持する
5. [ ] [ID: P3-JAVA-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root fixture` で fixture parity PASS
6. [ ] [ID: P3-JAVA-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root sample` で sample parity PASS
