<a href="../../en/plans/p3-predicates-template.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P3: predicates.py の @template 化（Any 除去）

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P3-PREDICATES-TEMPLATE-01`

## 背景

`src/pytra/built_in/predicates.py` の `py_any(values: Any)` / `py_all(values: Any)` は
引数型が `Any` であり、C++ では `object` を受け取る非テンプレート関数として生成される。

実際の呼び出しは `list[bool]` / `list[int]` 等の型確定したコレクションであり、
`@template("T")` を使えばテンプレート関数として生成でき、`Any` / `object` 経由が不要になる。

```python
# Before
def py_any(values: Any) -> bool:

# After
@template("T")
def py_any(values: T) -> bool:
```

## 対象

- `src/pytra/built_in/predicates.py` — `@template("T")` に変更
- `src/runtime/cpp/generated/built_in/predicates.h` — 再生成（テンプレート関数に）

## 受け入れ基準

- `py_any` / `py_all` が `@template("T")` で宣言されている。
- C++ 生成コードで `py_any<list<bool>>(xs)` のようにテンプレートインスタンスが生成される。
- `Any` が `src/pytra/built_in/predicates.py` から除去されている。
- fixture / sample pass。

## 決定ログ

- 2026-03-19: Any 除去の一環として起票。`@template` デコレータは既に `numeric_ops.py` / `zip_ops.py` で使用実績あり。
