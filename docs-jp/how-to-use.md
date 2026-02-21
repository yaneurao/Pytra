# 使い方について

<a href="../docs/how-to-use.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


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

## 最初に確認する制約

- Python の標準ライブラリ直接 import は原則非推奨です。`pytra.std.*` を使ってください。
- ただし `math` / `random` / `timeit` / `traceback` / `typing` / `enum` など、`pytra.std.*` に対応 shim がある一部モジュールは正規化して扱えます。
- `import` できるのは `src/pytra/` 配下にあるモジュール（`pytra.std.*`, `pytra.utils.*`, `pytra.compiler.*`）と、ユーザーが作成した自作 `.py` モジュールです。
- 自作モジュール import は仕様上合法ですが、複数ファイル依存解決は段階的に実装中です。
- サポート済みモジュール一覧と API は [モジュール一覧](pylib-modules.md) を参照してください。
- 変換オプションの方針と候補は [オプション仕様](spec-options.md) を参照してください。
- 補助スクリプト（`tools/`）の用途一覧は [ツール一覧](tools.md) を参照してください。


## トランスパイラの使い方

以下は言語別の手順です。必要な言語だけ展開して参照してください。

<details>
<summary>C++</summary>

```bash
python src/py2cpp.py test/fixtures/collections/iterable.py test/transpile/cpp/iterable.cpp
g++ -std=c++20 -O3 -ffast-math -flto -I src -I src/runtime/cpp test/transpile/cpp/iterable.cpp \
  src/runtime/cpp/pytra/utils/png.cpp src/runtime/cpp/pytra/utils/gif.cpp src/runtime/cpp/pytra/std/math.cpp src/runtime/cpp/pytra/std/math-impl.cpp \
  src/runtime/cpp/pytra/std/time.cpp src/runtime/cpp/pytra/std/pathlib.cpp src/runtime/cpp/pytra/std/dataclasses.cpp \
  src/runtime/cpp/pytra/built_in/gc.cpp \
  -o test/transpile/obj/iterable.out
./test/transpile/obj/iterable.out
```

補足:
- C++ の速度比較は `-O3 -ffast-math -flto` を使用します。
- Python 側で import できるのは `src/pytra/` にあるモジュールと、ユーザー自作 `.py` モジュールです（例: `from pytra.utils import png`, `from pytra.utils.gif import save_gif`, `from pytra.utils.assertions import py_assert_eq`）。
- `pytra` モジュールに対応するターゲット言語ランタイムを `src/runtime/cpp/` 側に用意します。GC は `base/gc` を使います。
- `src/runtime/cpp/pytra/{std,utils,compiler}/*.cpp` は手書き固定ではなく、`src/pytra/{std,utils,compiler}/*.py` をトランスパイラで変換して生成・更新する前提です。
- `python3 src/py2cpp.py src/pytra/<tree>/<mod>.py -o ... --header-output ...` で `*.cpp` / `*.h` を同時生成できます。
- `python3 src/py2cpp.py src/pytra/<tree>/<mod>.py --emit-runtime-cpp` を使うと、`src/runtime/cpp/pytra/<tree>/...` の既定パスへ直接生成します（`<tree>` は `std` / `utils` / `compiler`）。
- 例: `src/pytra/std/math.py` -> `src/runtime/cpp/pytra/std/math.cpp` と `src/runtime/cpp/pytra/std/math.h`。
- 例: `src/pytra/compiler/east_parts/core.py` -> `src/runtime/cpp/pytra/compiler/east_parts/core.cpp` と `src/runtime/cpp/pytra/compiler/east_parts/core.h`。
- `src/pytra/utils/png.py` / `src/pytra/utils/gif.py` は bridge 方式で生成され、`runtime` 側の公開 API に型変換ラッパが付きます。
- `src/pytra/std/json.py` / `src/pytra/std/typing.py` / `src/pytra/utils/assertions.py` も `.h/.cpp` を生成します。
- 不足するネイティブ処理は `*-impl.cpp`（例: `src/runtime/cpp/pytra/std/math-impl.cpp`）で補完します。
- `png.write_rgb_png(...)` は常に PNG を出力します（PPM 出力は廃止）。
- import 依存を可視化したい場合は `python src/py2cpp.py INPUT.py --dump-deps` を使います（`modules/symbols` と `graph` を出力）。
- `pytra` 名前空間は予約済みです。入力ファイルと同じディレクトリに `pytra.py` / `pytra/__init__.py` を置くことはできません。
- ユーザーモジュール import で未解決・循環参照がある場合、`[input_invalid]` で早期エラーにします。
- 添字境界チェックは `--bounds-check-mode {always,debug,off}` で切替できます（既定は `off`）。
- 除算仕様は `--floor-div-mode {native,python}` と `--mod-mode {native,python}` で切替できます（既定は `native`）。
- 整数ビット幅は `--int-width {32,64,bigint}` で指定できます（`bigint` は未実装）。
- 文字列の添字/スライス意味論は `--str-index-mode {byte,codepoint,native}` / `--str-slice-mode {byte,codepoint}` で指定できます（`codepoint` は未実装）。
- 生成コード最適化は `-O0`〜`-O3` で指定できます（既定は `-O3`）。
  - `-O0`: 最適化なし（調査向け）
  - `-O1`: 軽量最適化
  - `-O2`: 中程度の最適化
  - `-O3`: 積極最適化（既定）
- オプション群は `--preset {native,balanced,python}` で一括指定できます。個別指定を併用した場合は個別指定が優先されます。
- 解決後のオプションを確認したい場合は `--dump-options` を使います。
- 生成コードのトップ namespace を付けたい場合は `--top-namespace NS` を使います（未指定時はトップ namespace なし）。
- 出力形態は `--multi-file`（既定）と `--single-file` を選べます。
- `--multi-file` は `out/include`, `out/src` + `manifest.json` を生成します。
- 複数ファイル出力先は `--output-dir DIR` で指定できます（`--multi-file` 時）。
- 複数ファイル出力のビルドは `python3 tools/build_multi_cpp.py out/manifest.json -o out/app.out` を使います。
- `--multi-file` では、ユーザーモジュール import 呼び出しを C++ namespace 参照へ変換してリンク可能な形で出力します。
- 複数ファイル出力の実行一致チェックは `python3 tools/verify_multi_file_outputs.py --samples 01_mandelbrot` のように実行できます。
  - 画像を出力するサンプルは `output:` で示されたファイルのバイナリ一致も検証します。

例:
- 性能優先（既定）:
  - `python src/py2cpp.py INPUT.py -o OUT.cpp --preset native`
- 互換性バランス:
  - `python src/py2cpp.py INPUT.py -o OUT.cpp --preset balanced`
- 互換性優先（注: `int-width=bigint` は未実装）:
  - `python src/py2cpp.py INPUT.py -o OUT.cpp --preset python --int-width 64`
- 最終解決オプション確認:
  - `python src/py2cpp.py INPUT.py --preset balanced --mod-mode native --dump-options`
- selfhost 調査向け（最適化なし）:
  - `python src/py2cpp.py INPUT.py -o OUT.cpp -O0`
- トップ namespace を付ける:
  - `python src/py2cpp.py INPUT.py -o OUT.cpp --top-namespace myproj`

### 画像ランタイム一致チェック（Python正本 vs C++）

次のコマンドで、`src/pytra/utils/png.py` / `src/pytra/utils/gif.py` の出力と `src/runtime/cpp/pytra/utils/png.cpp` / `src/runtime/cpp/pytra/utils/gif.cpp`（bridge）経由の C++ 出力が一致するかを確認できます。

```bash
python3 tools/verify_image_runtime_parity.py
```

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
python src/py2cs.py test/fixtures/collections/iterable.py -o test/transpile/cs/iterable.cs
python3 tools/check_py2cs_transpile.py
```

補足:
- `py2cs.py` は EAST ベースの変換器です（`.py/.json -> EAST -> C#`）。
- C# 出力品質の段階改善は `docs-jp/todo.md` を参照してください。

</details>

<details>
<summary>JavaScript</summary>

```bash
python src/py2js.py test/fixtures/collections/iterable.py -o test/transpile/js/iterable.js
node test/transpile/js/iterable.js
```

補足:
- `browser` / `browser.widgets.dialog` は外部参照として扱われ、`py2js.py` は import 本体を生成しません。

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
- `sample/py` の一部で使う `pylib` API は、Go 側ランタイム拡張が必要なケースがあります（最新状況は `docs-jp/todo.md` を参照）。

</details>

<details>
<summary>Java</summary>

```bash
python src/py2java.py test/fixtures/collections/iterable.py test/transpile/java/iterable.java
javac test/transpile/java/iterable.java
java -cp test/transpile/java iterable
```

補足:
- `sample/py` の一部で使う `pylib` API は、Java 側ランタイム拡張が必要なケースがあります（最新状況は `docs-jp/todo.md` を参照）。

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
python src/pytra/compiler/east.py sample/py/01_mandelbrot.py -o test/transpile/east/01_mandelbrot.json --pretty

# 2) EAST(JSON) から C++ へ変換（.py を直接渡しても可）
python src/py2cpp.py test/transpile/east/01_mandelbrot.json -o test/transpile/cpp/01_mandelbrot.cpp

# 3) コンパイルして実行
g++ -std=c++20 -O2 -I src -I src/runtime/cpp test/transpile/cpp/01_mandelbrot.cpp \
  src/runtime/cpp/pytra/utils/png.cpp src/runtime/cpp/pytra/utils/gif.cpp \
  -o test/transpile/obj/01_mandelbrot
./test/transpile/obj/01_mandelbrot
```

補足:
- EAST 変換器は `src/pytra/compiler/east.py` を使用します。
- EASTベース C++ 生成器は `src/py2cpp.py` を使用します。

</details>

## selfhost 検証手順（`py2cpp.py` -> `py2cpp.cpp`）

前提:
- プロジェクトルートで実行する。
- `g++` が使えること。
- `selfhost/` は検証用の作業ディレクトリ（Git管理外）として扱う。

```bash
# 0) selfhost C++ を生成してビルド（ランタイム .cpp も含めてリンク）
python3 tools/build_selfhost.py > selfhost/build.all.log 2>&1

# 1) ビルドエラーをカテゴリ確認
rg "error:" selfhost/build.all.log
```

コンパイル成功時の比較手順:

```bash
# 2) selfhost 実行ファイルで sample/py/01 を変換
mkdir -p test/transpile/cpp2
./selfhost/py2cpp.out sample/py/01_mandelbrot.py test/transpile/cpp2/01_mandelbrot.cpp

# 3) Python 版 py2cpp でも同じ入力を変換
python3 src/py2cpp.py sample/py/01_mandelbrot.py -o test/transpile/cpp/01_mandelbrot.cpp

# 4) 生成差分を確認（ソース差分は許容、まずは確認用）
diff -u test/transpile/cpp/01_mandelbrot.cpp test/transpile/cpp2/01_mandelbrot.cpp || true

# 5) Python版とselfhost版の出力差分を代表ケースで一括確認
python3 tools/check_selfhost_cpp_diff.py --show-diff
```

補足:
- 現時点の `selfhost/py2cpp.py` は `load_east()` をスタブ化しているため、`INPUT.py` 変換は未対応です。
- 上記の 2) 以降は selfhost 入力パーサ復帰後に有効化する想定です。

失敗時の確認ポイント:
- `build.all.log` の `error:` を先に分類し、型系（`std::any` / `optional`）と構文系（未lowering）を分ける。
- `selfhost/py2cpp.cpp` の該当行に対して、元の `src/py2cpp.py` の記述が `Any` 混在を増やしていないか確認する。
- `selfhost/py2cpp.py` が古い場合があるため、毎回 `cp src/py2cpp.py selfhost/py2cpp.py` を先に実行する。

## CodeEmitter 作業時の変換チェック

`CodeEmitter` を段階的に改修するときは、各ステップごとに次を実行します。

```bash
python3 tools/check_py2cpp_transpile.py
python3 tools/check_py2rs_transpile.py
python3 tools/check_py2js_transpile.py
```

補足:
- 既定では既知の負例フィクスチャ（`test/fixtures/signature/ng_*.py` と `test/fixtures/typing/any_class_alias.py`）を除外して判定します。
- 負例も含めて確認したい場合は `--include-expected-failures` を付けます。

## 共通の制約と注意点

Pytra は Python のサブセットを対象とします。通常の Python コードとして実行できる入力でも、未対応構文を含む場合は変換時に失敗します。

`py2cpp` の機能サポート状況を細かく確認したい場合は、`docs-jp/spec-py2cpp-support.md` を参照してください（テスト根拠つき）。

### 0. エラーカテゴリ

`src/py2cpp.py` の失敗時メッセージは、次のカテゴリで表示されます。

- `[user_syntax_error]`: ユーザーコードの文法エラーです。
- `[not_implemented]`: まだ実装されていない構文です（将来対応候補）。
- `[unsupported_by_design]`: 言語仕様として非対応の構文です。
- `[internal_error]`: トランスパイラ内部エラーです。

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
- 型注釈エイリアス: `byte` は `uint8` として扱います（1文字/1byte用途）。
- バイト列: `bytes` / `bytearray` -> `vector<uint8_t>`
- コンテナ:
  - `list[T] -> list<T>`（`std::vector<T>` ラッパー）
  - `dict[K, V] -> dict<K, V>`（`std::unordered_map<K,V>` ラッパー）
  - `set[T] -> set<T>`（`std::unordered_set<T>` ラッパー）
  - `tuple[...] -> tuple<...>`
- `dict` / `set` は Python 互換メソッド（`get`, `keys`, `values`, `items`, `add`, `discard`, `remove`）を `py_runtime.h` 側で提供します。
- `str` / `list` / `dict` / `set` / `bytes` / `bytearray` は標準コンテナ継承ではなく wrapper として扱います。

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
- コンテナ: `list[T] -> List<T>`, `dict[K, V] -> Dictionary<K, V>`, `set[T] -> HashSet<T>`, `tuple[...] -> (T1, T2, ...)`

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
- Go の型注釈反映を強化して `any` 退化を減らす作業は `docs-jp/todo.md` の未完了項目です。

</details>

<details>
<summary>Java</summary>

- 現状は `Object` ベース実装を併用します。
- `bytes` / `bytearray` はランタイムで `byte[]` として扱います。
- Java の型注釈反映を強化して `Object` 退化を減らす作業は `docs-jp/todo.md` の未完了項目です。

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

- Python 側で `import` できるモジュールは `src/pytra/` 配下のモジュール（`pytra.std.*`, `pytra.utils.*`, `pytra.compiler.*`）と、ユーザー自作 `.py` モジュールです。
- `pytra` モジュールごとに、ターゲット言語側の対応ランタイムが必要です。
- その対応ランタイムは、原則として `src/pytra/utils/*.py` / `src/pytra/std/*.py` を各言語向けトランスパイラで変換して生成します（手書きは最小限）。

```python
from pytra.utils import png
from pytra.std.pathlib import Path
```

上記を変換する場合、対象言語側でも `pytra.utils.png` / `pytra.std.pathlib` 相当の実装が必要です（原則として `src/pytra/utils/*.py` と `src/pytra/std/*.py` からトランスパイラで生成します）。
