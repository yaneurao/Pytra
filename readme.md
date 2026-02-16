# Pytraとは何？

Pytraは、Pythonのサブセットで書かれたプログラムを他の様々な言語に変換するためのトランスパイラ群です。

現状サポートしている変換先の言語は、
- C++
- C#
- 🚧 JavaScript
- 🚧 Rust
です。

⚠ まだ開発途上にあり、実用にほど遠いかもしれません。サンプルコードなどを確認してから自己責任において、ご利用ください。

## 開発動機

マルチプラットフォーム対応のゲームを作ろうと思うと、現在は、Unityが現実解です。UnityではC#で書く必要があります。私はサーバーサイドは、Pythonで書きたかったのですが、ブラウザ側もあるなら、そこはJavaScriptで書く必要があります。

こうなると3つの言語を行き来することになります。場合によっては同じロジックを3回実装しなければなりません。これはさすがにおかしいのではないか？と思ったのが開発のきっかけです。

また、素のPythonだと遅すぎてサーバーサイドで大量のリクエストを捌くのには向かないです。ここが少しでも速くなればと思い、開発しました。

JavaScriptのコードにも変換できるので、Pythonでブラウザゲームの開発もできます。

## トランスパイラ本体

- Python → C++ : [src/py2cpp.py](src/py2cpp.py)
- Python → C# : [src/py2cs.py](src/py2cs.py)
- Python → JavaScript : 🚧[src/py2js.py](src/py2js.py)

## トランスパイラの使い方

### 1. Python から C++ へ変換

```bash
python src/py2cpp.py <input.py> <output.cpp>
```

例:

```bash
python src/py2cpp.py test/py/case28_iterable.py test/cpp/case28_iterable.cpp
```

### 2. Python から C# へ変換

```bash
python src/py2cs.py <input.py> <output.cs>
```

例:

```bash
python src/py2cs.py test/py/case28_iterable.py test/cs/case28_iterable.cs
```

### 3. 変換後コードの実行例

#### C++

```bash
g++ -std=c++20 -O2 -I src test/cpp/case28_iterable.cpp \
  src/cpp_module/png.cpp src/cpp_module/gif.cpp src/cpp_module/math.cpp \
  src/cpp_module/time.cpp src/cpp_module/pathlib.cpp src/cpp_module/dataclasses.cpp \
  src/cpp_module/ast.cpp src/cpp_module/gc.cpp \
  -o test/obj/case28_iterable.out
./test/obj/case28_iterable.out
```

#### C#

```bash
mcs -out:test/obj/case28_iterable.exe \
  test/cs/case28_iterable.cs \
  src/cs_module/py_runtime.cs src/cs_module/time.cs src/cs_module/png_helper.cs
mono test/obj/case28_iterable.exe
```

### 4. 注意点

- 対象は Python のサブセットです。一般的な Python コードすべてが変換できるわけではありません。
- 型注釈が必要な箇所があります（ただし一部は推論可能）。
- Python で `import` するモジュールは、対応するランタイム実装が `src/cpp_module/` または `src/cs_module/` に必要です。
- 生成された C++/C# は「読みやすさ」より「変換の忠実性」を優先しています。


## 変換例

どのようなコードに変換されるのかは、以下のフォルダのファイルをご覧ください。

### テストコード

10行程度の簡単なコードがどう変換されるか確認するためのもの。

- [test/py](test/py) : テストコード。(Pythonで書かれたファイル。)
- [test/cpp](test/cpp) : テストコードをC++のコードに変換したもの。
- [test/cs](test/cs) : テストコードをC#のコードに変換したもの。
- [test/js](test/js) : 🚧テストコードをJavaScriptのコードに変換したもの。

### サンプルコード

実行に数秒を要する数十行程度のサンプルコードを別の言語に変換して、その実行時間を比較するためのもの。

- [sample/py](sample/py) : サンプルコード Pythonで書かれた14個のファイル。
- [sample/cpp](sample/cpp) : サンプルコードをC++のコードに変換したもの。
- [sample/cs](sample/cs) : サンプルコードをC#のコードに変換したもの。
- [sample/js](sample/js) : 🚧サンプルコードをJavaScriptのコードに変換したもの。

## 実行速度の比較

サンプルコードの実行時間。

|ファイル名|内容| Python(元のコード) | C++に変換後 | C#に変換後 | JSに変換後 | Rustに変換後 |
|-|-|-|-|-|-|-|
|01_mandelbrot|マンデルブロ集合をPNG出力| 1000[ms] | 300[ms] | 400[ms] | 🚧 | 🚧|

## 言語的制約

- Pythonのsubset言語です。(通常のPythonのコードとして実行できます。)
- 型を明示する必要があります。
- ただし、以下のようなケースは暗黙の型推論を行います。
  - x = 1 のように右辺が整数リテラルの時は、左辺は int 型である。
  - x が int型だと、わかっているときの y = x (右辺の型は明らかにintなので左辺は型推論によりint)

型名について
- intは、64-bit 符号付き整数型です。
- int8,uint8,int16,uint16,int32,uint32,int64,uint64はそれが使えるplatformでは、それを使うようにします。(C++だとint8はint8_tに変換されます。)
- floatは、Pythonの仕様に基づき、64-bit 浮動小数点数です。(C++だとdoubleになります。)
- float32 という型名にすると 32-bit 浮動小数点数とみなして変換されます。(C++だとfloatになります。)


## 実装済みの言語機能

- 変数代入（通常代入、型注釈付き代入、拡張代入の主要ケース）
- 算術演算（`+ - * / // % **` の主要ケース）
- 比較演算（`== != < <= > >= in not in is is not` の主要ケース）
- 条件分岐（`if / elif / else`）
- ループ（`while`、`for in <iterable>`、`for in range(...)`）
- 例外（`try/except/finally`、`raise` の主要ケース）
- 関数定義・関数呼び出し・戻り値
- クラス定義（単一継承、`__init__`、static member、instance member）
- `@dataclass` の基本変換
- 文字列（f-string の主要ケース、`replace` などの主要メソッド）
- コンテナ（`list`, `dict`, `set`, `tuple` の主要ケース）
- list/set comprehension の主要ケース
- `if __name__ == "__main__":` ガードの認識
- 型マッピング（`int`, `int8..uint64`, `float`, `float32`, `str`, `bool`, `None`）

### module

- `math`（主要関数: `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `log10`, `floor`, `ceil`, `pow` など）
- `time`（`perf_counter`）
- `pathlib`（利用中機能の範囲）
- `dataclasses`（`@dataclass`）
- `ast`（セルフホスティングのためのランタイム実装）

独自追加。
- `py_module.png_helper` : PNG画像出力ヘルパ
- `py_module.gif_helper` : GIF画像出力ヘルパ

## 未実装項目

- JavaScript / Rust 向けトランスパイラ本体の本格実装
- Python 構文の完全互換（現状はサブセット）
- 標準ライブラリ網羅対応（`import` 可能モジュールの拡充）
- 動的なimport、動的型付け(これ)
- 例外処理・型推論の高度化（より複雑なケースの対応）
- 生成コード品質の最適化（可読性・サイズ・高速化）
- 回帰テストのさらなる拡充（網羅率向上）
- スライス構文の完全対応（現状は `a[b:c]` のみ対応、`a[:c]`, `a[b:]`, `a[:]`, `a[b:c:d]`, 負step, スライス代入は未対応）


## 開発について

本トランスパイラは、主にGPT-5.3-Codexで開発しています。

## ライセンス

MIT Licenseとします。
