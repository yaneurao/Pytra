# P0-EXCEPTION-CPP: C++ backend の例外処理実装（CommonRenderer 連携）

最終更新: 2026-03-28
ステータス: 未着手

## 背景

C++ はネイティブ例外（throw/try-catch）を持つため、`exception_style: "native_throw"` で EAST3 の `Raise` / `Try` をそのまま写像する。CommonRenderer の共通骨格を使い、C++ emitter は構文トークンの override だけで実装する。

## サブタスク

1. [ID: P0-EXCEPTION-CPP-S1] CommonRenderer に `emit_raise` / `emit_try` の共通骨格を実装する — `native_throw` 言語向けのノード走査（Raise → throw 式生成、Try → try ブロック + handler 分岐 + finally）
2. [ID: P0-EXCEPTION-CPP-S2] C++ emitter で `Raise` → `throw ExceptionType("msg")` の写像を override する
3. [ID: P0-EXCEPTION-CPP-S3] C++ emitter で `Try` → `try { } catch (ExceptionType& e) { }` の写像を override する — `except ValueError` が派生クラスも catch する（C++ の catch は継承で自然に動作）
4. [ID: P0-EXCEPTION-CPP-S4] C++ emitter で `finally` を RAII / スコープガードに写像する
5. [ID: P0-EXCEPTION-CPP-S5] fixture 追加（raise/try/except/finally、ユーザー定義例外、複数 handler）+ C++ compile + run parity 確認

## 設計ノート

- C++ の `catch (ValueError& e)` は C++ の継承により派生クラスも自然に catch する。type_id range check は不要。
- `finally` は C++ にネイティブ構文がない。スコープガード（RAII パターン）で実現する:
  ```cpp
  {
      auto _finally = pytra_scope_guard([&]() { cleanup(); });
      try { ... } catch (...) { ... }
  }
  ```
- CommonRenderer の `emit_raise` / `emit_try` 骨格は Go の `union_return` とは別パス。`native_throw` 言語（Java, C#, Kotlin 等）も同じ骨格を使う。

## 受け入れ基準

1. `raise ValueError("msg")` が C++ で `throw PytraValueError("msg")` に変換されること
2. `try/except/finally` が C++ で `try/catch` + スコープガードに変換されること
3. `except ValueError` が ValueError の派生クラスも catch すること（C++ 継承による自然な動作）
4. CommonRenderer の `emit_raise` / `emit_try` 骨格が実装され、C++ emitter は override だけで構成されること
5. 既存 fixture + sample の C++ parity が維持されること

## 決定ログ

- 2026-03-28: C++ は native_throw で実装。CommonRenderer の共通骨格を先に作り、C++ emitter は override のみとする方針。finally は RAII スコープガードで対応。
