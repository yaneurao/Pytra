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
- 2026-02-26: [ID: `P3-GSK-NATIVE-01-S1-01`] 共通契約 spec `docs-ja/spec/spec-gsk-native-backend.md`（英訳: `docs/spec/spec-gsk-native-backend.md`）を追加。EAST3 入力責務、未対応時 fail-closed、runtime 境界、sidecar 既定撤去要件を定義。
- 2026-02-26: [ID: `P3-GSK-NATIVE-01-S1-02`] 同 spec に sidecar 互換モード隔離方針を追加。`--go-backend/--swift-backend/--kotlin-backend sidecar` の明示 opt-in、native 既定時の `.js` 非生成、native→sidecar 自動フォールバック禁止を固定。
- 2026-02-26: [ID: `P3-GSK-NATIVE-01-S2-01`] `src/hooks/go/emitter/go_native_emitter.py` を追加し、`py2go.py` に `--go-backend {native,sidecar}` を配線して既定を native 化。旧 `go_emitter.py` は sidecar 互換経路として維持し、`test_py2go_smoke.py`（`10/10`）と `tools/check_py2go_transpile.py`（`132/132`）の通過を確認。
- 2026-02-26: [ID: `P3-GSK-NATIVE-01-S2-02`] Go native emitter の本文 lower を拡張（`Return/Expr/AnnAssign/Assign/AugAssign/If/ForCore/While`、主要式、`math` 呼び出し、`list/subscript/slice/listcomp`、class/constructor 基本）。`runtime_parity_check.py --case-root fixture --targets go add if_else for_range inheritance instance_member super_init --ignore-unstable-stdout`（`pass=6/6`）と `runtime_parity_check.py --case-root sample --targets go 01_mandelbrot 02_raytrace_spheres 03_julia_set 04_orbit_trap_julia 05_mandelbrot_zoom 06_julia_parameter_sweep 07_game_of_life_loop 08_langtons_ant 09_fire_simulation --ignore-unstable-stdout`（`pass=9/9`）を確認。

## 分解

- [x] [ID: P3-GSK-NATIVE-01-S1-01] 共通移行契約（EAST3 ノード対応範囲、未対応時 fail-closed、runtime 境界）を定義する。
- [x] [ID: P3-GSK-NATIVE-01-S1-02] 3言語共通で sidecar 互換モードの隔離方針（既定 native / opt-in legacy）を確定する。
- [x] [ID: P3-GSK-NATIVE-01-S2-01] Go native emitter 骨格と `py2go.py` 既定切替を実装する。
- [x] [ID: P3-GSK-NATIVE-01-S2-02] Go の式/文/class 基本対応を実装し、`sample/py` 前半ケースを通す。
- [ ] [ID: P3-GSK-NATIVE-01-S3-01] Swift native emitter 骨格と `py2swift.py` 既定切替を実装する。
- [ ] [ID: P3-GSK-NATIVE-01-S3-02] Swift の式/文/class 基本対応を実装し、`sample/py` 前半ケースを通す。
- [ ] [ID: P3-GSK-NATIVE-01-S4-01] Kotlin native emitter 骨格と `py2kotlin.py` 既定切替を実装する。
- [ ] [ID: P3-GSK-NATIVE-01-S4-02] Kotlin の式/文/class 基本対応を実装し、`sample/py` 前半ケースを通す。
- [ ] [ID: P3-GSK-NATIVE-01-S5-01] 3言語の transpile/smoke/parity 回帰を native 既定で通し、CI 導線を更新する。
- [ ] [ID: P3-GSK-NATIVE-01-S5-02] `sample/go` / `sample/swift` / `sample/kotlin` 再生成とドキュメント同期を行う。
