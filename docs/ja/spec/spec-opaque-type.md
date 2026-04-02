<a href="../../en/spec/spec-opaque-type.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Opaque 型仕様（extern class の型契約）

最終更新: 2026-04-03
ステータス: 確定（v1）

## 1. 目的

- `@extern class` で宣言された外部クラスを、Pytra の型システムで安全に扱う。
- 外部ライブラリ（SDL3 等）の handle / ポインタを rc で包まずにそのまま受け渡す。
- boxing / unboxing を発生させない。

## 2. 非目標

- opaque 型のフィールドアクセス。
- opaque 型に対する算術演算。
- opaque 型の継承。
- opaque 型のコンストラクタ直接呼び出し（factory メソッド経由のみ）。

## 3. 定義

`@extern class` で宣言され、本体にメソッドシグネチャのみを持つクラスは **opaque 型** として扱う。

```python
@extern
class Window:
    def set_title(self, title: str) -> None: ...
    def close(self) -> None: ...

@extern
class Renderer:
    def clear(self) -> None: ...
    def present(self) -> None: ...
```

opaque 型は以下の特徴を持つ:

- **rc で包まない**。ターゲット言語のネイティブ型（ポインタ、handle 等）としてそのまま扱う。
- **boxing しない**。`Object<void>` / `Any` にはならない。
- **名目型**。`Window` と `Renderer` は別の型であり、相互に代入できない。
- **type_id を持たない**。isinstance の対象外。
- **メソッド呼び出しは `@extern` で宣言されたもののみ**。opaque 型のメソッドは全て extern。

## 4. 型システム上の位置づけ

EAST の型カテゴリ:

| カテゴリ | rc | boxing | isinstance | 例 |
|---|---|---|---|---|
| POD | なし | なし | exact match | `int64`, `float64`, `bool`, `str` |
| クラス | あり | あり | type_id range check | ユーザー定義クラス |
| Any / object | あり | あり | — | `Any`, `object` |
| **opaque** | **なし** | **なし** | **不可** | `@extern class Window` |

opaque 型は通常のクラスと同じ `NamedType` で表現する。`OpaqueType` という専用 kind は使わない。opaque かどうかは `ClassDef.meta.opaque_v1` と `class_storage_hint: "opaque"` で判定する。

```json
{
  "kind": "NamedType",
  "name": "Window"
}
```

emitter は `class_storage_hint` を見て rc の要否を判断する:
- `"ref"` → `shared_ptr`（通常クラス）
- `"value"` → 値型
- `"opaque"` → 生ポインタ、rc なし

## 5. できること / できないこと

### できること

```python
@extern
class App:
    def create_window(self) -> Window: ...
    def destroy_window(self, win: Window) -> None: ...

@extern
class Window:
    def set_title(self, title: str) -> None: ...

if __name__ == "__main__":
    app: App = App()
    win: Window = app.create_window()
    win.set_title("hello")          # OK: Window の extern メソッド呼び出し
    app.destroy_window(win)          # OK: Window 型の引数に Window を渡す
```

- 同じ opaque 型を要求する引数にそのまま渡す
- `@extern` で宣言されたメソッドを呼ぶ
- 変数に代入する
- 関数の引数や戻り値として使う
- **コンテナに入れる**: `list[Window]`, `dict[str, Window]`, `set[Window]`
- **Optional にする**: `Window | None`（null ポインタに対応）
- **等値比較**: `win1 == win2`（ポインタ比較として扱う）

### できないこと

```python
    print(win)                       # NG: str 変換不可
    x: Any = win                     # NG: Any に boxing 不可
    isinstance(win, Window)          # NG: isinstance 不可
    win.width                        # NG: フィールドアクセス不可（extern メソッドのみ）
    if win:                          # NG: truthiness 判定不可
```

## 6. 各言語への写像

| 言語 | 写像 |
|---|---|
| C++ | ポインタ（`Window*`）。rc なし。 |
| Go | ポインタ（`*Window`）または unsafe.Pointer。rc なし。 |
| Rust | `*mut Window` または `Box<Window>`。rc なし。 |
| Java | オブジェクト参照（`Window`）。GC が管理。 |
| C# | オブジェクト参照（`Window`）。GC が管理。 |
| JS/TS | そのまま（`Window`）。GC が管理。 |

GC 言語では「rc なし」は自然（GC があるから）。C++/Rust/Go では生ポインタとして扱い、ライフタイム管理は外部ライブラリの責務。

## 7. EAST 表現

### extern class 宣言

```json
{
  "kind": "ClassDef",
  "name": "Window",
  "decorators": ["extern"],
  "meta": {
    "opaque_v1": {
      "schema_version": 1
    }
  },
  "body": [
    {
      "kind": "FunctionDef",
      "name": "set_title",
      "decorators": ["extern"],
      "args": [{"name": "self"}, {"name": "title", "type": "str"}],
      "return_type": "None"
    }
  ]
}
```

### opaque 型の変数

opaque 型の変数は通常のクラスと同じ `NamedType` で表現する。`OpaqueType` kind は使わない。

```json
{
  "kind": "Name",
  "id": "win",
  "resolved_type": "Window",
  "type_expr": {
    "kind": "NamedType",
    "name": "Window"
  }
}
```

### opaque 型のメソッド呼び出し

opaque 型のメソッドは通常の `Call` + `Attribute` として表現。`@extern` メソッドとして解決済み。

## 8. 決定事項（2026-04-03 確定）

- **`list[Window]` は許可する。** list は rc で管理するが、要素の Window は生ポインタ。C++ では `list<Window*>` になる。compile/resolve は opaque 型を `object` に退化させず、`NamedType("Window")` のまま保持すること。
- **`Optional[Window]`（`Window | None`）は許可する。** null ポインタの表現として自然。C++ では `Window*` が `nullptr` を取れるので追加コスト不要。
- **等値比較（`win1 == win2`）は許可する。** ポインタ比較として扱う。
- **コンストラクタ呼び出し（`Window()`）は factory メソッド経由のみ。** opaque 型の内部構造は不明なので、直接構築はできない。`App.create_window()` のような factory パターンを使う。
- **`@extern class` にフィールドを持たせるケースは opaque ではない。** フィールドを持つ `@extern class` は通常の extern クラス（`class_storage_hint: "ref"`）として扱い、opaque 型とは区別する。opaque 型はメソッドシグネチャのみ。

## 9. 関連

- [spec-type_id.md](./spec-type_id.md) — type_id 仕様（opaque 型は type_id を持たない）
- [spec-east.md](./spec-east.md) — EAST ノード仕様
- [spec-emitter-guide.md](./spec-emitter-guide.md) — emitter の写像規約
- [plans/p6-extern-method-redesign.md](../plans/p6-extern-method-redesign.md) — @runtime / @extern 再設計
