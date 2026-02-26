# TODO（未完了）

> `docs-ja/` が正（source of truth）です。`docs/` はその翻訳です。

<a href="../../docs/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-26

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs-ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs-ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs-ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs-ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs-ja/todo/index.md` / `docs-ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs-ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs-ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。


## 未完了タスク

### P0: Java backend の EAST3 直生成移行（sidecar 撤去）（最優先）

文脈: [docs-ja/plans/p0-java-native-rollout.md](../plans/p0-java-native-rollout.md)

1. [ ] [ID: P0-JAVA-NATIVE-01] Java backend を `EAST3 -> Java native emitter` 直生成経路へ移行し、sidecar JS 依存を既定経路から除去する。
2. [ ] [ID: P0-JAVA-NATIVE-01-S1-01] Java backend 契約（入力 EAST3 ノード責務、未対応時 fail-closed、runtime 境界）を文書化し、preview 出力との差分を明示する。
3. [ ] [ID: P0-JAVA-NATIVE-01-S1-02] `src/hooks/java/emitter` に native emitter 骨格を追加し、module/function/class の最小実行経路を通す。
4. [ ] [ID: P0-JAVA-NATIVE-01-S1-03] `py2java.py` に backend 切替配線を追加し、既定を native、旧 sidecar を互換モードへ隔離する。
5. [ ] [ID: P0-JAVA-NATIVE-01-S2-01] 式/文（算術、条件、ループ、関数呼び出し、組み込み基本型）を native emitter へ実装し、`sample/py` 前半ケースを通す。
6. [ ] [ID: P0-JAVA-NATIVE-01-S2-02] class/instance/isinstance 系と runtime フックを native 経路へ接続し、OOP 系ケースを通す。
7. [ ] [ID: P0-JAVA-NATIVE-01-S2-03] `import math` と画像系ランタイム呼び出し（`png`/`gif`）の最小互換を整備し、sample 実運用ケースへ対応する。
8. [ ] [ID: P0-JAVA-NATIVE-01-S3-01] `check_py2java_transpile` / unit smoke / parity を native 既定で通し、回帰検出を固定する。
9. [ ] [ID: P0-JAVA-NATIVE-01-S3-02] `sample/java` を再生成し、preview 要約出力を native 実装出力へ置換する。
10. [ ] [ID: P0-JAVA-NATIVE-01-S3-03] `docs-ja/how-to-use.md` / `docs-ja/spec/spec-import.md` の Java 記述を sidecar 前提から更新し、運用手順を同期する。

### P0: EAST3 共通最適化層の実装導入（最優先）

文脈: [docs-ja/plans/p0-east3-optimizer-rollout.md](../plans/p0-east3-optimizer-rollout.md)

1. [ ] [ID: P0-EAST3-OPT-01] `EAST3 -> EAST3` 共通最適化層を導入し、pass manager / opt level / fail-closed 契約を実装へ反映する。
2. [ ] [ID: P0-EAST3-OPT-01-S1-01] optimizer エントリ (`east3_optimizer.py`) と pass manager 骨格（`PassContext`/`PassResult`）を追加する。
3. [ ] [ID: P0-EAST3-OPT-01-S1-02] CLI オプション（`--east3-opt-level`, `--east3-opt-pass`, dump/trace）を実装し、`O0/O1/O2` 契約を固定する。
4. [ ] [ID: P0-EAST3-OPT-01-S2-01] `NoOpCastCleanupPass` / `LiteralCastFoldPass` を実装し、`O1` 既定セットを確立する。
5. [ ] [ID: P0-EAST3-OPT-01-S2-02] `RangeForCanonicalizationPass` / `UnusedLoopVarElisionPass` を実装し、`for ... in range(...)` の責務境界を反映する。
6. [ ] [ID: P0-EAST3-OPT-01-S2-03] `LoopInvariantHoistLitePass` / `StrengthReductionFloatLoopPass` を `O2` 限定で導入する。
7. [ ] [ID: P0-EAST3-OPT-01-S3-01] pass 単体テスト（入力/出力EAST3差分、非適用ガード、意味保存）を追加する。
8. [ ] [ID: P0-EAST3-OPT-01-S3-02] `sample` 回帰 + parity 検証を実行し、`O0`/`O1`/`O2` 切替時の互換を確認する。
9. [ ] [ID: P0-EAST3-OPT-01-S3-03] 実装差分を `spec-east3-optimizer` と同期し、運用手順（トレース確認/切り分け）を文書化する。

### P0: C++ backend 後段最適化層（CppOptimizer）導入（最優先）

文脈: [docs-ja/plans/p0-cpp-optimizer-rollout.md](../plans/p0-cpp-optimizer-rollout.md)

1. [ ] [ID: P0-CPP-OPT-01] `EAST3 -> C++ lowering` 後段に `CppOptimizer` 層を導入し、`CppEmitter` から最適化責務を分離する。
2. [ ] [ID: P0-CPP-OPT-01-S1-01] `src/hooks/cpp/optimizer/` の骨格（optimizer/context/trace/passes）と no-op 配線を追加する。
3. [ ] [ID: P0-CPP-OPT-01-S1-02] `py2cpp` 実行経路へ `CppOptimizer` 呼び出しを追加し、`--cpp-opt-level` / `--cpp-opt-pass` / dump オプションを配線する。
4. [ ] [ID: P0-CPP-OPT-01-S2-01] `CppDeadTempPass` / `CppNoOpCastPass` を実装し、emitter 内の同等ロジックを移設する。
5. [ ] [ID: P0-CPP-OPT-01-S2-02] `CppConstConditionPass` / `CppRangeForShapePass` を導入し、C++ 構文化前の IR 正規化を固定する。
6. [ ] [ID: P0-CPP-OPT-01-S2-03] `CppRuntimeFastPathPass` を限定導入し、runtime 契約同値の範囲で最適化する。
7. [ ] [ID: P0-CPP-OPT-01-S3-01] `CppEmitter` 側の最適化分岐を削減し、責務境界を `spec-cpp-optimizer` に合わせて整理する。
8. [ ] [ID: P0-CPP-OPT-01-S3-02] C++ 回帰（`test_py2cpp_*` / `check_py2cpp_transpile.py` / `runtime_parity_check --targets cpp`）を固定する。
9. [ ] [ID: P0-CPP-OPT-01-S3-03] 速度/サイズ/生成差分のベースラインを計測し、導入効果を文脈ファイルへ記録する。

### P3: Go/Swift/Kotlin backend の EAST3 直生成移行（sidecar 撤去）（低優先）

文脈: [docs-ja/plans/p3-go-swift-kotlin-native-rollout.md](../plans/p3-go-swift-kotlin-native-rollout.md)

1. [ ] [ID: P3-GSK-NATIVE-01] Go/Swift/Kotlin backend を `EAST3 -> <lang> native emitter` 直生成経路へ移行し、sidecar JS 依存を既定経路から除去する。
2. [ ] [ID: P3-GSK-NATIVE-01-S1-01] 共通移行契約（EAST3 ノード対応範囲、未対応時 fail-closed、runtime 境界）を定義する。
3. [ ] [ID: P3-GSK-NATIVE-01-S1-02] 3言語共通で sidecar 互換モードの隔離方針（既定 native / opt-in legacy）を確定する。
4. [ ] [ID: P3-GSK-NATIVE-01-S2-01] Go native emitter 骨格と `py2go.py` 既定切替を実装する。
5. [ ] [ID: P3-GSK-NATIVE-01-S2-02] Go の式/文/class 基本対応を実装し、`sample/py` 前半ケースを通す。
6. [ ] [ID: P3-GSK-NATIVE-01-S3-01] Swift native emitter 骨格と `py2swift.py` 既定切替を実装する。
7. [ ] [ID: P3-GSK-NATIVE-01-S3-02] Swift の式/文/class 基本対応を実装し、`sample/py` 前半ケースを通す。
8. [ ] [ID: P3-GSK-NATIVE-01-S4-01] Kotlin native emitter 骨格と `py2kotlin.py` 既定切替を実装する。
9. [ ] [ID: P3-GSK-NATIVE-01-S4-02] Kotlin の式/文/class 基本対応を実装し、`sample/py` 前半ケースを通す。
10. [ ] [ID: P3-GSK-NATIVE-01-S5-01] 3言語の transpile/smoke/parity 回帰を native 既定で通し、CI 導線を更新する。
11. [ ] [ID: P3-GSK-NATIVE-01-S5-02] `sample/go` / `sample/swift` / `sample/kotlin` 再生成とドキュメント同期を行う。
