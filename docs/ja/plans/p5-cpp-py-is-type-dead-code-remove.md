# P5: py_is_dict 等デッドコード関数を py_runtime.h から除去

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-CPP-PY-IS-TYPE-DEAD-CODE-REMOVE-01`

## 背景

`py_runtime.h` には `py_is_dict` / `py_is_list` / `py_is_set` / `py_is_str` / `py_is_bool` / `py_is_int` / `py_is_float` の型述語が定義されているが、C++ emitter はこれらを一切 emit していない。

`isinstance` 判定は P5-ANY-ELIM-OBJECT-FREE-01 以前から `py_runtime_value_isinstance(x, PYTRA_TID_INT)` 等の `PYTRA_TID_*` 体系に移行済みであり、`py_is_*` は `Any` 廃止以前の遺物として残っている。
`test_py2cpp_codegen_issues.py` に `assertNotIn("return py_is_int(x);"` のアサートがあり、emitter が生成しないことは既にテストで保証されている。

`py_is_none` だけは `x is None` 比較の emit で現役のため除去対象外。

## 目的

- `py_is_dict` / `py_is_list` / `py_is_set` / `py_is_str` / `py_is_bool` / `py_is_int` / `py_is_float` を `py_runtime.h` から削除する。
- 参照しているテストコード（`test_cpp_runtime_iterable.py:140` の `py_is_list(typed_iter)` アサート）を修正する。

## 対象

- `src/runtime/cpp/native/core/py_runtime.h`（7 関数群の定義を削除）
- `test/unit/backends/cpp/test_cpp_runtime_iterable.py`（直接参照 1 件を修正）

## 非対象

- `py_is_none`（`is None` 比較で emit 中。残す）
- `py_runtime_value_isinstance` / `PYTRA_TID_*` 体系（変更なし）
- 非 C++ バックエンド

## 受け入れ基準

- `py_runtime.h` に `py_is_dict` / `py_is_list` / `py_is_set` / `py_is_str` / `py_is_bool` / `py_is_int` / `py_is_float` が存在しない。
- `py_is_none` は残っておりコンパイルが通る。
- 既存ユニットテストが全て通る（`test_cpp_runtime_iterable.py` の修正含む）。
- selfhost diff mismatches=0。

## 子タスク（案）

- [ ] [ID: P5-CPP-PY-IS-TYPE-DEAD-CODE-REMOVE-01-S1-01] `py_runtime.h` から 7 関数群を削除し、`test_cpp_runtime_iterable.py` の直接参照を修正してテストが通ることを確認する。
- [ ] [ID: P5-CPP-PY-IS-TYPE-DEAD-CODE-REMOVE-01-S1-02] selfhost diff で非退行を確認する。

## 決定ログ

- 2026-03-18: py_runtime.h 縮小調査にて emitter からの呼び出しがゼロであることを確認し起票。`PYTRA_TID_*` + `py_runtime_value_isinstance` への移行が P5-ANY-ELIM-OBJECT-FREE-01 以前に完了していたことが判明。`py_is_none` のみ `cpp_emitter.py:3544/3547` で emit 中のため残置。
