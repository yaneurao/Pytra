<a href="../../en/todo/java.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Java backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-30

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

### P1-JAVA-EMITTER: Java emitter を toolchain2 に新規実装する

文脈: [docs/ja/plans/p1-java-emitter.md](../plans/p1-java-emitter.md)

1. [x] [ID: P1-JAVA-EMITTER-S1] `src/toolchain2/emit/java/` に Java emitter を新規実装する — CommonRenderer + override 構成。旧 `src/toolchain/emit/java/` と TS emitter（`src/toolchain2/emit/ts/`）を参考にする。Java 固有のノード（class 必須、package、static method、checked exception 等）だけ override として残す
   完了メモ: 2026-03-30 toolchain2 用の `emit/java/` を追加し、`pytra-cli2 --target java` の emit/build 配線と smoke test を実装
2. [x] [ID: P1-JAVA-EMITTER-S2] `src/runtime/java/mapping.json` を作成し、runtime_call の写像を定義する。`types` テーブルも含める（spec-runtime-mapping.md §7）。`env.target` 必須エントリも忘れないこと
   完了メモ: 2026-03-30 `src/runtime/java/mapping.json` を追加し、`env.target` / builtins / 基本型写像を定義
3. [x] [ID: P1-JAVA-EMITTER-S3] fixture 全件の Java emit 成功を確認する
   完了メモ: 2026-03-30 `PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets java` で fixture 131/131 PASS
4. [x] [ID: P1-JAVA-EMITTER-S4] Java runtime を toolchain2 の emit 出力と整合させる（旧 runtime の引き継ぎ or 再実装）
   完了メモ: 2026-03-30 `PyRuntime.java` / `pathlib.java` / `argparse.java` / `json.java` / `mapping.json` を toolchain2 出力に合わせ、type-id helper・GIF helper・pathlib/runtime helper を整合
5. [x] [ID: P1-JAVA-EMITTER-S5] fixture + sample の Java compile + run parity を通す（`javac` + `java`）
   完了メモ: 2026-03-30 `PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets java --case-root sample` で sample 18/18 PASS
6. [x] [ID: P1-JAVA-EMITTER-S6] stdlib の Java parity を通す（`--case-root stdlib`）
   完了メモ: 2026-03-30 `PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py --targets java --case-root stdlib` で stdlib 16/16 PASS

### P2-JAVA-LINT-FIX: Java emitter のハードコード違反を修正する

仕様: [spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1, §7

1. [x] [ID: P2-JAVA-LINT-S1] `check_emitter_hardcode_lint.py` で Java の違反が 0 件になることを確認する
   完了メモ: 2026-03-31 `python3 tools/check/check_emitter_hardcode_lint.py` で Java の違反 0 件を確認

### P3-JAVA-SELFHOST: Java emitter で toolchain2 を Java に変換し build を通す

文脈: [docs/ja/plans/p3-java-selfhost.md](../plans/p3-java-selfhost.md)

1. [ ] [ID: P3-JAVA-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（他言語と共通。先に完了した側の成果を共有）
2. [ ] [ID: P3-JAVA-SELFHOST-S1] toolchain2 全 .py を Java に emit し、build が通ることを確認する
3. [ ] [ID: P3-JAVA-SELFHOST-S2] build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P3-JAVA-SELFHOST-S3] selfhost 用 Java golden を配置し、回帰テストとして維持する
5. [ ] [ID: P3-JAVA-SELFHOST-S4] `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root fixture` で fixture parity PASS
6. [ ] [ID: P3-JAVA-SELFHOST-S5] `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root sample` で sample parity PASS
