<a href="../../en/plans/p4-dart-native-backend.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P4 Dart native backend

最終更新: 2026-03-21

目的:
- Dart native emitter（EAST3 直接生成）を新規実装し、Python → Dart 変換を可能にする。
- 最小限の smoke テストが通る状態を初期ゴールとする。

背景:
- Lua / PowerShell / Julia と同じ native emitter パターンで実装する。
- Dart は JS/TS と構文的に近い部分（C スタイルブレース、`var`/`final` 宣言、`class` 定義）が多いが、Lua emitter をベースにする（native emitter の最小テンプレートとして確立済み）。
- Dart 固有の特徴: null safety (`?`)、`late` 修飾子、`List<T>`/`Map<K,V>` ジェネリクス、`int`/`double`/`String`/`bool` 型、`main()` エントリポイント、`dynamic` 型（Any 相当）。

非対象:
- マルチファイル出力（program_writer）は初期スコープ外。
- lower / optimizer は初期スコープ外。
- プロファイル JSON は初期スコープ外（将来追加可）。
- `docs/en/` の翻訳更新。

受け入れ基準:
- `transpile_to_dart_native(east_doc)` が EAST3 JSON → Dart ソースを生成できる。
- `test/unit/backends/dart/test_py2dart_smoke.py` の基本テストが通る。
- `transpiler_versions.json` に `"dart": "0.1.0"` が登録されている。
- `check_py2x_profiles.json` に Dart プロファイルが登録されている。

## 子タスク

### S1: emitter パッケージ作成

- [x] [ID: P4-DART-NATIVE-01-S1] `src/toolchain/emit/dart/` 配下に emitter パッケージを作成する。

### S2: Dart ランタイム作成

- [x] [ID: P4-DART-NATIVE-01-S2] `src/runtime/dart/built_in/py_runtime.dart` を作成する。

### S3: テスト・登録

- [x] [ID: P4-DART-NATIVE-01-S3] smoke テスト作成、`transpiler_versions.json`・`check_py2x_profiles.json`・`docs/ja/language/index.md` を更新する。

### S4: 動作確認

- [x] [ID: P4-DART-NATIVE-01-S4] smoke テストが通ることを確認する。

## 決定ログ

- 2026-03-21: Lua emitter をベースに Dart native emitter を新規実装する方針を決定。プロファイル JSON / lower / optimizer は初期スコープ外とする。
- 2026-03-21: S1〜S4 完了。emitter パッケージ作成、runtime 作成、テスト・登録更新、smoke テスト 7/7 通過。
