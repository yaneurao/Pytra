<a href="../../en/spec/spec-zig-native-backend.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Zig Native Backend 契約仕様

この文書は Zig native emitter（EAST3 → Zig 直接生成）の契約を定義する。

## 1. 目的

- Zig backend を sidecar 依存なしの native 直生成として実装する際の責務境界を固定する。
- 初期実装段階でも、対応範囲と未対応時の失敗条件を明文化する。

## 2. 入力 EAST3 ノード責務

Zig native emitter は以下を満たす EAST3 ドキュメントのみを受理する。

- ルートは `dict` かつ `kind == "Module"`。
- `east_stage == 3`（`--east-stage 2` は受理しない）。
- `body` は EAST3 statement ノード列。

## 3. fail-closed 契約

未対応入力を受けた場合、互換経路へ逃がさず即時失敗する。

- 未対応 `kind` / shape を検出した時点で `RuntimeError` を送出する。
- エラーメッセージは少なくとも `lang=zig` と failure kind（node/shape）を含む。
- CLI は非 0 で終了し、不完全な `.zig` を成功扱いしない。

## 4. runtime 境界

Zig 生成コードの runtime 境界は、原則として次に限定する。

- `src/runtime/zig/built_in/` 配下の Zig runtime API
- Zig 標準ライブラリ（`std`）

## 5. 非対応（Zig 言語特性に起因する永続的制約）

以下の Python 機能は Zig の言語設計上、変換対象外とする。

### 5.1 try/except/finally（例外処理）

Zig には例外機構がない。Python の `try/except/finally` は Zig に変換しない。

- `try` ブロック内のステートメントはそのまま emit する（ガード無しの直列実行）。
- `except` ハンドラは emit しない（到達不能扱い）。
- `finally` ブロック内のステートメントは `try` 本体の後にそのまま emit する。
- `raise` は `@panic()` に変換する（プロセス即終了）。
- 入力 Python で例外に依存するロジック（`except` で分岐するフロー）は、Zig backend では期待通りに動作しない。これは仕様上の制約とする。

### 5.2 クラス継承（composition パターン）

Zig には class 継承がないため、composition（委譲）パターンで変換する。

- 単一クラス（継承なし）は `struct` に変換する。
- `class Dog(Animal)` は `Dog` struct に `_base: Animal` フィールドを持たせる。
- 基底クラスのメソッドで override されていないものは、`self._base.method()` への委譲関数を自動生成する。
- `super().__init__()` は Pytra パーサーが現在非対応のため、変換できない。
- ポリモーフィズム（`Animal` 型変数に `Dog` を代入）は `&dog._base` でポインタを取得することで対応可能。ただし仮想ディスパッチ（override メソッドの動的呼び出し）は未対応。

### 5.3 isinstance / issubclass

Zig にはランタイム型検査がない。`isinstance` / `issubclass` は stub 実装（常に `false`）とする。

### 5.4 参照セマンティクス

Zig は値型が基本であり、Python の参照セマンティクス（オブジェクトの共有・エイリアス）を直接表現できない。

- 関数引数への代入がオリジナルに反映されない場合がある。
- この制約は Zig の言語設計に起因する永続的なものであり、ポインタ渡しへの変換は将来的な改善対象とする。

## 6. 検証観点（初期）

- `transpile_to_zig_native()` が EAST3 から `.zig` を生成できる。
- `check_py2x_transpile.py --target zig` で全 fixture の変換が成功する。
- `test/unit/backends/zig/test_py2zig_smoke.py` で基本テストが通る。
- core/control fixture の大半が `zig build-exe` でコンパイル・実行でき、Python と同一の stdout を出力する。
