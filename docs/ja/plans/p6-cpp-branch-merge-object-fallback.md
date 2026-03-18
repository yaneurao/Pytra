# P6: if/else 分岐型マージ失敗の object フォールバック排除

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-CPP-BRANCH-MERGE-OBJECT-FALLBACK-01`

## 背景

`cpp_emitter.py` の `_predeclare_if_join_names()` が if/else 両分岐で型が異なる変数を
事前宣言する際、型マージに失敗すると `object` にフォールバックしている。

| ファイル | 行 | 関数 | 条件 |
|---|---|---|---|
| `src/backends/cpp/emitter/cpp_emitter.py` | L2101-2105 | `_predeclare_if_join_names()` | 分岐型マージ結果が `""` / `"auto"` になる |

```python
# 現状（L2101-2105）:
decl_t = decl_t if decl_t != "" else "object"
cpp_t = self._cpp_type_text(decl_t)
fallback_to_object = cpp_t in {"", "auto"}
decl_t = "object" if fallback_to_object else decl_t
cpp_t = "object" if fallback_to_object else cpp_t
```

## 方針

- 分岐型マージ失敗時は `object` フォールバックではなく、
  `std::variant<T1, T2>` を使う（一般ユニオン対応 P6-EAST3-GENERAL-UNION-VARIANT-01 の後で実施）。
  または Python ソース側に明示型注釈を要求するコンパイルエラーを出す。
- `_merge_decl_types_for_branch_join()` の型マージロジックを拡張し、
  異なる具体型が合流する場合に union 型を返せるようにする。

## 依存

- P6-EAST3-GENERAL-UNION-VARIANT-01（std::variant サポート）が先行完了していること推奨

## 対象

- `src/backends/cpp/emitter/cpp_emitter.py` L2101-2105、`_merge_decl_types_for_branch_join()` 周辺

## 受け入れ基準

- if/else 型マージ失敗によるサイレント `object` フォールバックが 0 になる。
- selfhost mismatches=0。

## 決定ログ

- 2026-03-18: object 排除方針の下、カテゴリ B フォールバックとして特定。
