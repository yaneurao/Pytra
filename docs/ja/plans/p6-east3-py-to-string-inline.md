<a href="../../en/plans/p6-east3-py-to-string-inline.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P6: py_to_string を EAST3 IR 経由インライン emit に移行し py_runtime.h から除去

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-EAST3-PY-TO-STRING-INLINE-01`

## 背景

`py_to_string(v)` は `py_runtime.h` に 7 overload で定義されており、C++ emitter が `str(v)` ビルトイン呼び出しを文字列として直接 emit している。

- `int64` / `float64` 等算術型 → `std::to_string(v)` に置き換え可能
- `str` → identity（`v` そのまま）に置き換え可能
- `bool` → `"true"` / `"false"` リテラル or `(v ? "true" : "false")` にインライン可能
- `uint8` / `int8` → `std::to_string(static_cast<int>(v))` に置き換え可能
- `const char*` → `std::string(v)` に置き換え可能
- `optional<T>` → 型確定時は `v.has_value() ? py_to_string(*v) : "None"` にインライン可能
- `object` 境界 → fallback として維持

## 目的

- 型が確定している箇所で `py_to_string(v)` を標準 C++ 式にインライン置き換えする。
- `py_to_string` を `py_runtime.h` から削除する（object fallback は別ファイルへ）。

## 対象

- `src/toolchain/emit/cpp/emitter/`（`py_to_string` emit 箇所）
- `src/runtime/cpp/native/core/py_runtime.h`（除去対象関数）
- `tools/unittest/emit/cpp/`（回帰テスト）

## 非対象

- 非 C++ バックエンドへの対応
- float のフォーマット精度変更（現状維持）

## 受け入れ基準

- 生成 C++ に `py_to_string(...)` の型確定ケースが残らない（生成コード内）。
- `py_to_string` が `py_runtime.h` から削除されている（object fallback は別ファイルへ）。
- fixture 3/3・sample 18/18 pass、selfhost diff mismatches=0。

## 決定ログ

- 2026-03-18: py_len と同一パターン（型確定でインライン化、object 境界は fallback 維持）で起票。str() ビルトインの emit 路線整理。
- 2026-03-18: 実装完了。render_to_string() で算術型→std::to_string、str→identity、bool→三項演算子、Path→__str__() が既にインライン化済み。py_to_string を py_runtime.h から base_ops.h へ移動。object 境界の fallback は維持。241 test pass。
