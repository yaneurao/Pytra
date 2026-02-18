# TODO

## 最優先方針（確定）

- `Any -> std::any` は廃止する。
- `Any -> object` とし、`object` は GC 管理対象（`rc<PyObj>`）で表現する。
- `None` は `object` の null（空ハンドル）として扱う。

## フェーズ1: ランタイム土台（`src/cpp_module/py_runtime.h`）

- [ ] `object` の型エイリアスを導入する（`using object = rc<PyObj>;`）。
- [ ] `PyObj` 派生のボックス型を実装する。
- [ ] `PyIntObj`（`int64`）
- [ ] `PyFloatObj`（`float64`）
- [ ] `PyBoolObj`（`bool`）
- [ ] `PyStrObj`（`str`）
- [ ] `PyListObj`（`list<object>`）
- [ ] `PyDictObj`（`dict<str, object>`）
- [ ] `PySetObj`（`set<object>` または当面 `set<str>` 制約）
- [ ] `make_object(...)` ヘルパを実装する（プリミティブ/コンテナ -> `object`）。
- [ ] `object` からの取り出しヘルパを実装する。
- [ ] `obj_to_int64`
- [ ] `obj_to_float64`
- [ ] `obj_to_bool`
- [ ] `obj_to_str`
- [ ] `obj_to_dict`
- [ ] `obj_to_list`
- [ ] `py_is_none(object)` / `py_is_none(rc<...>)` を統一実装する。
- [ ] `py_to_string(object)` を実装する。
- [ ] `py_dict_get_default(dict<str, object>, ...)` を実装する。

## フェーズ2: 型変換（`src/py2cpp.py`）

- [ ] `cpp_type()` で `Any` / `object` を `object` 型へ解決する。
- [ ] `dict[str, Any]` を `dict<str, object>` に変換する。
- [ ] `list[Any]` を `list<object>` に変換する。
- [ ] `set[Any]` の当面方針を定義する（制限付きでも可）。
- [ ] `T | None` の扱いを整理する。
- [ ] `Any | None` は `object` の null で表現（`optional` を使わない）。
- [ ] `非Any` の `T | None` は現行どおり `optional<T>` を維持するか決定。

## フェーズ3: 式/文 lowering 修正（`src/py2cpp.py`）

- [ ] `Any` 代入時に `make_object(...)` を生成する。
- [ ] `Any` の算術・比較時に明示的 unbox ヘルパを生成する。
- [ ] `dict[str, Any].get(...).items()` が `object` 経由で動作するように生成する。
- [ ] `Any` 経由 `is None` / `is not None` を `py_is_none` に統一する。
- [ ] `boolop` 値選択（`x or y`, `x and y`）で `object` truthy 判定を使う。
- [ ] `str()` / `int()` / `float()` の `Any` 引数を `object` 経由変換へ統一する。

## フェーズ4: テスト拡張

- [ ] `test/fixtures/typing/any_basic.py` を新仕様（`object`）で通す。
- [ ] `test/fixtures/typing` に追加する。
- [ ] `any_none.py`（`is None` / `is not None`）
- [ ] `any_dict_items.py`（`dict[str, Any].get(...).items()`）
- [ ] `any_list_mixed.py`（`list[Any]` の混在要素）
- [ ] `any_class_refcount.py`（`Any` にクラスインスタンスを入れて参照カウント確認）
- [ ] `test/unit/test_py2cpp_features.py` に `Any` 系の C++実行回帰を追加する。

## フェーズ5: selfhost 回復

- [ ] `selfhost/py2cpp.cpp` を再生成し、コンパイルエラーを再計測する。
- [ ] `std::any` 由来エラーが消えていることを確認する。
- [ ] `sample/py/01` 変換まで selfhost 実行を通す。
- [ ] `src/py2cpp.py` 生成結果との一致比較を行う（仕様に定義した一致条件で判定）。

## ドキュメント更新

- [ ] `docs/spec-east.md` に `Any -> object(rc<PyObj>)` を明記する。
- [ ] `docs/spec-user.md` に `Any` の制約/仕様を追記する。
- [ ] `docs/how-to-use.md` に selfhost 検証手順（`cpp_module` 同期含む）を維持更新する。

## 進捗メモ

- 2026-02-18 時点の旧方針（`Any -> std::any`）は破棄する。
- 以後は `object(rc<PyObj>)` 方針のみで実装を進める。
