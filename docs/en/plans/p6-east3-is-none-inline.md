<a href="../../ja/plans/p6-east3-is-none-inline.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p6-east3-is-none-inline.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p6-east3-is-none-inline.md`

# P6: py_is_none を EAST3 IR 経由インライン emit に移行し py_runtime.h から除去

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-EAST3-IS-NONE-INLINE-01`

## 背景

`py_is_none(v)` は `py_runtime.h` に 3 overload（`optional<T>` / 任意型 / `object`）で定義されており、C++ emitter が `v is None` 判定を文字列として直接 emit している。

- `optional<T>` → `!v.has_value()` に置き換え可能
- 確定型（int / str / list 等） → 常に `false`
- `object` → `!v`（rc ポインタの bool 変換）

EAST3 IR には `IsNone` 相当の意味論が存在し、emitter は型情報を持つため、型確定ケースでインライン展開し `py_is_none` 呼び出しを排除できる。

## 目的

- C++ emitter が `py_is_none(v)` を emit するすべての箇所を型ベースのインライン式に置き換える。
- `py_is_none` を `py_runtime.h` から削除する。

## 対象

- `src/toolchain/emit/cpp/emitter/`（`py_is_none` emit 箇所）
- `src/runtime/cpp/native/core/py_runtime.h`（除去対象関数）
- `tools/unittest/emit/cpp/`（回帰テスト）

## 非対象

- 非 C++ バックエンドへの対応
- `py_is_none` の挙動変更（現状維持）

## 受け入れ基準

- 生成 C++ に `py_is_none(...)` の呼び出しが残らない（生成コード内）。
- `py_is_none` が `py_runtime.h` から削除されている。
- fixture 3/3・sample 18/18 pass、selfhost diff mismatches=0。

## 決定ログ

- 2026-03-18: py_len/py_slice 除去（P6-EAST3-LEN-SLICE-NODE-01）後の次候補として起票。型分岐が明確で fallback 不要のため最もシンプルな候補。
