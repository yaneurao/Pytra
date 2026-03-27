<a href="../../en/plans/p1-ifexp-optional-inference.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-IFEXP-OPTIONAL: 三項演算子の Optional 型推論

最終更新: 2026-03-27
ステータス: 完了

## 背景

`x = expr if cond else None` の形で、真側が型 `T`、偽側が `None` の場合、`x` の型は `Optional[T]`（= `T | None`）に推論されるべきである。現在の resolver はこのパターンの型推論ができておらず、selfhost コードで三項演算子を if 文に書き直す回避が発生している。

```python
# 本来はこれで x: str | None に推論されるべき
x = value_summary["mirror"] if "mirror" in value_summary else None

# 現状: resolver が推論できないため if 文に書き直している
x = ""
if "mirror" in value_summary:
    x = normalize_type_name(value_summary["mirror"])
```

## 設計

### resolver の IfExp 型推論を拡張

resolver が `IfExp`（三項演算子）の型推論で以下を行う:

1. 真側（`body`）と偽側（`orelse`）の `resolved_type` をそれぞれ解決する
2. 両側が同じ型なら、その型を IfExp の型とする（既存動作）
3. 片側が `None` の場合、もう片側の型 `T` から `OptionalType(inner=T)` を生成する
4. 両側が異なる非 None 型の場合は `UnionType` を生成する

### 影響範囲

- `src/toolchain2/resolve/py/resolver.py` の IfExp 処理
- 新しい EAST ノードは不要（`resolved_type` / `type_expr` の更新のみ）
- emitter への影響なし（narrowing 済みの型を写像するだけ）

## サブタスク

1. [x] [ID: P1-IFEXP-OPT-S1] resolver の IfExp 型推論で `T if cond else None` → `Optional[T]` を返すようにする
2. [x] [ID: P1-IFEXP-OPT-S2] 両側が異なる非 None 型の場合に `UnionType` を返すようにする
3. [x] [ID: P1-IFEXP-OPT-S3] fixture 追加 + golden 生成 + parity 確認

## 受け入れ基準

1. `x = expr if cond else None` で `x` の型が `Optional[T]` に推論されること
2. `x = a if cond else b`（a: int, b: str）で `x` の型が `int | str` に推論されること
3. 既存 fixture / sample の parity が維持されること

## 決定ログ

- 2026-03-27: go-selfhost で三項演算子を if 文に書き直す回避が発生。resolver の IfExp 型推論が `Optional[T]` を返せないことが原因。resolver の修正として起票。
- 2026-03-27: resolver に `IfExp` の `Optional[T]` / union merge を追加し、`ifexp_optional_inference` fixture・golden・linked と unit test を追加して完了。
