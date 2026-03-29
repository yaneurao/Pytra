<a href="../../en/plans/p6-east3-py-to-inline.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P6: py_to<T> / py_to_int64 / py_to_float64 を EAST3 IR 経由インライン emit に移行し py_runtime.h から除去

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-EAST3-PY-TO-INLINE-01`

## 背景

`py_to<T>(v)` / `py_to_int64(v)` / `py_to_float64(v)` は `py_runtime.h` に定義されており、C++ emitter が型キャスト式を文字列として直接 emit している。

- 算術型間 → `static_cast<T>(v)` に置き換え可能
- `str` → `int64` → `std::stoll(v)` に置き換え可能
- `str` → `float64` → `std::stod(v.std())` に置き換え可能
- `object` 境界 → fallback として維持（`py_div` / `py_len` と同じ方針）

EAST3 IR はキャスト意味論を持ち、emitter は型情報を参照できるため、算術型確定ケースでインライン展開して `py_to` 呼び出しを排除できる。

`py_to_bool` については `truthy_len_expr` オーバーライド等で一部対処済みのため、残存 emit 箇所を個別に確認して対処する。

## 目的

- 算術型・str が確定している箇所で `py_to<T>` / `py_to_int64` / `py_to_float64` を `static_cast` / `std::stoll` / `std::stod` にインライン置き換えする。
- `py_to<T>` 等を `py_runtime.h` から削除する（object 境界 fallback は `scalar_ops.h` 等へ移動）。

## 対象

- `src/toolchain/emit/cpp/emitter/`（`py_to` emit 箇所）
- `src/runtime/cpp/native/core/py_runtime.h`（除去対象関数）
- `tools/unittest/emit/cpp/`（回帰テスト）

## 非対象

- 非 C++ バックエンドへの対応
- `py_to_bool` の全面置き換え（残存箇所を確認の上、必要に応じて本タスクに含める）

## 受け入れ基準

- 生成 C++ に `py_to<T>(...)` / `py_to_int64(...)` / `py_to_float64(...)` の型確定ケースが残らない（生成コード内）。
- 対象関数が `py_runtime.h` から削除されている（object fallback は別ファイルへ）。
- fixture 3/3・sample 18/18 pass、selfhost diff mismatches=0。

## 決定ログ

- 2026-03-18: py_div（P5）・py_len（P6）と同一パターン（算術型確定でインライン化、object 境界は fallback 維持）で実績あり。起票。
