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
- Python → Rust : 🚧[src/py2rs.py](src/py2rs.py)

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
- 変数には、型注釈が必要です。（ただし一部は推論可能）。
- Python で `import` するモジュールは、対応するランタイム実装が `src/cpp_module/` または `src/cs_module/` に必要です。
- `sample/py/` を Python のまま実行する場合は、`py_module` を解決するため `PYTHONPATH=src` を付けて実行してください（例: `PYTHONPATH=src python3 sample/py/01_mandelbrot.py`）。
- 生成された C++/C# は「読みやすさ」より「変換の忠実性」を優先しています。


## 変換例

どのようなコードに変換されるのかは、以下のフォルダのファイルをご覧ください。

### テストコード

10行程度の簡単なコードがどう変換されるか確認するためのもの。

- [test/py](test/py) : テストコード。(Pythonで書かれたファイル。)
- [test/cpp](test/cpp) : テストコードをC++のコードに変換したもの。
- [test/cs](test/cs) : テストコードをC#のコードに変換したもの。
- [test/js](test/js) : 🚧テストコードをJavaScriptのコードに変換したもの。
- [test/rs](test/rs) : 🚧テストコードをRustのコードに変換したもの。

### サンプルコード

実行に数秒を要する数十行程度のサンプルコードを別の言語に変換して、その実行時間を比較するためのもの。

Python 版サンプルの実行例:

```bash
PYTHONPATH=src python3 sample/py/01_mandelbrot.py
```

- [sample/py](sample/py) : サンプルコード Pythonで書かれた14個のファイル。
- [sample/cpp](sample/cpp) : サンプルコードをC++のコードに変換したもの。
- [sample/cs](sample/cs) : サンプルコードをC#のコードに変換したもの。
- [sample/js](sample/js) : 🚧サンプルコードをJavaScriptのコードに変換したもの。
- [sample/rs](sample/rs) : 🚧サンプルコードをRustのコードに変換したもの。

## 実行速度の比較

サンプルコードの実行時間（単位: 秒）。

測定条件:
- Python: `PYTHONPATH=src python3 sample/py/<file>.py`
- C++: `g++ -std=c++20 -O2 -I src ...` でビルドした実行ファイル
- C#: `mcs ...` + `mono ...`

|ファイル名|内容| Python(元のコード) | C++に変換後 | C#に変換後 | JSに変換後 | Rustに変換後 |
|-|-|-:|-:|-:|-|-|
|01_mandelbrot|マンデルブロ集合（PNG）|1.689|0.089|0.078|🚧|🚧|
|02_raytrace_spheres|球の簡易レイトレーサ（PNG）|0.414|0.030|0.121|🚧|🚧|
|03_julia_set|ジュリア集合（PNG）|1.380|0.087|0.141|🚧|🚧|
|04_monte_carlo_pi|モンテカルロ法で円周率近似|3.657|0.052|0.200|🚧|🚧|
|05_mandelbrot_zoom|マンデルブロズーム（GIF）|13.802|0.525|2.694|🚧|🚧|
|06_julia_parameter_sweep|ジュリア集合パラメータ掃引（GIF）|5.724|0.234|0.190|🚧|🚧|
|07_game_of_life_loop|ライフゲーム（GIF）|1.290|0.067|0.314|🚧|🚧|
|08_langtons_ant|ラングトンのアリ（GIF）|0.744|0.050|0.234|🚧|🚧|
|09_fire_simulation|炎シミュレーション（GIF）|1.088|0.054|0.522|🚧|🚧|
|10_plasma_effect|プラズマエフェクト（GIF）|2.419|0.221|0.769|🚧|🚧|
|11_lissajous_particles|リサージュ粒子（GIF）|1.118|0.081|0.163|🚧|🚧|
|12_sort_visualizer|ソート可視化（GIF）|3.471|0.233|0.465|🚧|🚧|
|13_maze_generation_steps|迷路生成ステップ（GIF）|0.521|0.033|0.113|🚧|🚧|
|14_raymarching_light_cycle|簡易レイマーチング（GIF）|2.666|0.152|0.467|🚧|🚧|

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
- a[b:c] 形式のスライス構文

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
- 標準ライブラリ網羅対応（`import` 可能モジュールの拡充）
- 回帰テストのさらなる拡充（網羅率向上）
- 例外処理・型推論の高度化
- a[b:c] 以外のスライス構文

対応予定なし

- Python 構文の完全互換（現状はサブセット）
- 動的なimport
- 動的な型付け
- 弱参照, 循環参照 非対応
- スライスオブジェクト


## 開発について

本トランスパイラは、主にGPT-5.3-Codexで開発しています。

## ライセンス

MIT License
