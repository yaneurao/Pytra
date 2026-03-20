# P0: tagged union の tag を PYTRA_TID に統一

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-TAGGED-UNION-TID-UNIFY-01`

## 背景

P1-TAGGED-UNION-ALL-BACKENDS-01 で `type X = A | B | ...` から C++ tagged struct を生成する仕組みを導入した。
現在の tagged struct はローカル enum Tag を使用している：

```cpp
struct ArgValue {
    enum Tag { TAG_STR, TAG_BOOL, TAG_NONE };  // ローカルな 0, 1, 2
    Tag tag;
};
```

一方、Pytra にはクラス継承の isinstance 判定用に DFS オーダーベースの type_id レンジ方式
（`PYTRA_TID_*` 定数 + `py_tid_is_subtype(actual, expected)` 関数）が既に存在する。

tagged union の tag をこの既存 type_id と統一することで、isinstance を1つの仕組みで実現できる。

## 現状の問題

1. tagged union の isinstance（`isinstance(v, int)` where `v: JsonVal`）が未実装
2. tagged union と class 継承で isinstance が別メカニズムになる
3. tagged union メンバがクラス型の場合、継承関係を尊重した isinstance ができない

## 修正方針

### ステップ 1: tagged struct の tag 型を uint32 に変更

```cpp
struct JsonVal {
    uint32 tag;  // PYTRA_TID_* を直接使用
    // fields...

    JsonVal() : tag(PYTRA_TID_NONE) {}
    JsonVal(const str& v) : tag(PYTRA_TID_STR), str_val(v) {}
    JsonVal(int64 v) : tag(PYTRA_TID_INT), int64_val(v) {}
    // ...
};
```

各 union メンバの tag 値：

| union メンバ | tag 値 |
|-------------|--------|
| `None` | `PYTRA_TID_NONE (0)` |
| `bool` | `PYTRA_TID_BOOL (1)` |
| `int` | `PYTRA_TID_INT (2)` |
| `float` | `PYTRA_TID_FLOAT (3)` |
| `str` | `PYTRA_TID_STR (4)` |
| `list[T]` | `PYTRA_TID_LIST (5)` |
| `dict[K,V]` | `PYTRA_TID_DICT (6)` |
| `set[T]` | `PYTRA_TID_SET (7)` |
| ユーザークラス | `ClassName::PYTRA_TYPE_ID (1000+)` |

### ステップ 2: isinstance の統一

tagged union 変数への isinstance を既存の `py_tid_is_subtype` で判定する。

```python
isinstance(v, int)  # v: JsonVal
```
↓ C++
```cpp
py_tid_is_subtype(v.tag, PYTRA_TID_INT)
// または簡易ケース: v.tag == PYTRA_TID_INT
```

emitter の isinstance 判定パスに、対象変数が tagged union 型であることを検出し、
`v.tag` を `py_tid_is_subtype` / `py_runtime_value_isinstance` に渡すコードを生成するロジックを追加する。

### ステップ 3: 型ナローイング

isinstance チェック後の変数アクセスを正しいフィールドに変換する。

```python
if isinstance(v, int):
    return str(v)      # v を int として使う
```
↓ C++
```cpp
if (v.tag == PYTRA_TID_INT) {
    return ::std::to_string(v.int64_val);
}
```

emitter が isinstance ガード内のスコープで、変数の型を narrowed type として追跡し、
フィールドアクセスを自動挿入する。

### ステップ 4: 動作確認

json.py を `type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]` で
書き直し、transpile が正しく動作することを確認する。

## 対象

- `src/toolchain/emit/cpp/emitter/cpp_emitter.py` — tagged struct 生成・isinstance・型ナローイング
- `src/toolchain/emit/cpp/emitter/header_builder.py` — tagged struct 生成
- `src/toolchain/emit/cpp/emitter/type_bridge.py` — tagged union 型のフィールドアクセス変換
- `src/pytra/std/json.py` — union type での書き直し（検証用）

## 非対象

- 非 C++ バックエンド（後続タスク）
- C++ union メモリ最適化（後続タスク）
- Generic type alias（`type Stack[T] = list[T]`）

## 受け入れ基準

- tagged struct の tag が `uint32` 型で `PYTRA_TID_*` 定数を使用する。
- `isinstance(v, int)` が tagged union 変数に対して `v.tag == PYTRA_TID_INT` を生成する。
- isinstance ガード内で変数の型ナローイングが正しく動作する（フィールドアクセス自動挿入）。
- json.py が `type JsonVal = ...` で書き直され、transpile 成功する。
- 既存の fixture / sample pass。

## 決定ログ

- 2026-03-18: ユーザー提案。tagged union の tag を PYTRA_TID と統一し、isinstance を1つの仕組みで実現する方針を決定。
  DFS オーダーベースの type_id レンジ方式が既に実装済みであり、tagged union メンバがクラス型の場合も
  継承関係を尊重した isinstance が自然に動作する。P0 として起票。
- 2026-03-18: 実装完了。ステップ 1-3 を実装。tag を `uint32` + `PYTRA_TID_*` に変更。isinstance を `v.tag == PYTRA_TID_XXX` に変換。
  if-stmt 内の isinstance ガードで型ナローイング（変数アクセスをフィールドアクセスに自動変換）を実装。
  json.py の書き直しは次タスクとして分離（isinstance + ナローイングが使える状態になった）。242 test pass。
