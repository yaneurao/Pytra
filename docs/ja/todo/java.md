<a href="../../en/todo/java.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Java backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-01

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 参考資料

- 旧 toolchain1 の Java emitter: `src/toolchain/emit/java/`
- toolchain2 の TS emitter（参考実装）: `src/toolchain2/emit/ts/`
- 既存の Java runtime: `src/runtime/java/`
- emitter 実装ガイドライン: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json 仕様: `docs/ja/spec/spec-runtime-mapping.md`

## 未完了タスク

### P0-JAVA-TYPE-ID-CLEANUP: Java runtime から type_id_table 参照を削除する

仕様: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

Java は `instanceof` がネイティブにあるので `pytra_built_in_type_id_table` クラス参照は不要。

1. [x] [ID: P0-JAVA-TYPEID-CLN-S1] `src/runtime/java/built_in/PyRuntime.java` から `type_id_table` クラス参照を削除する（2026-04-01）— `pytra_built_in_type_id_table` への反射 lookup を廃止し、built-in type id は runtime 内定数へ直結
2. [x] [ID: P0-JAVA-TYPEID-CLN-S2] Java emitter の isinstance を `x instanceof Type` に置換する（2026-04-01）— 既存 emitter 実装 [java_native_emitter.py](/workspace/Pytra/src/toolchain/emit/java/emitter/java_native_emitter.py) の `_render_isinstance_check` が `instanceof` のみを使っていることを確認
3. [ ] [ID: P0-JAVA-TYPEID-CLN-S3] fixture + sample + stdlib parity に回帰がないことを確認する

### P0-JAVA-NEW-FIXTURES: 新規 fixture の Java parity を通す

今セッションで追加された fixture の Java parity 確認。Python では全て PASS 済み。

1. [x] [ID: P0-JAVA-NEWFIX-S1] `tuple_unpack_variants` が Java で compile + run parity PASS することを確認する（2026-04-01）— old EAST3 lowering の nested `FunctionDef -> ClosureDef` / non-Name listcomp target assignment 漏れを修正し、Java emitter の `ClosureDef` helper emit・unpack・`try/catch`・dynamic Eq・`print(bool)` を補正して `pytra-cli.py --target java --run` で `True`
2. [x] [ID: P0-JAVA-NEWFIX-S2] `typed_container_access` が Java で compile + run parity PASS することを確認する（2026-04-01）— Java emitter に `dict.items/keys/values` lowering、`tuple_expanded` runtime-iter unpack、container assignment cast 補正、tuple 型の Java 化を追加し、`pytra-cli.py --target java --run` で `True`
3. [x] [ID: P0-JAVA-NEWFIX-S3] `in_membership_iterable` が Java で compile + run parity PASS することを確認する（2026-04-01）— Java emitter の `In/NotIn` を `PyRuntime.pyIn` ベースへ寄せ、`range` を `PyRuntime.pyRange`、`set[T]` を `LinkedHashSet<T>` に lowering して `pytra-cli.py --target java --run` で `True`
4. [x] [ID: P0-JAVA-NEWFIX-S4] `callable_higher_order` が Java で compile + run parity PASS することを確認する（2026-04-01）— Java emitter に `callable` を `Function<Object,Object>` として扱う最小 higher-order support を追加し、関数値を cast 付き lambda に lowering、callable 呼び出しを `.apply(...)` に変換して `pytra-cli.py --target java --run` で `True`
5. [x] [ID: P0-JAVA-NEWFIX-S5] `object_container_access` が Java で compile + run parity PASS することを確認する（2026-04-01）— Java old emitter の general-union reject を外して object lane を許可し、`set()` builtin と `LinkedHashSet` coercion を追加して `pytra-cli.py --target java --run` で `True`

### P0-JAVA-LINT-V2: emitter hardcode lint の Java 残件を解消する

`check_emitter_hardcode_lint.py --lang java` で `skip_pure_python` が FAIL。

1. [x] [ID: P0-JAVA-LINT-V2-S1] skip_pure_python 違反を修正する — mapping.json の skip_modules から pure Python モジュールを外す（2026-04-01）— `src/runtime/java/mapping.json` から `pytra.std.` を除去
2. [x] [ID: P0-JAVA-LINT-V2-S2] `check_emitter_hardcode_lint.py --lang java` で全カテゴリ 0 件になることを確認する（2026-04-01）— 0 件

### P3-JAVA-SELFHOST: Java emitter で toolchain2 を Java に変換し build を通す

文脈: [docs/ja/plans/p3-java-selfhost.md](../plans/p3-java-selfhost.md)

1. [ ] [ID: P3-JAVA-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
2. [ ] [ID: P3-JAVA-SELFHOST-S1] toolchain2 全 .py を Java に emit し、build が通ることを確認する
3. [ ] [ID: P3-JAVA-SELFHOST-S2] build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P3-JAVA-SELFHOST-S3] selfhost 用 Java golden を配置し、回帰テストとして維持する
5. [ ] [ID: P3-JAVA-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root fixture` で fixture parity PASS
6. [ ] [ID: P3-JAVA-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root sample` で sample parity PASS
