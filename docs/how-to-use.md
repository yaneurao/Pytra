# 使い方について

## トランスパイラ本体

| 変換元 | 変換先 | 実装 |
| - | - | - |
| Python | C++ | [src/py2cpp.py](../src/py2cpp.py) |
| Python | C# | [src/py2cs.py](../src/py2cs.py) |
| Python | Rust | [src/py2rs.py](../src/py2rs.py) |
| Python | JavaScript | 🚧 予定 |
| Python | TypeScript | 🚧 予定 |
| Python | Go | 🚧 予定 |
| Python | Java | 🚧 予定 |
| Python | Swift | 🚧 予定 |
| Python | Kotlin | 🚧 予定 |


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

### 3. Python から Rust へ変換

```bash
python src/py2rs.py <input.py> <output.rs>
```

例:

```bash
python src/py2rs.py test/py/case28_iterable.py test/rs/case28_iterable.rs
```

### 4. 変換後コードの実行例

#### C++

```bash
g++ -std=c++20 -O3 -ffast-math -flto -I src test/cpp/case28_iterable.cpp \
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

#### Rust

```bash
rustc -O test/rs/case28_iterable.rs -o test/obj/case28_iterable_rs.out
./test/obj/case28_iterable_rs.out
```

### 5. 注意点

- 対象は Python のサブセットです。一般的な Python コードすべてが変換できるわけではありません。
- 変数には、型注釈が必要です。（ただし一部は推論可能）。
- Python で `import` するモジュールは、対応するランタイム実装が `src/cpp_module/` または `src/cs_module/` に必要です。
- `sample/py/` を Python のまま実行する場合は、`py_module` を解決するため `PYTHONPATH=src` を付けて実行してください（例: `PYTHONPATH=src python3 sample/py/01_mandelbrot.py`）。
- 生成された C++/C# は「読みやすさ」より「変換の忠実性」を優先しています。
- 現在の `py2rs.py` は最小実装で、Python スクリプトを Rust 実行ファイルへ埋め込み、実行時に Python インタプリタを呼び出します（`python3` 優先、`python` フォールバック）。


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
