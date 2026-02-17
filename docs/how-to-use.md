# 使い方について

## 実行コマンドの前提（OS別）

このドキュメントのコマンド例は、基本的に POSIX シェル（bash/zsh）形式で記載しています。  
Windows では次の読み替えを行ってください。

- Python 実行:
  - POSIX: `python ...`
  - Windows: `py ...`（または `python ...`）
- 環境変数の一時指定:
  - POSIX: `PYTHONPATH=src python ...`
  - Windows PowerShell: `$env:PYTHONPATH='src'; py ...`
  - Windows cmd.exe: `set PYTHONPATH=src && py ...`
- 複数行コマンドの継続:
  - POSIX: `\`
  - Windows PowerShell: `` ` ``
  - Windows cmd.exe: `^`

## トランスパイラの使い方

以下は言語別の手順です。必要な言語だけ展開して参照してください。

<details>
<summary>C++</summary>

```bash
python src/py2cpp.py test/py/case28_iterable.py test/cpp/case28_iterable.cpp
g++ -std=c++20 -O3 -ffast-math -flto -I src test/cpp/case28_iterable.cpp \
  src/cpp_module/png.cpp src/cpp_module/gif.cpp src/cpp_module/math.cpp \
  src/cpp_module/time.cpp src/cpp_module/pathlib.cpp src/cpp_module/dataclasses.cpp \
  src/cpp_module/ast.cpp src/cpp_module/gc.cpp \
  -o test/obj/case28_iterable.out
./test/obj/case28_iterable.out
```

補足:
- C++ の速度比較は `-O3 -ffast-math -flto` を使用します。
- 入力コードで使う Python モジュールに対応する実装を `src/cpp_module/` に用意してください（例: `math`, `time`, `pathlib`, `png`, `gif`）。

</details>

<details>
<summary>Rust</summary>

```bash
python src/py2rs.py test/py/case28_iterable.py test/rs/case28_iterable.rs
rustc -O test/rs/case28_iterable.rs -o test/obj/case28_iterable_rs.out
./test/obj/case28_iterable_rs.out
```

補足:
- 入力コードで使う Python モジュールに対応する実装を `src/rs_module/` に用意してください。

</details>

<details>
<summary>C#</summary>

```bash
python src/py2cs.py test/py/case28_iterable.py test/cs/case28_iterable.cs
mcs -out:test/obj/case28_iterable.exe \
  test/cs/case28_iterable.cs \
  src/cs_module/py_runtime.cs src/cs_module/time.cs src/cs_module/png_helper.cs
mono test/obj/case28_iterable.exe
```

補足:
- 生成コードで利用するランタイム実装（`src/cs_module/*.cs`）を一緒にコンパイルしてください。

</details>

<details>
<summary>JavaScript</summary>

```bash
python src/py2js.py test/py/case28_iterable.py test/js/case28_iterable.js
node test/js/case28_iterable.js
```

補足:
- `import` を使う場合は `src/js_module/` に対応ランタイム実装が必要です。

</details>

<details>
<summary>TypeScript</summary>

```bash
python src/py2ts.py test/py/case28_iterable.py test/ts/case28_iterable.ts
npx tsx test/ts/case28_iterable.ts
```

補足:
- `import` を使う場合は `src/ts_module/` に対応ランタイム実装が必要です。

</details>

<details>
<summary>Go</summary>

```bash
python src/py2go.py test/py/case28_iterable.py test/go/case28_iterable.go
go run test/go/case28_iterable.go
```

補足:
- `sample/py` の一部で使う `math` / `png_helper` / `gif_helper` 系 API は、Go 側ランタイム拡張が必要なケースがあります（最新状況は `docs/todo.md` を参照）。

</details>

<details>
<summary>Java</summary>

```bash
python src/py2java.py test/py/case28_iterable.py test/java/case28_iterable.java
javac test/java/case28_iterable.java
java -cp test/java case28_iterable
```

補足:
- `sample/py` の一部で使う `math` / `png_helper` / `gif_helper` 系 API は、Java 側ランタイム拡張が必要なケースがあります（最新状況は `docs/todo.md` を参照）。

</details>

<details>
<summary>Swift</summary>

```bash
python src/py2swift.py test/py/case28_iterable.py test/swift/case28_iterable.swift
swiftc test/swift/case28_iterable.swift -o test/obj/case28_iterable_swift.out
./test/obj/case28_iterable_swift.out
```

補足:
- `py2swift.py` は Node バックエンド実行モードです（実行時に `node` を利用）。

</details>

<details>
<summary>Kotlin</summary>

```bash
python src/py2kotlin.py test/py/case28_iterable.py test/kotlin/case28_iterable.kt
kotlinc test/kotlin/case28_iterable.kt -include-runtime -d test/obj/case28_iterable_kotlin.jar
java -cp test/obj/case28_iterable_kotlin.jar pytra_case28_iterable
```

補足:
- `py2kotlin.py` は Node バックエンド実行モードです（実行時に `node` を利用）。

</details>

## 共通の制約と注意点

Pytra は Python のサブセットを対象とします。通常の Python コードとして実行できる入力でも、未対応構文を含む場合は変換時に失敗します。

### 1. 型注釈と型推論

- 基本は型注釈付きコードを推奨します。
- ただし、次のような「型が一意に決まる代入」は注釈を省略できます。

```python
# リテラルからの推論
x = 1         # int
y = 1.5       # float
s = "hello"   # str

# 既知型からの推論
a: int = 10
b = a         # int
```

- 型が曖昧になるケースは注釈を付けてください。

```python
# 推論が不安定になりやすい例
values = []              # 要素型が不明
table = {}               # key/value 型が不明
```

### 2. 型名の扱い

- 数値・文字列の基本型は、主に次の対応で変換されます。
  - C++: `int -> long long`, `float -> double`, `float32 -> float`, `str -> string`, `bool -> bool`
  - C#: `int -> long`, `float -> double`, `float32 -> float`, `str -> string`, `bool -> bool`
  - Rust: `int -> i64`, `float -> f64`, `float32 -> f32`, `str -> String`, `bool -> bool`
- 固定幅整数注釈（`int8,uint8,int16,uint16,int32,uint32,int64,uint64`）は、C++/C#/Rust で対応する固定幅型へ変換されます。
  - 例: `int8` は C++ で `int8_t`、C# で `sbyte`、Rust で `i8`
- `bytes` / `bytearray` は次のように変換されます。
  - C++: `vector<uint8_t>`
  - C#: `List<byte>`
  - Rust: `Vec<u8>`
  - JS/TS: `number[]`（ランタイムの `pyBytearray` / `pyBytes`）
  - Go/Java: ランタイムで `[]byte` / `byte[]` を扱います（注釈は `any` / `Object` ベース）
- コンテナ型注釈は次のように変換されます。
  - `list[T]` -> C++ `vector<T>` / C# `List<T>` / Rust `Vec<T>`
  - `dict[K, V]` -> C++ `unordered_map<K, V>` / C# `Dictionary<K, V>` / Rust `HashMap<K, V>`
  - `set[T]` -> C++ `unordered_set<T>` / C# `HashSet<T>` / Rust `HashSet<T>`
  - `tuple[...]` -> C++ `tuple<...>` / C# `Tuple<...>` / Rust `(... )`

```python
# bytes / bytearray の例
buf1: bytearray = bytearray(16)
buf2: bytes = bytes(buf1)

# コンテナ注釈の例
ids: list[int] = [1, 2, 3]
name_by_id: dict[int, str] = {1: "alice"}
```

### 3. import とランタイムモジュール

- Python 側で `import` したモジュールは、ターゲット言語側に対応ランタイムが必要です。
- 例: C++ なら `src/cpp_module/`, C# なら `src/cs_module/`, JS/TS なら `src/js_module` / `src/ts_module`。

```python
import math
from pathlib import Path
```

上記を変換する場合、対象言語側でも `math` / `pathlib` 相当の実装が必要です。

### 4. 実行時の注意

- `sample/py/` を Python のまま実行する場合は、`py_module` 解決のため `PYTHONPATH=src` を付けます。

POSIX:

```bash
PYTHONPATH=src python3 sample/py/01_mandelbrot.py
```

Windows PowerShell:

```powershell
$env:PYTHONPATH='src'; py sample/py/01_mandelbrot.py
```

Windows cmd.exe:

```bat
set PYTHONPATH=src && py sample/py/01_mandelbrot.py
```

- 生成コードは「読みやすさ」より「変換の忠実性」を優先しています。
