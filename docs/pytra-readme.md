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

## 実装済みの組み込み関数

- `print`, `len`, `range`
- `int`, `float`, `str`
- `ord`, `bytes`, `bytearray`
- `min`, `max`

## 対応module

Python標準ライブラリは「モジュール名だけ」でなく、対応関数を次のように限定します（未記載は未対応扱い）。

- `math`
  - 共通サブセット（主要ターゲットで利用実績あり）:
    - `sqrt`, `sin`, `cos`, `exp`, `floor`
    - 定数: `pi`, `e`
  - C++ 追加実装（`src/cpp_module/math.*`）:
    - `tan`, `log`, `log10`, `fabs`, `ceil`, `pow`
- `time`
  - `perf_counter`
- `pathlib`
  - C++ 実装（`src/cpp_module/pathlib.h/.cpp`）:
    - `Path.resolve()`
    - `Path.parent` / `Path.parents[index]`
    - `Path / "child"`（パス連結）
    - `Path.read_text()`, `Path.write_text()`
    - `Path.mkdir(parents_flag, exist_ok)`
    - `Path.name()`, `Path.stem()`, `str(Path)`
  - C# は `System.IO` へのマッピング中心で、`pathlib` 完全互換ではありません。
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
  - `py_module.png_helper`
    - `write_rgb_png(path, width, height, pixels)`
  - `py_module.gif_helper`
    - `save_gif(path, width, height, frames, palette, delay_cs, loop)`
    - `grayscale_palette()`
- ターゲット言語ごとのランタイム:
  - `src/cpp_module`, `src/cs_module`, `src/rs_module`
  - `src/js_module`, `src/ts_module`
  - `src/go_module`, `src/java_module`
  - `src/swift_module`, `src/kotlin_module`

## 作業中

- 本ページに記載している未完了項目（「作業中」「未実装項目」）の継続対応
- `sample/py/15` で見えた変換器側課題の吸収
- Go/Java の `sample/py` 向けランタイム拡張（`math`, `png`, `gif`）
- Rust 出力の PNG バイナリ完全一致化と import 生成最適化

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
