<a href="../../ja/plans/p5-lua-backend-emit-fix.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p5-lua-backend-emit-fix.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p5-lua-backend-emit-fix.md`

# P5: Lua バックエンドの emit 失敗修正

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-LUA-BACKEND-EMIT-FIX-01`

## 背景

`src/pytra/std/collections.py`（Deque クラス）を Lua バックエンドで transpile すると
空テキスト（0 bytes）が出力される。他の 13 バックエンドでは正常に生成される。

Lua emitter の基盤に問題がある可能性。

## 対象

- `src/toolchain/emit/lua/emitter/lua_native_emitter.py` — emit 失敗箇所の特定・修正
- Lua runtime の generated 出力

## 受け入れ基準

- `pytra.std.collections` (Deque) が Lua で transpile され、非空の出力が生成される。
- 既存の Lua fixture / sample が pass すること。

## 決定ログ

- 2026-03-19: collections.py の全バックエンド生成時に Lua のみ 0 bytes 出力を確認。起票。
