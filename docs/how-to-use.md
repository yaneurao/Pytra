# 使い方について

## トランスパイラ本体

| 変換元 | 変換先 | 実装 |
| - | - | - |
| Python | C++ | [src/py2cpp.py](../src/py2cpp.py) |
| Python | Rust | [src/py2rs.py](../src/py2rs.py) |
| Python | C# | [src/py2cs.py](../src/py2cs.py) |
| Python | JavaScript | [src/py2js.py](../src/py2js.py) |
| Python | TypeScript | [src/py2ts.py](../src/py2ts.py) |
| Python | Go | [src/py2go.py](../src/py2go.py) |
| Python | Java | [src/py2java.py](../src/py2java.py) |
| Python | Swift | [src/py2swift.py](../src/py2swift.py) |
| Python | Kotlin | [src/py2kotlin.py](../src/py2kotlin.py) |


## トランスパイラの使い方

### C++

```bash
python src/py2cpp.py test/py/case28_iterable.py test/cpp/case28_iterable.cpp
g++ -std=c++20 -O3 -ffast-math -flto -I src test/cpp/case28_iterable.cpp \
  src/cpp_module/png.cpp src/cpp_module/gif.cpp src/cpp_module/math.cpp \
  src/cpp_module/time.cpp src/cpp_module/pathlib.cpp src/cpp_module/dataclasses.cpp \
  src/cpp_module/ast.cpp src/cpp_module/gc.cpp \
  -o test/obj/case28_iterable.out
./test/obj/case28_iterable.out
```

### Rust

```bash
python src/py2rs.py test/py/case28_iterable.py test/rs/case28_iterable.rs
rustc -O test/rs/case28_iterable.rs -o test/obj/case28_iterable_rs.out
./test/obj/case28_iterable_rs.out
```

### C#

```bash
python src/py2cs.py test/py/case28_iterable.py test/cs/case28_iterable.cs
mcs -out:test/obj/case28_iterable.exe \
  test/cs/case28_iterable.cs \
  src/cs_module/py_runtime.cs src/cs_module/time.cs src/cs_module/png_helper.cs
mono test/obj/case28_iterable.exe
```

### JavaScript

```bash
python src/py2js.py test/py/case28_iterable.py test/js/case28_iterable.js
node test/js/case28_iterable.js
```

### TypeScript

```bash
python src/py2ts.py test/py/case28_iterable.py test/ts/case28_iterable.ts
npx tsx test/ts/case28_iterable.ts
```

### Go

```bash
python src/py2go.py test/py/case28_iterable.py test/go/case28_iterable.go
go run test/go/case28_iterable.go
```

### Java

```bash
python src/py2java.py test/py/case28_iterable.py test/java/case28_iterable.java
javac test/java/case28_iterable.java
java -cp test/java case28_iterable
```

### Swift

```bash
python src/py2swift.py test/py/case28_iterable.py test/swift/case28_iterable.swift
swiftc test/swift/case28_iterable.swift -o test/obj/case28_iterable_swift.out
./test/obj/case28_iterable_swift.out
```

### Kotlin

```bash
python src/py2kotlin.py test/py/case28_iterable.py test/kotlin/case28_iterable.kt
kotlinc test/kotlin/case28_iterable.kt -include-runtime -d test/obj/case28_iterable_kotlin.jar
java -cp test/obj/case28_iterable_kotlin.jar pytra_case28_iterable
```

## 注意点

- 対象は Python のサブセットです。一般的な Python コードすべてが変換できるわけではありません。
- 変数には、型注釈が必要です。（ただし一部は推論可能）。
- Python で `import` するモジュールは、対応するランタイム実装が `src/cpp_module/` または `src/cs_module/` に必要です。
- JavaScript / TypeScript のネイティブ変換で `import` を扱う場合は、対応するランタイム実装を `src/js_module/` / `src/ts_module/` に用意します（例: `py_runtime`, `time`, `math`）。
- `sample/py/` を Python のまま実行する場合は、`py_module` を解決するため `PYTHONPATH=src` を付けて実行してください（例: `PYTHONPATH=src python3 sample/py/01_mandelbrot.py`）。
- 生成された C++/C# は「読みやすさ」より「変換の忠実性」を優先しています。
- 現在の `py2rs.py` は最小実装で、Python スクリプトを Rust 実行ファイルへ埋め込み、実行時に Python インタプリタを呼び出します（`python3` 優先、`python` フォールバック）。
- 現在の `py2js.py` / `py2ts.py` はネイティブ変換モードです。生成 JS/TS は Python インタプリタを呼び出しません。
- 現在の `py2go.py` / `py2java.py` はネイティブ変換モードです。生成 Go/Java は Python インタプリタを呼び出しません。
- 現在の `py2swift.py` / `py2kotlin.py` は Node バックエンド実行モードです。生成 Swift/Kotlin は `node` を呼び出し、`python3` は呼び出しません。
- 現時点では `sample/py` の一部で使っている `math` / `png_helper` / `gif_helper` 系 API の Go/Java ネイティブ対応が未完了です。


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
