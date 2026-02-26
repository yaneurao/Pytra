# P3: Go/Swift/Kotlin backend の EAST3 直生成移行（sidecar 撤去）

最終更新: 2026-02-26

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P3-GSK-NATIVE-01`

背景:
- 現在の `py2go.py` / `py2swift.py` / `py2kotlin.py` は `transpile_to_js` の sidecar JavaScript を生成し、各言語側は Node bridge ラッパーを出力する構成である。
- その結果、`sample/go` / `sample/swift` / `sample/kotlin` はネイティブ backend としての実コード品質が見えにくく、言語ごとの最適化余地も活かせない。
- Java native 化（`P3-JAVA-NATIVE-01`）と同じ方向で、非 native backend を段階的に縮退する必要がある。

目的:
- Go / Swift / Kotlin backend を `EAST3 -> <lang> native emitter` の直生成経路へ移行し、既定経路から JS sidecar bridge を撤去する。

対象:
- `src/py2go.py` / `src/py2swift.py` / `src/py2kotlin.py`
- `src/hooks/go/emitter/` / `src/hooks/swift/emitter/` / `src/hooks/kotlin/emitter/`
- `tools/check_py2go_transpile.py` / `tools/check_py2swift_transpile.py` / `tools/check_py2kotlin_transpile.py`
- `sample/go` / `sample/swift` / `sample/kotlin` 再生成導線と関連ドキュメント

非対象:
- Java backend（`P3-JAVA-NATIVE-01` で管理）
- C++/Rust/C#/JS/TS backend の責務変更
- 高度最適化導入（まずは native 実行互換の確立を優先）

受け入れ基準:
- 既定の `py2go.py` / `py2swift.py` / `py2kotlin.py` が `.js` sidecar を生成しない。
- 各言語 backend が `sample/py` 主要ケースで Python と stdout parity を満たす。
- `sample/<lang>` が preview bridge ラッパーではなく native 実装出力へ置換される。
- 旧 sidecar 経路は廃止または明示 opt-in 互換モードへ縮退される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets go,swift,kotlin --all-samples --ignore-unstable-stdout`

決定ログ:
- 2026-02-26: 初版作成。Go/Swift/Kotlin sidecar backend を低優先で native 化する移行計画を追加。

## 分解

- [ ] [ID: P3-GSK-NATIVE-01-S1-01] 共通移行契約（EAST3 ノード対応範囲、未対応時 fail-closed、runtime 境界）を定義する。
- [ ] [ID: P3-GSK-NATIVE-01-S1-02] 3言語共通で sidecar 互換モードの隔離方針（既定 native / opt-in legacy）を確定する。
- [ ] [ID: P3-GSK-NATIVE-01-S2-01] Go native emitter 骨格と `py2go.py` 既定切替を実装する。
- [ ] [ID: P3-GSK-NATIVE-01-S2-02] Go の式/文/class 基本対応を実装し、`sample/py` 前半ケースを通す。
- [ ] [ID: P3-GSK-NATIVE-01-S3-01] Swift native emitter 骨格と `py2swift.py` 既定切替を実装する。
- [ ] [ID: P3-GSK-NATIVE-01-S3-02] Swift の式/文/class 基本対応を実装し、`sample/py` 前半ケースを通す。
- [ ] [ID: P3-GSK-NATIVE-01-S4-01] Kotlin native emitter 骨格と `py2kotlin.py` 既定切替を実装する。
- [ ] [ID: P3-GSK-NATIVE-01-S4-02] Kotlin の式/文/class 基本対応を実装し、`sample/py` 前半ケースを通す。
- [ ] [ID: P3-GSK-NATIVE-01-S5-01] 3言語の transpile/smoke/parity 回帰を native 既定で通し、CI 導線を更新する。
- [ ] [ID: P3-GSK-NATIVE-01-S5-02] `sample/go` / `sample/swift` / `sample/kotlin` 再生成とドキュメント同期を行う。
