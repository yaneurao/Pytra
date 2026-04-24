# Selfhost 向け Python コーディングガイド

この文書は、CPython では自然に動くが、Pytra の selfhost や C++ 生成では壊れやすかった Python の書き方をまとめたものです。

要点だけ先に書くと、次の方針です。

- 短く賢いコードより、明示的で段階的なコードを優先する
- `JsonVal` を「動的な Python オブジェクト」として扱わない
- `Optional[...]` は `JsonVal` に入れる前に `None` / 実値へ正規化する
- JSON 風の値は `isinstance(...)` ではなく accessor 経由で扱う

## この文書が必要な理由

selfhost で起きた不具合の多くは、Python 側では自然に見える暗黙変換や省略記法が、C++ へ落ちたときに曖昧になったり壊れたりしたことが原因でした。

特に壊れやすかったのは次の境界です。

- `dict[str, JsonVal]` の構築
- `list[JsonVal]` の構築
- `Optional[T] -> JsonVal` の変換
- `JsonVal` に対する `isinstance(...)`
- container literal 内の conditional expression など、密度の高い式

## ルール 1: `Optional[T]` を `JsonVal` に暗黙変換させない

次のようなコードは避けてください。

```python
return {
    "lineno": self.lineno,
    "col": self.col,
    "end_lineno": self.end_lineno,
    "end_col": self.end_col,
}
```

これは Python としては自然ですが、`Optional[int]` を含む場合、selfhost では壊れやすいです。

代わりに、次のように明示分岐してください。

```python
out: dict[str, JsonVal] = {}
if self.lineno is None:
    out["lineno"] = None
else:
    out["lineno"] = int(self.lineno)
if self.col is None:
    out["col"] = None
else:
    out["col"] = int(self.col)
if self.end_lineno is None:
    out["end_lineno"] = None
else:
    out["end_lineno"] = int(self.end_lineno)
if self.end_col is None:
    out["end_col"] = None
else:
    out["end_col"] = int(self.end_col)
return out
```

理由:

- selfhost では `Optional[int]` がそのまま `JsonVal` に流れたときに壊れやすかった
- 明示分岐すると backend 側の解釈が安定する
- `JsonVal` 境界では `None` と `int(...)` のような素直な値にしておくほうが安全

## ルール 2: `dict[str, JsonVal]` は一発 literal より段階代入を優先する

値が単純な JSON primitive ではない場合、密度の高い dict literal は避けてください。

避けたい形:

```python
d: dict[str, JsonVal] = {
    "kind": "Assign",
    "source_span": self.source_span.to_jv(),
    "target": expr_to_jv(self.target),
    "value": expr_to_jv(self.value),
    "declare": self.declare,
}
```

推奨形:

```python
d: dict[str, JsonVal] = {}
d["kind"] = "Assign"
d["source_span"] = self.source_span.to_jv()
d["target"] = expr_to_jv(self.target)
d["value"] = expr_to_jv(self.value)
d["declare"] = self.declare
```

理由:

- dict literal では複数の変換が一度に走る
- 1 つだけ問題のある値が混ざったとき、壊れ方の切り分けが難しい
- 段階代入のほうが selfhost 時の生成コードも追いやすい

## ルール 3: `JsonVal` 境界では conditional expression より `if/else` を使う

次のような書き方は避けてください。

```python
out["end_col"] = None if self.end_col is None else int(self.end_col)
```

推奨形:

```python
if self.end_col is None:
    out["end_col"] = None
else:
    out["end_col"] = int(self.end_col)
```

理由:

- conditional expression 自体は正しいが、selfhost では statement レベルの分岐のほうが安定した
- 特に `JsonVal` を作る直前では、式を詰め込まないほうがよい

## ルール 4: `JsonVal` を動的 Python オブジェクトのように扱わない

次のようなコードは避けてください。

```python
if isinstance(v, dict):
    ...
elif isinstance(v, list):
    ...
elif isinstance(v, int):
    ...
```

推奨形:

```python
value = JsonValue(v)
obj_v = value.as_obj()
if obj_v is not None:
    ...
arr_v = value.as_arr()
if arr_v is not None:
    ...
int_v = value.as_int()
if int_v is not None:
    ...
```

理由:

- `JsonVal` は Pytra では tagged union 境界型であって、任意の Python object ではない
- accessor を通したほうが C++ 側の表現と一致しやすい
- selfhost では `isinstance(...)` より accessor のほうが安定した

## ルール 5: 型が確定していない `JsonVal` に直接 container 操作をしない

次のようなコードは避けてください。

```python
for item in v:
    ...

name = v.get("name")
```

ただし、`v` がすでに正確な型の `dict` や `list` だと分かっている場合は別です。

推奨形:

```python
obj_v = JsonValue(v).as_obj()
if obj_v is not None:
    name = obj_v.get_str("name")

arr_v = JsonValue(v).as_arr()
if arr_v is not None:
    for item in arr_v.raw:
        ...
```

理由:

- `JsonVal` への Python 流儀の直接操作は selfhost で不整合を起こしやすい
- accessor を使うと期待している表現が明示される

## ルール 6: ad-hoc な `dict[str, JsonVal]` より `@dataclass` を優先する

内部表現として ad-hoc な dict を直接返すより、まず `@dataclass` で構造を定義し、必要な境界でだけ `to_jv()` するほうが望ましいです。

避けたい形:

```python
def build_span(...) -> dict[str, JsonVal]:
    return {
        "lineno": lineno,
        "col": col,
        "end_lineno": end_lineno,
        "end_col": end_col,
    }
```

推奨形:

```python
@dataclass
class SourceSpan:
    lineno: int | None
    col: int | None
    end_lineno: int | None
    end_col: int | None

    def to_jv(self) -> dict[str, JsonVal]:
        out: dict[str, JsonVal] = {}
        if self.lineno is None:
            out["lineno"] = None
        else:
            out["lineno"] = int(self.lineno)
        if self.col is None:
            out["col"] = None
        else:
            out["col"] = int(self.col)
        if self.end_lineno is None:
            out["end_lineno"] = None
        else:
            out["end_lineno"] = int(self.end_lineno)
        if self.end_col is None:
            out["end_col"] = None
        else:
            out["end_col"] = int(self.end_col)
        return out
```

理由:

- 内部表現の型が固定される
- `JsonVal` への変換点を `to_jv()` に閉じ込められる
- どこが wire format で、どこが通常の Python オブジェクトかが明確になる
- selfhost 不整合が起きたときに、境界コードだけを見ればよくなる

注意:

- `@dataclass` を使っても、`to_jv()` を雑に書くと同じ問題は再発する
- 重要なのは「通常の内部表現」と「`JsonVal` 境界」を分離すること
- `to_jv()` は依然として保守的に書く必要がある

## ルール 7: AST や metadata の基盤コードでは保守的な Python を使う

次の領域では特に保守的に書いてください。

- parser 出力
- AST node の `to_jv()`
- source span の直列化
- resolver metadata
- import metadata
- manifest 生成

推奨する書き方:

- ローカル変数を明示する
- `if/else` を明示する
- container を段階的に構築する
- `JsonValue(...).as_*()` を使う

避けたいもの:

- 賢い 1 行コード
- 暗黙変換頼みのコード
- 複数の変換を一つの式に押し込むコード

理由:

- これらは selfhost の土台になるコードだから
- ここでの不具合は、後段で opaque な C++ エラーや runtime 失敗として現れやすい

## `JsonVal` 境界で安全な形

`JsonVal` に入れる値は、できるだけ次のどれかに正規化してから入れてください。

- `None`
- `bool`
- `int`
- `float`
- `str`
- `list[JsonVal]`
- `dict[str, JsonVal]`

「あとで Pytra がいい感じに解釈してくれるだろう」と期待しないほうが安全です。

## レビュー時のチェックリスト

selfhost 対象コードをレビューするときは、次を見てください。

- `Optional[...]` がそのまま `JsonVal` container に入っていないか
- 非自明な変換を含む dict literal がないか
- `JsonVal` 境界に conditional expression がないか
- `JsonVal` を `isinstance(...)` で見ていないか
- `JsonVal` に対して直接 `.get(...)`、添字、iteration をしていないか

もし当てはまるなら、上の保守的な形へ書き直したほうがよいです。

## この文書の適用範囲

これは一般的な Python スタイルガイドではありません。

対象は次です。

- Pytra compiler source
- selfhost に乗る stdlib code
- JSON / AST / metadata 境界コード

通常の補助スクリプトや selfhost に乗らない Python では、普通の Python らしい書き方でも問題ないことがあります。
