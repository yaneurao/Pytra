# P0-COMMON-RENDERER-UNION-MEMBER: union 構成要素の格納で covariant copy をスキップする

最終更新: 2026-04-13

## 背景

C++ selfhost build で `list[JsonVal].append(stmt)` が covariant copy ラムダに誤変換される。`stmt` の型は `dict[str, JsonVal]` で、`JsonVal` の union 構成要素の 1 つ。Python では `list[JsonVal]` に `dict[str, JsonVal]` を append するのは合法（union の構成要素を union に格納するだけ）だが、emitter が「要素型と引数型が一致しない → covariant copy が必要」と誤判定する。

## 問題

```python
out: list[JsonVal] = []         # JsonVal = None | bool | int | ... | dict[str, JsonVal]
stmt: dict[str, JsonVal] = ...
out.append(stmt)                # ← dict を JsonVal（variant）に格納するだけ
```

emitter が生成する誤ったコード（C++）:

```cpp
// dict を丸ごとコピーする lambda を生成してしまう
py_list_append_mut(out, ([&]() {
    Object<dict<str, JsonVal>> __cov_1;
    for (auto const& __item_2 : stmt) {
        __cov_1.push_back(__item_2);  // ← dict に push_back はない
    }
    return __cov_1;
}()));
```

正しいコード:

```cpp
// variant への単純格納
py_list_append_mut(out, JsonVal(stmt));
```

## 影響

- C++ だけでなく Go / Rust / Zig 等、variant / enum / interface で union を表現する全言語で同じ問題が起きうる
- `list[Union].append(member)` だけでなく、`dict[str, Union]` への代入、関数引数での受け渡し等、union 型に構成要素を格納する全ての場面に適用される

## 修正方針

### CommonRenderer に helper を追加

```python
def _is_union_member(self, member_type: str, union_type: str) -> bool:
    """member_type が union_type の構成要素かどうか判定する。

    例: _is_union_member("dict[str, JsonVal]", "JsonVal") → True
        （JsonVal = None | bool | int | ... | dict[str, JsonVal]）
    """
```

### 適用箇所

`list[U].append(x)` で `x` の `resolved_type` がリストの要素型 `U` と一致しない場合:

1. `_is_union_member(x_type, U)` を呼ぶ
2. True なら covariant copy をスキップし、variant への単純格納コードを生成
3. False なら既存の covariant copy ロジックを使う

### 各言語での「単純格納」

| 言語 | union 表現 | 単純格納 |
|------|-----------|---------|
| C++ | `std::variant` | `JsonVal(stmt)` または暗黙変換 |
| Rust | `enum` | `JsonVal::Dict(stmt)` |
| Go | `interface{}` / `any` | そのまま代入 |
| Zig | `union(enum)` | `.{ .dict = stmt }` |
| TS/JS | 動的型 | そのまま代入（問題が顕在化しない） |

### union 構成要素の判定方法

`_is_union_member` は:
1. `union_type` が type alias なら展開する（P0-RESOLVE-TYPE-ALIAS の仕組みを使う）
2. 展開後の union 構成要素リストに `member_type` が含まれるか判定
3. 再帰型（`JsonVal` 自体が構成要素に `list[JsonVal]` を含む）は名前比較で判定
