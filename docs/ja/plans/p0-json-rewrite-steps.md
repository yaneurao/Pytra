<a href="../../en/plans/p0-json-rewrite-steps.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: json.py を type JsonVal で段階的に書き直し

最終更新: 2026-03-19

関連 TODO:
- P0-JSON-REWRITE-S1-01 〜 P0-JSON-REWRITE-S4-01

## 背景

P0-TYPE-ALIAS-NO-EXPAND-01 完了により、`type JsonVal = ...` の再帰型がパーサー・emitter で
正しく処理されるようになった。json.py を tagged union で書き直す。

## ステップ分割

### S1: type 宣言とファクトリ関数の置き換え

- `_JsonVal` クラス + タグ定数（`_JV_NULL` 等）+ ファクトリ関数（`_jv_null()` 等）を削除
- `type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]` を追加
- ファクトリ関数の呼び出しを直接値に置き換え（`_jv_int(42)` → `42`）

### S2: パーサーの書き換え

- `_JsonParser` の `_parse_value` / `_parse_number` 等の戻り値型を `JsonVal` に変更
- `_jv_*()` ファクトリ呼び出しを直接値の return に置き換え

### S3: ダンパーの書き換え

- `_dump_json_value` のタグ判定（`v.tag == _JV_INT`）を `isinstance(v, int)` + `cast(int, v)` に変更
- `_dump_json_list` / `_dump_json_dict` の引数型を `list[JsonVal]` / `dict[str, JsonVal]` に変更

### S4: 公開 API の書き換え

- `JsonObj` / `JsonArr` / `JsonValue` の内部型を `_JsonVal` → `JsonVal` に変更
- `loads` / `loads_obj` / `loads_arr` / `dumps` の引数・戻り値型を更新
- Python 実行テスト + C++ transpile テスト

## 決定ログ

- 2026-03-19: json.py の書き直しを 4 ステップに分割。各ステップを P0 で起票。
