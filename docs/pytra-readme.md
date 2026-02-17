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

- Python 標準ライブラリ（主要サブセット）:
  - `math`, `time`, `pathlib`, `dataclasses`, `ast`
- 自作ライブラリ:
  - `py_module.png_helper`
  - `py_module.gif_helper`
- ターゲット言語ごとのランタイム:
  - `src/cpp_module`, `src/cs_module`, `src/rs_module`
  - `src/js_module`, `src/ts_module`
  - `src/go_module`, `src/java_module`
  - `src/swift_module`, `src/kotlin_module`

## 作業中

- `docs/todo.md` 記載の未完了項目
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
