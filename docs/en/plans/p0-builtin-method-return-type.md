<a href="../../ja/plans/p0-builtin-method-return-type.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-builtin-method-return-type.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-builtin-method-return-type.md`

# P0: 組み込み型メソッドの戻り値型推論を拡充

最終更新: 2026-03-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-BUILTIN-METHOD-RETURN-TYPE`

## 背景

`dict[str, Any].get()` の戻り値が `unknown` に推論され、emitter が適切な型キャストを生成できない。同様に `dict.values()` の戻り値型も不明で、コンテナ操作が壊れる。

これらは Python の言語仕様として戻り値型が確定しており、`signature_registry.py` の `_OWNER_METHOD_RETURN_TYPES` に登録すれば解決する。モジュール固有情報ではなく、言語の組み込み型のメソッド戻り値型なので EAST1 パーサーの責務範囲。

## 対象

| メソッド | 戻り値型 |
|---|---|
| `dict.get(key)` | value type（`Any` if `dict[str, Any]`） |
| `dict.get(key, default)` | value type |
| `dict.values()` | `list[V]`（V は dict の value type） |
| `dict.keys()` | `list[K]`（K は dict の key type） |
| `dict.items()` | `list[tuple[K, V]]` |
| `list.pop()` | element type |
| `str.split()` | `list[str]` |

## 子タスク

- [ ] [ID: P0-BUILTIN-METHOD-RETURN-TYPE-01] `signature_registry.py` に不足している組み込み型メソッドの戻り値型を追加する
- [ ] [ID: P0-BUILTIN-METHOD-RETURN-TYPE-02] ユニットテストを追加する

## 決定ログ

- 2026-03-22: PS 担当が dict.get() / dict.values() の resolved_type=unknown 問題を報告。全 backend 共通の改善として起票。
