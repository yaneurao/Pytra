# TODO（未完了のみ）

## 1. Any/object 方針への移行（最優先）

- [x] `src/cpp_module/py_runtime.h` に `using object = rc<PyObj>;` を導入する。
- [x] `Any -> object` 変換のためのボックス型を実装する。
- [x] `PyIntObj` / `PyFloatObj` / `PyBoolObj` / `PyStrObj`
- [x] `PyListObj` / `PyDictObj`（`list<object>` / `dict<str, object>` ベース）
- [x] `make_object(...)` / `obj_to_int64` / `obj_to_float64` / `obj_to_bool` / `obj_to_str` を実装する。
- [x] `py_is_none(object)` を実装し、null `object` 判定を統一する。
- [x] `py_to_string(object)` を実装する。

## 2. py2cpp 側の Any lowering 更新

- [x] `src/py2cpp.py` の `cpp_type()` で `Any` / `object` を `object` 型へ解決する。
- [x] `dict[str, Any]` を `dict<str, object>` に変換する。
- [x] `list[Any]` を `list<object>` に変換する。
- [x] `Any` 代入時に `make_object(...)` を生成する。
- [x] `Any` 利用演算時に明示的 unbox (`obj_to_*`) を生成する。
- [x] `Any is None` / `Any is not None` を `py_is_none` ベースへ統一する。

## 3. selfhost 回復

- [x] `selfhost/py2cpp.cpp` を再生成し、現時点のコンパイルエラー件数を計測する。
  - 計測値: `305` errors（`g++ -std=c++20 -O2 -I src selfhost/py2cpp.cpp ...`）
- [ ] `Any -> object` 移行後の `selfhost` コンパイルを通す。
- [ ] `selfhost` で `sample/py/01` を変換できることを確認する。
  - 現状メモ: `PYTHONPATH=src python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp` で
    `unsupported_syntax: expected token EOF, got NAME`（`except ValueError:` 付近）により EAST 生成が停止。

## 4. 内包表現・lambda の追加回帰

- [x] `test/fixtures/collections` に内包表現の追加ケースを増やす。
- [x] 二重内包（nested comprehension）
- [x] `if` 句を複数持つ内包
- [x] `range(start, stop, step)` を使う内包
- [x] `test/fixtures/core` に lambda の追加ケースを増やす。
- [x] `lambda` 本体が `ifexp` を含むケース
- [x] 外側変数 capture + 複数引数
- [x] 関数引数として lambda を渡すケース
- [x] 上記を `test/unit/test_py2cpp_features.py` の C++ 実行回帰に追加する。

## 5. ドキュメント更新

- [x] `docs/spec-east.md` に `Any -> object(rc<PyObj>)` 方針を明記する。
- [x] `docs/spec.md` に `Any` の制約（boxing/unboxing, None 表現）を追記する。
- [x] `readme.md` に `Any` 実装状況（移行中）を明記する。
