# P0: object = tagged value 統一

最終更新: 2026-03-20

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-OBJECT-IS-TAGGED-VALUE-01`

## 背景

現在の C++ runtime には 3 つの「任意の値を持てる型」がある:

1. `object` = `rc<RcObject>` — gc_managed クラスのみ格納可能。POD (`str`, `int` 等) は入らない。
2. `PyTaggedValue` = `{pytra_type_id tag; object value;}` — tagged union 用に新設。POD は `PyBoxed` 経由で `object` に入れる。
3. `Any` — Python の `Any` に対応。現在は `object` と同じ。

Python では `object` はまさに「type_id + 値」であり、tagged union と同じ構造。これらを統一する。

## 設計

### 原則

- **`object` = `PyTaggedValue`**。`object` が `type_id` + 値を持つ唯一の型。
- **tagged union は `object`**。`str | int` も `str | Path` も `Any` も全部 `object`。union ごとの typedef (`_Union_*`, `using X = PyTaggedValue`) は不要。
- **box / unbox は `object` のメソッド**。

### object の新しい定義

```cpp
struct object {
    pytra_type_id tag;
    rc<RcObject> value;  // boxed data

    object() : tag(PYTRA_TID_NONE), value() {}

    // 暗黙変換コンストラクタ（POD → box）
    object(const str& v) : tag(PYTRA_TID_STR), value(new PyBoxed<str, PYTRA_TID_STR>(v)) {}
    object(const char* v) : tag(PYTRA_TID_STR), value(new PyBoxed<str, PYTRA_TID_STR>(str(v))) {}
    object(int64 v) : tag(PYTRA_TID_INT), value(new PyBoxed<int64, PYTRA_TID_INT>(v)) {}
    object(int v) : tag(PYTRA_TID_INT), value(new PyBoxed<int64, PYTRA_TID_INT>(static_cast<int64>(v))) {}
    object(float64 v) : tag(PYTRA_TID_FLOAT), value(new PyBoxed<float64, PYTRA_TID_FLOAT>(v)) {}
    object(bool v) : tag(PYTRA_TID_BOOL), value(new PyBoxed<bool, PYTRA_TID_BOOL>(v)) {}

    // クラス型（rc<T>）→ upcast
    template <class T, std::enable_if_t<std::is_base_of_v<RcObject, T>, int> = 0>
    object(const rc<T>& v) : tag(v ? v->py_type_id() : PYTRA_TID_NONE), value(v) {}

    // monostate = None
    object(std::monostate) : tag(PYTRA_TID_NONE), value() {}

    // unbox
    template <class T, pytra_type_id TID>
    const T& unbox() const { return static_cast<PyBoxed<T, TID>*>(value.get())->value; }

    // unbox for class types (downcast)
    template <class T>
    T* as() const { return static_cast<T*>(value.get()); }

    // bool conversion
    explicit operator bool() const { return tag != PYTRA_TID_NONE; }

    // isinstance
    bool is(pytra_type_id expected) const { return tag == expected; }
};
```

### emitter の変更

| 現在 | 変更後 |
|------|--------|
| `str \| int` → `_Union_str_int64` | `str \| int` → `object` |
| `using _Union_str_int64 = PyTaggedValue;` | 削除（typedef 不要） |
| `PyTaggedValue{TID, py_box(v)}` | `object(v)`（暗黙変換） |
| `py_unbox<str, TID>(v.value)` | `v.unbox<str, PYTRA_TID_STR>()` |
| `v.tag == PYTRA_TID_STR` | `v.is(PYTRA_TID_STR)` or `v.tag == PYTRA_TID_STR` |
| `(*static_cast<T*>(v.value.get()))` | `(*v.as<T>())` |
| `_tagged_union_types` レジストリ | 削除（union は全て `object`） |
| `_inline_union_structs` | 削除 |
| `_tagged_union_has_none` | 削除 |

### 影響範囲

| ファイル | 変更 |
|---------|------|
| `src/runtime/cpp/core/py_types.h` | `object` の定義を `PyTaggedValue` ベースに変更 |
| `src/runtime/cpp/core/tagged_value.h` | `PyBoxed` テンプレートは残す。`PyTaggedValue` struct は `object` に統合して削除。 |
| `src/backends/cpp/emitter/type_bridge.py` | union 型 → `object` を返す。`_inline_union_structs` 廃止。 |
| `src/backends/cpp/emitter/cpp_emitter.py` | `_emit_tagged_union_struct` 廃止。`_tagged_union_types` レジストリ廃止。 |
| `src/backends/cpp/emitter/call.py` | `_try_render_tagged_union_cast` を `object::unbox` / `object::as` に変更。 |
| `src/backends/cpp/emitter/runtime_expr.py` | isinstance を `v.tag ==` or `v.is()` に変更。 |
| `src/backends/cpp/emitter/stmt.py` | 暗黙 unbox を `object::unbox` に変更。 |
| `src/runtime/cpp/core/type_id_support.h` | `py_runtime_value_isinstance` 等を `object::is` ベースに統合。 |

### 既存 `object` (`rc<RcObject>`) との互換

現在 `object` = `rc<RcObject>` を直接使っている箇所が多数ある。段階的に移行:

1. **Phase 1**: `object` の定義を変更し、`rc<RcObject>` を `value` メンバに持つ struct にする。`object` → `rc<RcObject>` の暗黙変換と逆方向を用意して既存コードを壊さない。
2. **Phase 2**: emitter が union 型に `object` を emit するよう変更。`_Union_*` 廃止。
3. **Phase 3**: 既存コードの `object` 使用箇所を新 API (`unbox`, `as`, `is`) に移行。
4. **Phase 4**: 互換レイヤ除去。

### `Any` 型との統一

`Any` = `object`。型注釈 `Any` は C++ では `object` に変換される。これは現在も同じ。`object` が tagged value になることで、`Any` の値にも type_id が付き、isinstance が正確に動作する。

## 非対象

- 非 C++ バックエンド（本タスクは C++ のみ。他バックエンドは後続。）
- `object` のメモリレイアウト最適化（small buffer optimization 等。将来検討。）

## 受け入れ基準

- [ ] `object` が `type_id` + `rc<RcObject>` の struct として定義されている。
- [ ] tagged union 型が `object` として emit される（`_Union_*` typedef 不要）。
- [ ] `f(v: str | int)` が `f(object v)` に変換される。
- [ ] box / unbox が `object` のメソッドで完結する。
- [ ] `pathlib.py` を含む `out/cpp/` g++ ビルドが通る。
- [ ] `check_py2x_transpile --target cpp` pass。

## 子タスク

- [ ] [ID: P0-OBJECT-IS-TAGGED-VALUE-01-S1] `object` の定義を `{pytra_type_id tag; rc<RcObject> value;}` に変更する。暗黙変換コンストラクタ、`unbox`, `as`, `is` メソッドを追加。既存 `rc<RcObject>` 互換レイヤを用意。
- [ ] [ID: P0-OBJECT-IS-TAGGED-VALUE-01-S2] emitter が union 型に `object` を emit するよう変更。`_Union_*` typedef 生成、`_tagged_union_types` / `_inline_union_structs` レジストリを廃止。
- [ ] [ID: P0-OBJECT-IS-TAGGED-VALUE-01-S3] emitter の cast / isinstance / 暗黙代入を `object::unbox` / `object::as` / `object::is` に変更。
- [ ] [ID: P0-OBJECT-IS-TAGGED-VALUE-01-S4] `pathlib.py` を含む `out/cpp/` g++ ビルドを検証する。
- [ ] [ID: P0-OBJECT-IS-TAGGED-VALUE-01-S5] 既存コードの `object` 使用箇所を新 API に移行し、互換レイヤを除去する。

## 決定ログ

- 2026-03-20: tagged union を `PyTaggedValue` (`type_id` + `object`) に統一する方針で S1-S4 を実装。
- 2026-03-20: ユーザーから「`PyTaggedValue` こそが `object` であるべき。box/unbox もメソッドとして持つ。union ごとの typedef は不要で、全て `object`」と提案。`object` = tagged value の設計で P0 最優先として起票。
