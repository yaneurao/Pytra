# P0-EXCEPTION-GO: Go backend の例外処理実装

最終更新: 2026-03-28
ステータス: 未着手

## 背景

Go にはネイティブ例外がないため、Python の `raise` / `try/except/finally` を戻り値 union（`T | PytraError`）に自動変換する必要がある。Go selfhost では toolchain コードが try/except を使っており、これがブロッカーになりうる。

spec-exception.md §5 に従い、linker のマーカー付与 + EAST3 lowering の ErrorReturn/ErrorCheck/ErrorCatch + Go emitter の写像を実装する。

## サブタスク

1. [ID: P0-EXCEPTION-GO-S1] Go runtime に `PytraError` / `PytraValueError` / `PytraRuntimeError` クラス階層を実装する — struct embedding + `pytraErrorIsInstance(err, tidMin, tidMax)` 関数
2. [ID: P0-EXCEPTION-GO-S2] linker に `can_raise_v1` マーカーの推移的付与を実装する — call graph 走査で raise を含む関数を特定し、try/except なしの呼び出し元に推移的にマーカーを伝播
3. [ID: P0-EXCEPTION-GO-S3] EAST3 言語別 lowering で `exception_style: "union_return"` の場合に `Raise` → `ErrorReturn`、`ErrorCheck`（propagate/catch）、`ErrorCatch` ノードを生成する
4. [ID: P0-EXCEPTION-GO-S4] Go emitter で `ErrorReturn` / `ErrorCheck` / `ErrorCatch` を写像する — `(T, *PytraError)` 戻り値、`if _err != nil` 伝播、type_id range check による isinstance、`defer` による finally
5. [ID: P0-EXCEPTION-GO-S5] fixture 追加（raise/try/except/finally、ユーザー定義例外、複数 handler、ネスト）+ Go parity 確認

## 受け入れ基準

1. `raise ValueError("msg")` が Go で `return _zero, &PytraValueError{...}` に変換されること
2. `try/except ValueError` が Go で type_id range check による isinstance 判定になること
3. `except ValueError` が ValueError の派生クラス（ParseError 等）も catch すること
4. `finally` が Go の `defer` に写像され、正常/エラー両方で実行されること
5. 既存 fixture + sample の Go parity が維持されること

## 決定ログ

- 2026-03-28: Go/Rust/Zig の例外処理を union_return 方式で実装する方針を決定。例外型は通常のクラス（type_id 付き）として扱い、isinstance は type_id range check で判定。spec-exception.md に詳細仕様を記載。
