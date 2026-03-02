# P0: Nim toolchain 導入 + py2nim 実装 + test 通過

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-NIM-TOOLCHAIN-PY2NIM-01`

背景:
- 現在の `main` には `src/hooks/nim/` の雛形のみがあり、CLI 入口の `src/py2nim.py` は未整備である。
- PR #3 相当の Nim 導線は、そのままでは import 崩れ（`hooks.js` 参照）で起動不能だった。
- 実行環境に Nim コンパイラが入っておらず（`which nim` が空）、生成コードの compile/run 回帰を実施できない。

目的:
- この環境へ Nim コンパイラを導入し、再現可能なバージョン固定運用にする。
- `py2nim.py` を EAST3 only の CLI として実装し、Nim runtime 分離で変換・実行可能化する。
- `test/` 配下の Nim 対象テストと transpile チェックを通し、回帰導線を固定する。

対象:
- ツールチェーン導入手順（Nim install / version pin / 存在確認）
- `src/py2nim.py`
- `src/backends/nim/emitter/*`（必要なら `src/hooks/nim` から移設）
- `src/runtime/nim/pytra/py_runtime.nim`
- `test/unit/test_py2nim_smoke.py` と Nim fixture
- `tools/check_py2nim_transpile.py`

非対象:
- Nim backend の性能最適化（ベンチマーク改善）
- sample 全件 parity の同時達成（まず test 導線と基本実行性を優先）
- Nim 以外 backend の設計変更

受け入れ基準:
- `nim --version` がこの環境で実行可能で、導入手順が再現可能な形で残る。
- `python3 src/py2nim.py <fixture.py> -o <out.nim>` で `.nim` と runtime が生成される。
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2nim_smoke.py' -v` が pass する。
- `python3 tools/check_py2nim_transpile.py` が pass する。
- 追加した Nim 導線が既存主要チェック（少なくとも `tools/check_py2cpp_transpile.py`）を壊さない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `nim --version`
- `python3 tools/check_py2nim_transpile.py`
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2nim_smoke.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

決定ログ:
- 2026-03-02: ユーザー指示により、Nim コンパイラ導入・`py2nim.py` 実装・`test/` 通過までを P0 として起票。
- 2026-03-02: 既存 `src/hooks/nim/` 雛形は流用可能だが、import 崩れを避けるため `src/backends/nim/` 基準で責務を再整理する方針を採用。

## 分解

- [ ] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S1-01] Nim コンパイラ導入方式（パッケージマネージャ/バージョン固定）を決定し、この環境へ導入する。
- [ ] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S1-02] `nim --version` と最小 compile 実行で toolchain 稼働を確認し、再現手順を残す。
- [ ] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-01] Nim backend の実装配置を `src/backends/nim/emitter/` 基準へ整理し、`src/hooks/nim` 依存を解消する。
- [ ] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-02] `src/py2nim.py` を実装し、EAST3 only・runtime 分離コピー・fail-closed を満たす CLI 導線を作る。
- [ ] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-03] Nim native emitter の最小対応（関数/分岐/ループ/主要式）を整備し、既知 fixture を変換可能にする。
- [ ] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S2-04] `src/runtime/nim/pytra/py_runtime.nim` を整備し、生成コードからの参照契約を固定する。
- [ ] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-01] `test/unit/test_py2nim_smoke.py` と必要 fixture を整備し、Nim 導線の最小回帰を固定する。
- [ ] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-02] `tools/check_py2nim_transpile.py` を整備して transpile 一括回帰を追加する。
- [ ] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-03] Nim 対象 test/check を実行して pass を確認し、結果を記録する。
- [ ] [ID: P0-NIM-TOOLCHAIN-PY2NIM-01-S3-04] 既存主要チェック（`check_py2cpp_transpile` など）で非退行を確認する。
