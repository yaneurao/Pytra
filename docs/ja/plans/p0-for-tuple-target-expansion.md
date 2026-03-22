# P0: for ループの TupleTarget 事前展開

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-FOR-TUPLE-EXPAND`

## 背景

`for line_index, source in enumerate(lines)` の ForCore が `TupleTarget` を持ち、各 emitter がタプル展開コードを個別に生成する必要がある。

## 設計

EAST3 lowering で ForCore の TupleTarget を事前展開:
1. TupleTarget を単一の NameTarget（`__iter_tmp`）に置換
2. body の先頭に各要素への代入を挿入: `line_index = __iter_tmp[0]`, `source = __iter_tmp[1]`

emitter は NameTarget のみ処理すれば済む。

## 子タスク

- [ ] [ID: P0-FOR-TUPLE-EXPAND-01] ForCore TupleTarget を事前展開する EAST3 パスを実装する
- [ ] [ID: P0-FOR-TUPLE-EXPAND-02] ユニットテストを追加する

## 決定ログ

- 2026-03-22: Zig 担当が ForCore TupleTarget の展開ロジックを emitter 側で実装する手間を報告。全 backend 共通。
