# P1 Julia native backend

最終更新: 2026-03-21

目的:
- Julia native emitter（EAST3 直接生成）を新規実装し、Python → Julia 変換を可能にする。
- 最小限の smoke テストが通る状態を初期ゴールとする。

背景:
- Lua / PowerShell と同じ native emitter パターンで実装する。
- Julia は Lua と構文的に近い部分（`end` ブロック終端、`function` 宣言）が多く、Lua emitter をベースにする。
- Julia 固有の特徴: 1-indexed 配列、多重ディスパッチ、`struct` ベースの型定義、`nothing` が nil 相当。

非対象:
- マルチファイル出力（program_writer）は初期スコープ外。
- lower / optimizer は初期スコープ外。
- プロファイル JSON は初期スコープ外（将来追加可）。

受け入れ基準:
- `transpile_to_julia_native(east_doc)` が EAST3 JSON → Julia ソースを生成できる。
- `test/unit/backends/julia/test_py2julia_smoke.py` の基本テストが通る。
- `transpiler_versions.json` に `"julia": "0.1.0"` が登録されている。
- `check_py2x_profiles.json` に Julia プロファイルが登録されている。

## 子タスク

### S1: emitter パッケージ作成

- [x] [ID: P1-JULIA-NATIVE-01-S1] `src/toolchain/emit/julia/` 配下に emitter パッケージを作成する。

### S2: Julia ランタイム作成

- [x] [ID: P1-JULIA-NATIVE-01-S2] `src/runtime/julia/built_in/py_runtime.jl` を作成する。

### S3: テスト・登録

- [x] [ID: P1-JULIA-NATIVE-01-S3] smoke テスト作成、`transpiler_versions.json`・`check_py2x_profiles.json`・`docs/ja/language/index.md` を更新する。

### S4: 動作確認

- [x] [ID: P1-JULIA-NATIVE-01-S4] smoke テストが通ることを確認する。

## 決定ログ

- 2026-03-21: Lua emitter をベースに Julia native emitter を新規実装する方針を決定。プロファイル JSON / lower / optimizer は初期スコープ外とする。
- 2026-03-21: [P1-JULIA-NATIVE-01-S1〜S4] 全子タスク完了。emitter 実装、runtime 作成、smoke テスト 11/11 通過。
