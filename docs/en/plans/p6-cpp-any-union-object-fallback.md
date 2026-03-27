<a href="../../ja/plans/p6-cpp-any-union-object-fallback.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p6-cpp-any-union-object-fallback.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p6-cpp-any-union-object-fallback.md`

# P6: Any 混入ユニオン・式の object フォールバック排除

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-CPP-ANY-UNION-OBJECT-FALLBACK-01`

## 背景

C++ emitter が以下の3箇所で `object` にサイレントフォールバックしている。
いずれも `Any` / `unknown` / `object` を含む型が現れた際に型消去を行っている。

| ファイル | 行 | 関数 | 条件 |
|---|---|---|---|
| `src/toolchain/emit/cpp/emitter/type_bridge.py` | L591-592 | `_cpp_type_text()` | ユニオン要素に Any-like が含まれる（`int \| Any` 等） |
| `src/toolchain/emit/cpp/emitter/cpp_emitter.py` | L471-472 | `get_expr_type()` | 二項演算の片方が Any-like |
| `src/toolchain/emit/cpp/emitter/cpp_emitter.py` | L2082-2083 | `_infer_numeric_expr_type()` | 数値二項演算の片方が Any-like |

## 方針

- `int | Any` のような動的ユニオンは、Python ソース側で `Any` を使わない型に書き直すことが根本解決。
  emitter は警告またはエラーを出す（サイレントフォールバック禁止）。
- 二項演算で片方が Any-like の場合も同様：型不明を `object` に隠すのではなく、
  コンパイルエラーとして Python ソースへ型注釈を求める。
- `Any` の使用自体をコードベースから排除することが長期目標。

## 対象

- `src/toolchain/emit/cpp/emitter/type_bridge.py` L591-592
- `src/toolchain/emit/cpp/emitter/cpp_emitter.py` L471-472, L2082-2083

## 非対象

- `union_mode: "general"` の一般ユニオン → `std::variant` への変換（P6-EAST3-GENERAL-UNION-VARIANT-01 で対応）
- `Any` 型の根本排除（長期タスク）

## 受け入れ基準

- `Any` 混入ユニオン / Any-like 二項演算でサイレントに `object` を返す箇所が 0 になる。
- selfhost mismatches=0。

## 決定ログ

- 2026-03-18: object 排除方針の下、カテゴリ A フォールバックとして特定。
- 2026-03-18: 実装完了。(1) type_bridge.py: Any 混入 2+ 型ユニオンで ValueError（Any 単体は object 維持）。(2) cpp_emitter.py: Any-like 二項演算で object に隠さず空文字を返し resolved_type にフォールバック。241 test pass。
