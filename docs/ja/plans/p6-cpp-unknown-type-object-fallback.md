# P6: unknown / 空文字型の object フォールバック排除

最終更新: 2026-03-18

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-CPP-UNKNOWN-TYPE-OBJECT-FALLBACK-01`

## 背景

C++ emitter が型名が `"unknown"` または空文字列 `""` のときに `object` にサイレントフォールバックしている。
これは型推論失敗を隠蔽しており、バグの温床になっている。

| ファイル | 行 | 関数 | 条件 |
|---|---|---|---|
| `src/backends/cpp/emitter/type_bridge.py` | L668-669 | `_cpp_type_text()` | `east_type == "unknown"` |
| `src/backends/cpp/emitter/header_builder.py` | L1373-1374 | `_header_cpp_type_from_east()` | 型文字列が空 `""` |

## 方針

- `"unknown"` や `""` は型推論が失敗した証拠。サイレントに `object` に落とすのではなく、
  コンパイルエラーとして Python ソースへ型注釈を求める。
- エラーメッセージは「型を推論できません。型注釈を追加してください。」程度の診断情報を含む。
- `header_builder.py` の空文字フォールバックも同様にエラー化する。

## 対象

- `src/backends/cpp/emitter/type_bridge.py` L668-669
- `src/backends/cpp/emitter/header_builder.py` L1373-1374

## 受け入れ基準

- `"unknown"` / `""` → `object` サイレントフォールバックが 0 になる。
- selfhost mismatches=0。

## 決定ログ

- 2026-03-18: object 排除方針の下、カテゴリ B フォールバックとして特定。
