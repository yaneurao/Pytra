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
python src/py2cpp.py test/fixtures/collections/iterable.py test/transpile/cpp/iterable.cpp
g++ -std=c++20 -O3 -ffast-math -flto -I src test/transpile/cpp/iterable.cpp \
  src/cpp_module/png.cpp src/cpp_module/gif.cpp src/cpp_module/math.cpp \
  src/cpp_module/time.cpp src/cpp_module/pathlib.cpp src/cpp_module/dataclasses.cpp \
  src/cpp_module/gc.cpp \
  -o test/transpile/obj/iterable.out
./test/transpile/obj/iterable.out
```

補足:
- C++ の速度比較は `-O3 -ffast-math -flto` を使用します。
- 入力コードで使う Python モジュールに対応する実装を `src/cpp_module/` に用意してください（例: `math`, `time`, `pathlib`, `png`, `gif`）。
- 実行時に `--pytra-image-format=ppm` を付けると、`png_helper.write_rgb_png(...)` は PNG ではなく PPM(P6) を出力します。
  - 例: `./test/transpile/obj/iterable.out --pytra-image-format=ppm`
  - この場合、出力拡張子は実行時に `.ppm` へ切り替わります（元コード上の `out_path` 文字列表示はそのままです）。

</details>

<details>
<summary>Rust</summary>

```bash
python src/py2rs.py test/fixtures/collections/iterable.py test/transpile/rs/iterable.rs
rustc -O test/transpile/rs/iterable.rs -o test/transpile/obj/iterable_rs.out
./test/transpile/obj/iterable_rs.out
```

補足:
- 入力コードで使う Python モジュールに対応する実装を `src/rs_module/` に用意してください。

</details>

<details>
<summary>C#</summary>

```bash
python src/py2cs.py test/fixtures/collections/iterable.py test/transpile/cs/iterable.cs
mcs -out:test/transpile/obj/iterable.exe \
  test/transpile/cs/iterable.cs \
  src/cs_module/py_runtime.cs src/cs_module/time.cs src/cs_module/png_helper.cs src/cs_module/pathlib.cs
mono test/transpile/obj/iterable.exe
```

補足:
- 生成コードで利用するランタイム実装（`src/cs_module/*.cs`）を一緒にコンパイルしてください。

</details>

<details>
<summary>JavaScript</summary>

```bash
python src/py2js.py test/fixtures/collections/iterable.py test/transpile/js/iterable.js
node test/transpile/js/iterable.js
```

補足:
- `import` を使う場合は `src/js_module/` に対応ランタイム実装が必要です。

</details>

<details>
<summary>TypeScript</summary>

```bash
python src/py2ts.py test/fixtures/collections/iterable.py test/transpile/ts/iterable.ts
npx tsx test/transpile/ts/iterable.ts
```

補足:
- `import` を使う場合は `src/ts_module/` に対応ランタイム実装が必要です。

</details>

<details>
<summary>Go</summary>

```bash
python src/py2go.py test/fixtures/collections/iterable.py test/transpile/go/iterable.go
go run test/transpile/go/iterable.go
```

補足:
- `sample/py` の一部で使う `math` / `png_helper` / `gif_helper` 系 API は、Go 側ランタイム拡張が必要なケースがあります（最新状況は `docs/todo.md` を参照）。

</details>

<details>
<summary>Java</summary>

```bash
python src/py2java.py test/fixtures/collections/iterable.py test/transpile/java/iterable.java
javac test/transpile/java/iterable.java
java -cp test/transpile/java iterable
```

補足:
- `sample/py` の一部で使う `math` / `png_helper` / `gif_helper` 系 API は、Java 側ランタイム拡張が必要なケースがあります（最新状況は `docs/todo.md` を参照）。

</details>

<details>
<summary>Swift</summary>

```bash
python src/py2swift.py test/fixtures/collections/iterable.py test/transpile/swift/iterable.swift
swiftc test/transpile/swift/iterable.swift -o test/transpile/obj/iterable_swift.out
./test/transpile/obj/iterable_swift.out
```

補足:
- `py2swift.py` は Node バックエンド実行モードです（実行時に `node` を利用）。

</details>

<details>
<summary>Kotlin</summary>

```bash
python src/py2kotlin.py test/fixtures/collections/iterable.py test/transpile/kotlin/iterable.kt
kotlinc test/transpile/kotlin/iterable.kt -include-runtime -d test/transpile/obj/iterable_kotlin.jar
java -cp test/transpile/obj/iterable_kotlin.jar pytra_iterable
```

補足:
- `py2kotlin.py` は Node バックエンド実行モードです（実行時に `node` を利用）。

</details>

<details>
<summary>EAST (Python -> EAST -> C++)</summary>

```bash
# 1) Python を EAST(JSON) に変換
python src/common/east.py sample/py/01_mandelbrot.py -o test/transpile/east/01_mandelbrot.json --pretty

# 2) EAST(JSON) から C++ へ変換（.py を直接渡しても可）
python src/py2cpp.py test/transpile/east/01_mandelbrot.json -o test/transpile/cpp/01_mandelbrot.cpp

# 3) コンパイルして実行
g++ -std=c++20 -O2 -I src test/transpile/cpp/01_mandelbrot.cpp \
  src/cpp_module/png.cpp src/cpp_module/gif.cpp \
  -o test/transpile/obj/01_mandelbrot
./test/transpile/obj/01_mandelbrot
```

補足:
- EAST 変換器は `src/common/east.py`、EASTベース C++ 生成器は `src/py2cpp.py` を使用します。

</details>

## selfhost 検証手順（`py2cpp.py` -> `py2cpp.cpp`）

前提:
- プロジェクトルートで実行する。
- `g++` が使えること。
- `selfhost/` は検証用の作業ディレクトリ（Git管理外）として扱う。

```bash
# 0) 入力となる selfhost ソースを最新化
cp src/py2cpp.py selfhost/py2cpp.py

# 1) Python 版 py2cpp で selfhost 用 C++ を生成
python3 src/py2cpp.py selfhost/py2cpp.py -o selfhost/py2cpp.cpp

# 2) 生成 C++ をコンパイル
g++ -std=c++20 -O2 -I src selfhost/py2cpp.cpp -o selfhost/py2cpp.out \
  2> selfhost/build.stderr.log

# 3) ビルドエラーをカテゴリ確認
rg "error:" selfhost/build.stderr.log
```

コンパイル成功時の比較手順:

```bash
# 4) selfhost 実行ファイルで sample/py/01 を変換
mkdir -p test/transpile/cpp2
./selfhost/py2cpp.out sample/py/01_mandelbrot.py test/transpile/cpp2/01_mandelbrot.cpp

# 5) Python 版 py2cpp でも同じ入力を変換
python3 src/py2cpp.py sample/py/01_mandelbrot.py -o test/transpile/cpp/01_mandelbrot.cpp

# 6) 生成差分を確認（ソース差分は許容、まずは確認用）
diff -u test/transpile/cpp/01_mandelbrot.cpp test/transpile/cpp2/01_mandelbrot.cpp || true
```

失敗時の確認ポイント:
- `build.stderr.log` の `error:` を先に分類し、型系（`std::any` / `optional`）と構文系（未lowering）を分ける。
- `selfhost/py2cpp.cpp` の該当行に対して、元の `src/py2cpp.py` の記述が `Any` 混在を増やしていないか確認する。
- `selfhost/py2cpp.py` が古い場合があるため、毎回 `cp src/py2cpp.py selfhost/py2cpp.py` を先に実行する。

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

以下は言語別の対応です。必要な言語だけ展開して確認してください。

<details>
<summary>C++</summary>

- 基本型: `int -> long long`, `float -> double`, `float32 -> float`, `str -> string`, `bool -> bool`
- 固定幅整数: `int8 -> int8_t`, `uint8 -> uint8_t`, `int16 -> int16_t`, `uint16 -> uint16_t`, `int32 -> int32_t`, `uint32 -> uint32_t`, `int64 -> int64_t`, `uint64 -> uint64_t`
- バイト列: `bytes` / `bytearray` -> `vector<uint8_t>`
- コンテナ: `list[T] -> vector<T>`, `dict[K, V] -> unordered_map<K, V>`, `set[T] -> unordered_set<T>`, `tuple[...] -> tuple<...>`

</details>

<details>
<summary>Rust</summary>

- 基本型: `int -> i64`, `float -> f64`, `float32 -> f32`, `str -> String`, `bool -> bool`
- 固定幅整数: `int8 -> i8`, `uint8 -> u8`, `int16 -> i16`, `uint16 -> u16`, `int32 -> i32`, `uint32 -> u32`, `int64 -> i64`, `uint64 -> u64`
- バイト列: `bytes` / `bytearray` -> `Vec<u8>`
- コンテナ: `list[T] -> Vec<T>`, `dict[K, V] -> HashMap<K, V>`, `set[T] -> HashSet<T>`, `tuple[...] -> (... )`

</details>

<details>
<summary>C#</summary>

- 基本型: `int -> long`, `float -> double`, `float32 -> float`, `str -> string`, `bool -> bool`
- 固定幅整数: `int8 -> sbyte`, `uint8 -> byte`, `int16 -> short`, `uint16 -> ushort`, `int32 -> int`, `uint32 -> uint`, `int64 -> long`, `uint64 -> ulong`
- バイト列: `bytes` / `bytearray` -> `List<byte>`
- コンテナ: `list[T] -> List<T>`, `dict[K, V] -> Dictionary<K, V>`, `set[T] -> HashSet<T>`, `tuple[...] -> Tuple<...>`

</details>

<details>
<summary>JavaScript / TypeScript</summary>

- 数値は `number` ベースで扱います。
- `bytes` / `bytearray` はランタイム上 `number[]` として扱います（`pyBytearray` / `pyBytes`）。
- `list` / `tuple` は配列、`dict` は `Map` 相当、`set` は `Set` 相当へ変換されます（ランタイム補助を併用）。

</details>

<details>
<summary>Go</summary>

- 現状は `any` ベース実装を併用しますが、数値演算部分では `int` / `float64` / `bool` / `string` の推論を行います。
- `bytes` / `bytearray` はランタイムで `[]byte` として扱います。
- Go の型注釈反映を強化して `any` 退化を減らす作業は `docs/todo.md` の未完了項目です。

</details>

<details>
<summary>Java</summary>

- 現状は `Object` ベース実装を併用します。
- `bytes` / `bytearray` はランタイムで `byte[]` として扱います。
- Java の型注釈反映を強化して `Object` 退化を減らす作業は `docs/todo.md` の未完了項目です。

</details>

<details>
<summary>Swift / Kotlin</summary>

- 現状は Node バックエンド実行方式のため、型変換仕様は実質 JavaScript 側の型表現に準拠します。
- そのため、数値は `number` 相当、`bytes` / `bytearray` は `number[]` 相当で扱われます。

</details>

```python
# 型注釈の例
buf1: bytearray = bytearray(16)
buf2: bytes = bytes(buf1)
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
