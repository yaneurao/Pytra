<a href="../../ja/plans/p6-east3-general-union-variant.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p6-east3-general-union-variant.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p6-east3-general-union-variant.md`

# P6: 一般ユニオン型 → std::variant / 多言語 tagged union 対応

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-EAST3-GENERAL-UNION-VARIANT-01`

## 背景

Python の `str | bool | None`、`str | int | float | bool | None` などの多型ユニオン型は
EAST3 IR に `UnionType { union_mode: "general", options: [...] }` として既に正しく表現されている。
しかし C++ emitter の `type_bridge.py` がこれを拒否するため、
`src/pytra/std/argparse.py` / `src/pytra/utils/assertions.py` を transpiler で再生成できない：

```
error: unsupported general union for C++ emit: str|bool|None
error: cpp_signature_type: str|int64|float64|bool|None
```

これにより `generated/std/argparse.cpp` / `generated/utils/assertions.cpp` を
手動編集しなければならない状態になっている。`generated/` の手動編集は禁止されているため、
emitter 側を修正して自動生成できるようにすることが本タスクの目的である。

### 対応するファイル

| Python ソース | ユニオン型 | 影響する生成ファイル |
|---|---|---|
| `src/pytra/std/argparse.py` | `str \| bool \| None`、`dict[str, str \| bool \| None]` | `generated/std/argparse.cpp` |
| `src/pytra/utils/assertions.py` | `str \| int \| float \| bool \| None` | `generated/utils/assertions.cpp` |

## 方針

一般ユニオン型（3 型以上、または `Optional[T]` でない 2 型ユニオン）を各言語の sum type に変換する。

| 言語 | 変換先 |
|---|---|
| C++ | `std::variant<T1, T2, ..., std::monostate>`（`None` → `std::monostate`） |
| Rust | ネイティブ `enum` |
| C# | `OneOf<T1, T2, ...>` またはプロジェクト提供 Variant クラス |
| Swift / Kotlin | `sealed class` / `enum` |
| TypeScript | union literal type (`T1 \| T2 \| T3`) |
| その他 | プロジェクト提供 `Variant<T1, T2, ...>` クラス |

### C++ の具体例

- `str | bool | None` → `std::variant<str, bool, std::monostate>`
- `dict[str, str | bool | None]` → `dict<str, std::variant<str, bool, std::monostate>>`
- `str | int | float | bool | None` → `std::variant<str, int64, double, bool, std::monostate>`

### 使用パターンの対応

| Python パターン | C++ 変換 |
|---|---|
| `x = "hello"` (variant への代入) | `std::variant<...> x = "hello";`（暗黙変換） |
| `isinstance(x, str)` | `std::holds_alternative<str>(x)` |
| `x is None` | `std::holds_alternative<std::monostate>(x)` |
| `x is not None` | `!std::holds_alternative<std::monostate>(x)` |
| `match x: case str() as s:` | `std::visit` + overloaded lambda（後続タスク） |

## 目的

- C++ emitter が一般ユニオン型を `std::variant<...>` として emit できるようにする。
- `argparse.py` / `assertions.py` を transpiler で再生成できるようにする。
- 将来の非 C++ バックエンドへの拡張基盤を整える。

## 対象（本タスク: C++ 優先 MVP）

- `src/toolchain/emit/cpp/emitter/type_bridge.py`（型名変換: 拒否 → `std::variant<...>` emit）
- `src/toolchain/emit/cpp/emitter/cpp_emitter.py`（`isinstance` → `std::holds_alternative`、`is None` → `std::holds_alternative<std::monostate>`）
- `src/runtime/cpp/generated/std/argparse.cpp`（再生成）
- `src/runtime/cpp/generated/utils/assertions.cpp`（再生成）

## 非対象（後続タスクで対応）

- `std::visit` ベースの `match` 文サポート
- C++ 以外のバックエンド（Rust enum、C# 等）
- runtime Variant クラスの他言語向け実装

## 受け入れ基準

- `PYTHONPATH=src python3 src/toolchain/emit/cpp/cli.py src/pytra/std/argparse.py` が成功する。
- `PYTHONPATH=src python3 src/toolchain/emit/cpp/cli.py src/pytra/utils/assertions.py` が成功する。
- 再生成した `argparse.cpp` / `assertions.cpp` でコンパイルが通る。
- selfhost diff mismatches=0。

## 実装メモ

### type_bridge.py の変更箇所

- `_cpp_type_text()` (line 574-597): `UnionType general` を拒否している箇所を変更
  - `None` 型要素を `std::monostate` に変換
  - 各要素を `cpp_type()` 再帰呼び出しで変換
  - `std::variant<T1, T2, ...>` を返す
- `_reject_unsupported_cpp_general_union_type_expr()` (lines 58-74): 呼び出しを削除または条件変更

### cpp_emitter.py の変更箇所

- `isinstance(x, T)` で `x` の型が variant の場合 → `std::holds_alternative<T>(x)` emit
- `_render_is_none_expr()`: variant 型の場合 → `std::holds_alternative<std::monostate>(x)` emit

## 決定ログ

- 2026-03-18: `object` フォールバック案（p6-cpp-emit-union-type-to-object.md）は object 排除方針と矛盾するため却下。`std::variant` 採用を決定。IR はすでに `UnionType { union_mode: "general" }` として正しく表現済みであり、変更は emitter 層のみ。
