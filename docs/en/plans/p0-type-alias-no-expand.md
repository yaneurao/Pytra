<a href="../../ja/plans/p0-type-alias-no-expand.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-type-alias-no-expand.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-type-alias-no-expand.md`

# P0: パーサーの型エイリアス展開を抑止

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-TYPE-ALIAS-NO-EXPAND-01`

## 背景

EAST1 パーサー（`core_module_parser.py`）が `type JsonVal = None | bool | int | ...` を登録した後、
関数引数の `v: JsonVal` の型注釈を解決する際に `_sh_ann_to_type` がエイリアス名を展開形に置き換えてしまう。

```
type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]

def f(v: JsonVal) -> bool:
    ...
```

現状の EAST IR:
```json
{"arg_types": {"v": "bool|int64|float64|str|list[bool|int64|...|None]|dict[str,bool|int64|...|None]|None"}}
```

期待する EAST IR:
```json
{"arg_types": {"v": "JsonVal"}}
```

展開されると emitter の reverse map（`type_expr → alias_name`）でエイリアス名に戻せず、
`JsonVal` という名前の tagged struct ではなく `_Union_bool_int64_...` が生成されてしまう。

## 原因

`_sh_ann_to_type(ann_txt, type_aliases=...)` が `type_aliases` dict を使って
エイリアス名を展開形に置き換えている。`type X = T` で登録されたエイリアスは
名前のまま EAST IR に残すべき。

## 修正方針

1. `_sh_register_type_alias` で PEP 695 `type` 文由来のエイリアスを区別するフラグを追加
2. `_sh_ann_to_type` で PEP 695 エイリアスは展開せず名前のまま返す
3. または、`type_aliases` dict への登録を `type` 文由来のものはスキップし、
   パーサーが `JsonVal` を既知の型名として認識するだけにする

## 対象

- `src/toolchain/compile/core_module_parser.py` — `_sh_register_type_alias` / `_sh_ann_to_type`
- `src/toolchain/compile/core_type_semantics.py` — エイリアス登録・解決ロジック

## 受け入れ基準

- `type JsonVal = ...` の後、`v: JsonVal` の `resolved_type` が `"JsonVal"` のまま EAST IR に残る。
- emitter が `JsonVal` を named tagged struct として正しく emit する。
- 再帰型（`list[JsonVal]`）が内部展開されない。
- 既存の非再帰エイリアス（`type ArgValue = str | bool | None`）も同様にエイリアス名が保持される。
- fixture / sample pass。

## 決定ログ

- 2026-03-19: P1-JSON-TAGGED-UNION-REWRITE-01 のブロッカーとして特定。パーサーが型エイリアスを展開してしまうため emitter で名前に戻せない。P0 として起票。
