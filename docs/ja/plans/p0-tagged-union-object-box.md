# P0: tagged union を object + type_id に統一

最終更新: 2026-03-20

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-TAGGED-UNION-OBJECT-BOX-01`

## 背景

現在 tagged union（`str | Path` 等）は型ごとに専用 struct を生成している:

```cpp
struct _Union_str_Path {
    pytra_type_id tag;
    str str_val;
    Path path_val;  // ← Path の完全定義が必要
};
```

これにより:
1. **前方参照問題**: `_Union_str_Path` が `Path` より先に定義される必要があるが、`Path` のコンストラクタが `_Union_str_Path` を引数に取る。相互依存で解決不能。
2. **全バックエンド共通**: 値型セマンティクスの言語（C++, Rust, Go, Swift）全てで発生。
3. **struct 肥大化**: メンバ数分のフィールドを持つ。

## 設計

### 原則

- tagged union は `PyTaggedValue`（`type_id` + `object`）1 つで表現する。
- 型ごとの `_Union_*` struct は生成しない。`using X = PyTaggedValue;` の typedef だけ。
- tagged union の値は必ず `isinstance` で型を確認した後に **unbox してから使う**。`object` のまま演算は禁止。

### 値の格納方法

| メンバの種類 | 格納方法 | 理由 |
|-------------|---------|------|
| ユーザー定義クラス（`Path` 等） | `rc<T>` → `object` にアップキャスト | クラスは基本 `rc<T>`（gc_managed）。`object` にそのまま入る。 |
| POD（`str`, `int`, `float`, `bool`） | `PyBoxed<T, TID>` で wrap → `object` | POD は `RcObject` を継承しないので box が必要。 |

### box / unbox

```cpp
// runtime に定義（core/tagged_value.h）
template <class T, pytra_type_id TID>
struct PyBoxed : RcObject {
    T value;
    explicit PyBoxed(const T& v) : value(v) {}
    pytra_type_id py_type_id() const noexcept override { return TID; }
};

template <class T, pytra_type_id TID>
object py_box(const T& v) { return object(new PyBoxed<T, TID>(v)); }

template <class T, pytra_type_id TID>
const T& py_unbox(const object& v) { return static_cast<PyBoxed<T, TID>*>(v.get())->value; }
```

POD の box/unbox のみ `PyBoxed` を使う。クラスは `object` への直接 upcast / downcast。

### PyTaggedValue

```cpp
struct PyTaggedValue {
    pytra_type_id tag;
    object value;
};
```

全 tagged union がこの struct を共有。`using JsonVal = PyTaggedValue;` のように typedef する。

### emitter の変更

| 操作 | 現在 | 変更後 |
|------|------|--------|
| union 型宣言 | `struct _Union_str_Path { ... };` | `using _Union_str_Path = PyTaggedValue;` |
| POD を union に入れる | `_Union_str_Path("hello")` | `PyTaggedValue{PYTRA_TID_STR, py_box<str, PYTRA_TID_STR>("hello")}` |
| クラスを union に入れる | `_Union_str_Path(path)` | `PyTaggedValue{Path::PYTRA_TYPE_ID, path}` （`rc<Path>` → `object` upcast） |
| isinstance | `v.tag == PYTRA_TID_STR` | `v.tag == PYTRA_TID_STR`（変更なし） |
| cast (POD) | `v.str_val` | `py_unbox<str, PYTRA_TID_STR>(v.value)` |
| cast (クラス) | `v.path_val` | `static_cast<Path*>(v.value.get())` or `rc<Path>(v.value)` |
| is None | `v.tag == PYTRA_TID_NONE` | `v.tag == PYTRA_TID_NONE`（変更なし） |

### unbox 制約

- `object` のまま演算（`+`, `.method()` 等）を呼ぶことは禁止。
- emitter は `isinstance` 分岐で narrow された型で emit する。
- EAST3 の型推論が narrow を追跡しているので、emitter 側の変更は最小限。

### 性能

- クラスの格納: `rc<T>` → `object` は参照カウント操作のみ（コピーなし）。
- POD の格納: `PyBoxed` 経由でヒープ確保が入る。
- EAST3 optimizer の non-escape 解析で、box → 即 unbox のパターンはスタック配置に最適化可能（将来）。

### 各バックエンドの表現

| バックエンド | 表現 |
|-------------|------|
| C++ | `PyTaggedValue` (`pytra_type_id` + `object`) |
| Rust | `Box<dyn Any>` + type_id、または enum（Box 化） |
| Go | `interface{}` + type assertion |
| Java/C#/Kotlin | `Object` + `instanceof`（既に参照型） |
| Swift | `indirect enum` |
| JS/TS | そのまま（動的型付き） |

### 削除対象

- `_Union_*` struct の自動生成ロジック（型ごとのフィールド + コンストラクタ生成）→ typedef に置換済み
- `_tagged_union_field_name` によるフィールドアクセス → `py_unbox` / downcast に置換

## 対象ファイル

| ファイル | 変更 |
|---------|------|
| `src/toolchain/emit/cpp/emitter/cpp_emitter.py` | `_Union_*` struct 生成を `object + tag` に変更 |
| `src/toolchain/emit/cpp/emitter/type_bridge.py` | tagged union 型の C++ 表現を変更 |
| `src/toolchain/emit/cpp/emitter/header_builder.py` | union struct 生成除去 |
| `src/toolchain/compile/` | EAST3 レベルでの tagged union 表現検討 |
| 各バックエンド emitter | 同様の変更 |

## 受け入れ基準

- [ ] tagged union が `object + type_id` で表現される（型ごとの struct 不要）。
- [ ] `str | Path` のような自己参照 union が前方参照問題なしにコンパイルできる。
- [ ] unbox 制約: `object` のまま演算を emit しない。
- [ ] `pathlib.py` の `out/cpp/` g++ ビルドが通る。
- [ ] `check_py2x_transpile --target cpp` pass。

## 子タスク

- [x] [ID: P0-TAGGED-UNION-OBJECT-BOX-01-S1] tagged union 宣言を `using X = PyTaggedValue;` に変更。`_Union_*` struct 生成を除去。`core/tagged_value.h` に `PyBoxed`/`py_box`/`py_unbox`/`PyTaggedValue` を追加。
- [x] [ID: P0-TAGGED-UNION-OBJECT-BOX-01-S2] emitter の cast を変更。POD は `py_unbox<T, TID>(v.value)`、クラスは `(*static_cast<T*>(v.value.get()))` を emit。
- [ ] [ID: P0-TAGGED-UNION-OBJECT-BOX-01-S3] isinstance narrow 後の暗黙代入で unbox を emit。`s: str = v`（`v: PyTaggedValue`）→ `str s = py_unbox<str, PYTRA_TID_STR>(v.value);`。emitter が narrow 後の型変換を検出し unbox/downcast を挿入する。
- [ ] [ID: P0-TAGGED-UNION-OBJECT-BOX-01-S4] 関数呼び出し時の暗黙 box を emit。`show("hello")`（`show(PyTaggedValue)`）→ `show(PyTaggedValue{PYTRA_TID_STR, py_box<str, PYTRA_TID_STR>("hello")})`。emitter が引数の型不一致を検出し box を挿入する。
- [ ] [ID: P0-TAGGED-UNION-OBJECT-BOX-01-S5] `pathlib.py` を含む `out/cpp/` g++ ビルドを検証する。
- [ ] [ID: P0-TAGGED-UNION-OBJECT-BOX-01-S6] 他バックエンド（Rust, Go 等）への展開を検討する。

## 決定ログ

- 2026-03-20: `pathlib.h` の g++ ビルドで `_Union_str_Path` ↔ `Path` の相互依存が発覚。tagged union struct のフィールドが incomplete type を持てない問題。
- 2026-03-20: 全バックエンド共通の問題であることを確認。値型セマンティクスの言語全てで発生。
- 2026-03-20: ユーザー提案: tagged union は `object` (rc) + `type_id` だけ持ち、unbox して使う。POD 以外をボックス化するより、全部 object + tag で統一する方がシンプル。unbox してしか使わない制約を入れる。
- 2026-03-20: box/unbox テンプレート設計。`PyBoxed<T, TID>` で POD を wrap、クラスは `rc<T>` → `object` に直接 upcast（`PyBoxed` 不要）。ユーザー定義クラスは基本 `rc<T>`（gc_managed）なので `object` にそのまま入る。value 型最適化は EAST3 optimizer の non-escape 解析で rc が外れた後の話。
- 2026-03-20: S1 完了（typedef 化 + runtime ヘッダー追加）。S2-S3（cast/構築の emit 変更）が残課題。
