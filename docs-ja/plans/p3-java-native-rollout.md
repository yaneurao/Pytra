# P3: Java backend の EAST3 直生成移行（sidecar 撤去）

最終更新: 2026-02-26

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P3-JAVA-NATIVE-01`

背景:
- 現在の `py2java.py` は `transpile_to_js` で sidecar JavaScript を生成し、Java 側は Node bridge ラッパーを出力する構成である。
- `sample/java` は bridge 前提の薄い出力になりやすく、Java ネイティブ backend としての品質確認が難しい。
- ユーザー観点で「Java を選んだのに Java 本体コードが生成されない」状態は混乱を招くため、EAST3 直生成へ移行する必要がある。

目的:
- Java backend を `EAST3 -> Java native emitter` の直生成経路へ移行し、sidecar JS 依存を既定経路から除去する。

対象:
- `src/py2java.py`（生成経路切替、sidecar 出力の既定停止）
- `src/hooks/java/emitter/`（native emitter 実装）
- `tools/check_py2java_transpile.py` / `test/unit/test_py2java_smoke.py`（検証更新）
- `sample/java` 再生成導線と関連ドキュメント

非対象:
- Go/Swift/Kotlin backend の同時 native 化
- Java runtime 全面刷新（必要最小限の API 追加を除く）
- Java backend の高度最適化（まずは正しさと parity 優先）

受け入れ基準:
- 既定の `py2java.py` が `.js` sidecar を生成せず、Java 単体で実行可能なコードを出力する。
- `sample/py` 主要ケースで `java` 実行結果が Python 基準と一致する（既存 parity チェック導線で確認可能）。
- `sample/java` が preview 要約ではなく、実行ロジックを持つ native 出力へ置換される。
- sidecar 経路は廃止または明示 opt-in の互換モードへ縮退し、既定は native 固定になる。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2java_*.py'`
- `python3 tools/runtime_parity_check.py --case-root sample --targets java --all-samples --ignore-unstable-stdout`

決定ログ:
- 2026-02-26: 初版作成。Java sidecar bridge 依存を段階撤去する実装計画を追加。
- 2026-02-26: ユーザー指示により優先度を低優先へ変更し、Java native 移行タスクの識別子を低優先帯へ更新。
- 2026-02-26: [ID: `P3-JAVA-NATIVE-01-S1-01`] `docs-ja/spec/spec-java-native-backend.md`（英訳: `docs/spec/spec-java-native-backend.md`）を新設。入力 EAST3 責務、未対応時 fail-closed、runtime 境界、preview との差分を明文化。
- 2026-02-26: [ID: `P3-JAVA-NATIVE-01-S1-02`] `src/hooks/java/emitter/java_native_emitter.py` を追加し、`Module/FunctionDef/ClassDef` の native 骨格出力（本文は placeholder）を実装。`test_py2java_smoke.py` に module/function/class 最小経路テストを追加し、`tools/check_py2java_transpile.py` と併せて回帰なしを確認。
- 2026-02-26: [ID: `P3-JAVA-NATIVE-01-S1-03`] `py2java.py` に `--java-backend {native,sidecar}` を追加。既定を native 経路（`transpile_to_java_native`）へ切替え、旧 sidecar 出力は `--java-backend sidecar` 指定時のみ有効化。`test_py2java_smoke.py` の CLI smoke を native 既定へ更新し、sidecar 互換モードの生成確認テストを追加。
- 2026-02-26: [ID: `P3-JAVA-NATIVE-01-S2-01`] `java_native_emitter` の本文 lower を拡張。`Return/Expr/AnnAssign/Assign/AugAssign/If/ForCore` と主要式（`Name/Constant/UnaryOp/BinOp/Compare/BoolOp/Attribute/Call`）を Java 構文へ接続し、`test_py2java_smoke.py` に `if_else` / `for_range` の lower 検証を追加。
- 2026-02-26: [ID: `P3-JAVA-NATIVE-01-S2-01`] OOP 基本整合を補強。`self` 名参照を `this` へ lower、クラス名呼び出しを `new ClassName(...)` へ lower、未知型注釈は識別子であれば class 型として保持するように更新し、`test_py2java_smoke.py` の `inheritance` 生成期待値を拡張。
- 2026-02-26: [ID: `P3-JAVA-NATIVE-01-S2-01`] 簡易 return-flow 判定（`_block_guarantees_return`）を追加し、`if/else` 両分岐 `return` の関数で fallback `return` を重複挿入しないよう修正。`test_py2java_smoke.py` で `if_else` 生成に `return 0L;` が混入しないことを固定。

## 分解

- [x] [ID: P3-JAVA-NATIVE-01-S1-01] Java backend 契約（入力 EAST3 ノード責務、未対応時 fail-closed、runtime 境界）を文書化し、preview 出力との差分を明示する。
- [x] [ID: P3-JAVA-NATIVE-01-S1-02] `src/hooks/java/emitter` に native emitter 骨格を追加し、module/function/class の最小実行経路を通す。
- [x] [ID: P3-JAVA-NATIVE-01-S1-03] `py2java.py` に backend 切替配線を追加し、既定を native、旧 sidecar を互換モードへ隔離する。
- [ ] [ID: P3-JAVA-NATIVE-01-S2-01] 式/文（算術、条件、ループ、関数呼び出し、組み込み基本型）を native emitter へ実装し、`sample/py` 前半ケースを通す。
- [ ] [ID: P3-JAVA-NATIVE-01-S2-02] class/instance/isinstance 系と runtime フックを native 経路へ接続し、OOP 系ケースを通す。
- [ ] [ID: P3-JAVA-NATIVE-01-S2-03] `import math` と画像系ランタイム呼び出し（`png`/`gif`）の最小互換を整備し、sample 実運用ケースへ対応する。
- [ ] [ID: P3-JAVA-NATIVE-01-S3-01] `check_py2java_transpile` / unit smoke / parity を native 既定で通し、回帰検出を固定する。
- [ ] [ID: P3-JAVA-NATIVE-01-S3-02] `sample/java` を再生成し、preview 要約出力を native 実装出力へ置換する。
- [ ] [ID: P3-JAVA-NATIVE-01-S3-03] `docs-ja/how-to-use.md` / `docs-ja/spec/spec-import.md` の Java 記述を sidecar 前提から更新し、運用手順を同期する。
