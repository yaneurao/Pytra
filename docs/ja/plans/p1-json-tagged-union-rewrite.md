<a href="../../en/plans/p1-json-tagged-union-rewrite.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: json.py を type JsonVal = ... で書き直し

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-JSON-TAGGED-UNION-REWRITE-01`

## 背景

`src/pytra/std/json.py` は手動タグ付きクラス `_JsonVal` で JSON 値を表現している。
tagged union（`type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]`）と
`cast()` による型ナローイングが実装されたため、union type で書き直すことで：

- ソースコードがシンプルになる
- 再帰的 tagged union の実用検証になる
- 手動タグ定数（`_JV_NULL` 等）とファクトリ関数（`_jv_null()` 等）が不要になる

## 依存

- P0-INLINE-UNION-TAGGED-STRUCT-01（inline union の tagged struct 化）
- P0-TAGGED-UNION-CAST-NARROWING-01（cast() による型ナローイング）— 完了済み

## 対象

- `src/pytra/std/json.py` — union type での書き直し
- `src/runtime/cpp/generated/std/json.h` / `.cpp` — 再生成

## 受け入れ基準

- `type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]` で宣言。
- isinstance + cast() で型判定・値取り出し。
- 手動タグ定数・ファクトリ関数が除去されている。
- Python 実行時に既存テスト pass。
- C++ transpile + artifact parity pass。

## 決定ログ

- 2026-03-19: 再帰的 tagged union の実用検証として起票。P0-INLINE-UNION 完了が前提。
