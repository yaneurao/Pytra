<a href="../../ja/plans/p7-zig-native-backend.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p7-zig-native-backend.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p7-zig-native-backend.md`

# P7 Zig native backend

最終更新: 2026-03-21

目的:
- Zig native emitter（EAST3 直接生成）を新規実装し、Python → Zig 変換を可能にする。
- 最小限の smoke テストが通る状態を初期ゴールとする。

背景:
- Lua / PowerShell と同じ native emitter パターンで実装する。
- Zig 固有の特徴: コンパイル時計算（comptime）、エラーユニオン型（`!T`）、optional 型（`?T`）、`struct` ベースの型定義、GC なし（手動メモリ管理）、0-indexed 配列。
- Lua emitter をベースにし、Zig 構文へ適応する。

非対象:
- マルチファイル出力（program_writer）は初期スコープ外。
- lower / optimizer は初期スコープ外。
- プロファイル JSON は初期スコープ外（将来追加可）。
- Zig のコンパイル時メタプログラミング活用は初期スコープ外。

受け入れ基準:
- `transpile_to_zig_native(east_doc)` が EAST3 JSON → Zig ソースを生成できる。
- `test/unit/backends/zig/test_py2zig_smoke.py` の基本テストが通る。
- `transpiler_versions.json` に `"zig": "0.1.0"` が登録されている。
- `check_py2x_profiles.json` に Zig プロファイルが登録されている。

## 子タスク

### S1: emitter パッケージ作成

- [x] [ID: P7-ZIG-NATIVE-01-S1] `src/toolchain/emit/zig/` 配下に emitter パッケージを作成する。
  - `src/toolchain/emit/zig/emitter/__init__.py`
  - `src/toolchain/emit/zig/emitter/zig_native_emitter.py`
  - `src/toolchain/emit/zig.py`（CLI エントリーポイント）

### S2: Zig ランタイム作成

- [x] [ID: P7-ZIG-NATIVE-01-S2] `src/runtime/zig/built_in/py_runtime.zig` を作成する。

### S3: テスト・登録

- [x] [ID: P7-ZIG-NATIVE-01-S3] smoke テスト作成、`transpiler_versions.json`・`check_py2x_profiles.json`・`docs/ja/language/index.md` を更新する。

### S4: 動作確認

- [x] [ID: P7-ZIG-NATIVE-01-S4] smoke テストが通ることを確認する。

## 決定ログ

- 2026-03-21: Lua emitter をベースに Zig native emitter を新規実装する方針を決定。プロファイル JSON / lower / optimizer は初期スコープ外とする。
