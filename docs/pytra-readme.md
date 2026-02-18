# Pytra 実装状況メモ

このページは、`README.md` から分離した実装状況の詳細です。

## 実装済みの言語機能

- 変数代入（通常代入、型注釈付き代入、拡張代入の主要ケース）
- 算術・ビット演算（`+ - * / // % ** & | ^ << >>`）
- 比較演算（`== != < <= > >= in not in is is not` の主要ケース）
- 論理演算（`and or not`）
- 条件分岐（`if / elif / else`）
- ループ（`while`、`for in <iterable>`、`for in range(...)`）
- 例外（`try / except / finally`、`raise` の主要ケース）
- 関数定義・関数呼び出し・戻り値
- クラス定義（単一継承、`__init__`、class member、instance member）
- `@dataclass` の基本変換
- 文字列（f-string の主要ケース、`replace` など）
- コンテナ（`list`, `dict`, `set`, `tuple` の主要ケース）
- list/set comprehension の主要ケース
- スライス（`a[b:c]`）
- `if __name__ == "__main__":` ガード認識
- EAST 変換（`src/common/east.py`）と EAST ベース C++ 変換（`src/py2cpp.py`）

## 実装済みの組み込み関数

- `print`, `len`, `range`
- `int`, `float`, `str`
- `ord`, `bytes`, `bytearray`
- `min`, `max`
- `grayscale_palette`, `save_gif`, `write_rgb_png`（EAST/C++ ランタイム経由）

## 対応module

Python標準ライブラリは「モジュール名だけ」でなく、対応関数を次のように限定します（未記載は未対応扱い）。

- `math`
  - 共通対応（C++/C#/Rust/JS/TS/Go/Java）:
    - `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `fabs`, `floor`, `ceil`, `pow`
    - 定数: `pi`, `e`
  - 差分:
    - Swift/Kotlin は Node バックエンド方式のため、実体は JS/TS 側 `math` 実装に依存します。
    - C# は `System.Math` へ直接マッピングする設計です（専用 `math` ランタイムは未分離）。
- `time`
  - `perf_counter`
- `pathlib`
  - 共通対応（C++/Rust/C#/JS/TS/Go/Java/Swift/Kotlin）:
    - `Path(...)`, `pathlib.Path(...)`
    - `Path / "child"`（パス連結）
    - `exists`, `resolve`, `parent`, `name`, `stem`
    - `read_text`, `write_text`, `mkdir(parents, exist_ok)`
    - `str(Path)`（文字列化）
  - 実装位置:
    - C++: `src/cpp_module/pathlib.h/.cpp`
    - Rust: `src/rs_module/py_runtime.rs`（`PyPath`）
    - C#: `src/cs_module/pathlib.cs`（`py_path`）
    - JS/TS: `src/js_module/pathlib.js`, `src/ts_module/pathlib.ts`
    - Go/Java: `src/go_module/py_runtime.go`, `src/java_module/PyRuntime.java`
    - Swift/Kotlin: Node バックエンド方式のため、実体は JS ランタイム（`src/js_module/pathlib.js`）に依存
  - 差分:
    - Python `pathlib` の完全互換ではなく、Pytra の最小共通 API に限定しています。
    - `read_text` / `write_text` の encoding 指定は UTF-8 固定です（引数は互換目的で受理するが無視される実装を含む）。
- `dataclasses`
  - `@dataclass` デコレータ（変換時展開）
  - C++ ランタイム補助（最小）:
    - `dataclass(...)`, `DataclassTag`, `is_dataclass_v`
- `ast`
  - C++ 実装（`src/cpp_module/ast.*`）:
    - `parse(source, filename)`
    - `parse_file(path)`
    - 主要ノード型（`Module`, `FunctionDef`, `ClassDef`, `Assign`, `Call` など）

- 自作ライブラリ:
  - `pylib.png`
    - `write_rgb_png(path, width, height, pixels)`
  - `pylib.gif`
    - `save_gif(path, width, height, frames, palette, delay_cs, loop)`
    - `grayscale_palette()`
  - `pylib.assertions`
    - `py_assert_true`, `py_assert_eq`, `py_assert_all`, `py_assert_stdout`
- ターゲット言語ごとのランタイム:
  - `src/cpp_module`, `src/cs_module`, `src/rs_module`
  - `src/js_module`, `src/ts_module`
  - `src/go_module`, `src/java_module`
  - `src/swift_module`, `src/kotlin_module`

## 作業中

- Go/Java の静的型反映強化（`any`/`Object` 退化の削減）
- Go/Java の `bytes` / `bytearray` パス最適化

## EAST 実装状況

- `src/common/east.py`
  - `test/fixtures` 32/32, `sample/py` 16/16 を EAST 変換可能
  - `range(...)` は `ForRange` / `RangeExpr` へ正規化され、生の `Call(Name("range"))` は後段へ渡さない
- `src/py2cpp.py`
  - `sample/py` 16/16 を `変換 -> コンパイル -> 実行` まで通過
  - `append/extend/pop`, `perf_counter`, `min/max`, `save_gif` / `write_rgb_png` / `grayscale_palette` をランタイム連携
- ベンチマーク
  - 一覧/詳細は `sample/` 配下の最新計測結果を参照

## 未実装項目

- Python 構文の完全互換（現状はサブセット対応）
- `a[b:c]` 以外のスライス構文
- 標準ライブラリの網羅対応
- 高度な型推論・制御フロー解析の一部
- 動的 import / 動的型付けへの本格対応

## 対応予定なし

- Python 構文の完全一致互換
- 循環参照・弱参照を含む高度 GC 互換
- 全方位の動的実行機能（動的 import など）の完全再現
