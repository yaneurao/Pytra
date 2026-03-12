# トランスパイラCLIの使い方

このページは、統合 CLI `./pytra` ではなく `py2x.py` / `ir2lang.py` を直接使いたい場合の手順をまとめたものです。  
まず通常利用は [how-to-use.md](./how-to-use.md) を参照してください。

## 実行コマンドの前提（OS別）

このページのコマンド例は、基本的に POSIX シェル（bash/zsh）形式で記載しています。
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
python src/py2x.py --target cpp test/fixtures/collections/iterable.py -o test/transpile/cpp/iterable.cpp
g++ -std=c++20 -O3 -ffast-math -flto -I src -I src/runtime/cpp test/transpile/cpp/iterable.cpp \
  src/runtime/cpp/generated/utils/png.cpp src/runtime/cpp/generated/utils/gif.cpp \
  src/runtime/cpp/native/std/math.cpp src/runtime/cpp/native/std/time.cpp src/runtime/cpp/generated/std/pathlib.cpp \
  src/runtime/cpp/generated/built_in/type_id.cpp \
  src/runtime/cpp/native/core/gc.cpp src/runtime/cpp/native/core/io.cpp \
  -o test/transpile/obj/iterable.out
./test/transpile/obj/iterable.out
```

補足:
- C++ の速度比較は `-O3 -ffast-math -flto` を使用します。
- Python 側で import できるのは `src/pytra/` にあるモジュールと、ユーザー自作 `.py` モジュールです（例: `from pytra.utils import png`, `from pytra.utils.gif import save_gif`, `from pytra.utils.assertions import py_assert_eq`）。
- ユーザーモジュール import は absolute / relative の `from-import` を受理します（例: `from helper import f`, `from .helper import f`, `from ..pkg import y`, `from .helper import *`）。
- `pytra` モジュールに対応するターゲット言語ランタイムを `src/runtime/cpp/` 側に用意します。GC は `base/gc` を使います。
- `src/runtime/cpp/` は責務ごとに `core/`, `generated/`, `native/`, `pytra/` に分かれます。
- 生成物は `src/runtime/cpp/generated/`、C++ 固有 companion と low-level core 正本は `src/runtime/cpp/native/` に置きます。repo 常設の `pytra/core` shim は使いません。
- `python src/py2x.py --target cpp src/pytra/<tree>/<mod>.py -o ... --header-output ...` で `*.cpp` / `*.h` を同時生成できます。
- `python src/py2x.py --target cpp src/pytra/<tree>/<mod>.py --emit-runtime-cpp` を使うと、生成物は `src/runtime/cpp/generated/<tree>/...` に出力します（`<tree>` は `built_in` / `std` / `utils`）。
- 例: `src/pytra/built_in/type_id.py` -> `src/runtime/cpp/generated/built_in/type_id.cpp` と `src/runtime/cpp/generated/built_in/type_id.h`。
- 例: `src/pytra/built_in/numeric_ops.py` / `src/pytra/built_in/zip_ops.py` のような template-only helper は header-only なので `src/runtime/cpp/generated/built_in/*.h` だけを生成し、`.cpp` は作りません。
- 例: `src/pytra/std/math.py` は header-only なので `src/runtime/cpp/generated/std/math.h` を生成し、ネイティブ実体は `src/runtime/cpp/native/std/math.cpp` に置きます。
- `src/pytra/utils/png.py` / `src/pytra/utils/gif.py` は bridge 方式で生成され、`runtime` 側の公開 API に型変換ラッパが付きます。
- `src/pytra/std/json.py` / `src/pytra/utils/assertions.py` も `.h/.cpp` を生成します。
- 不足するネイティブ処理は対応する `src/runtime/cpp/native/...` に補完します（例: `src/runtime/cpp/native/std/math.cpp`）。
- `png.write_rgb_png(...)` は常に PNG を出力します（PPM 出力は廃止）。
- import 依存を可視化したい場合は `python src/py2x.py --target cpp INPUT.py --dump-deps` を使います（`modules/symbols` と `graph` を出力）。
- `pytra` 名前空間は予約済みです。入力ファイルと同じディレクトリに `pytra.py` / `pytra/__init__.py` を置くことはできません。
- ユーザーモジュール import で未解決・循環参照がある場合、`[input_invalid]` で早期エラーにします。
- relative import が entry root より上へ出る場合も `kind=relative_import_escape` で早期エラーにします。
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
- C++ の `list` モデル既定は `pyobj` です。`value` へ戻す rollback は `--cpp-list-model value` を指定してください。
- 複数ファイル出力のビルドは `python3 tools/build_multi_cpp.py out/manifest.json -o out/app.out` を使います。
- `--multi-file` では、ユーザーモジュール import 呼び出しを C++ namespace 参照へ変換してリンク可能な形で出力します。
- 複数ファイル出力の実行一致チェックは `python3 tools/verify_multi_file_outputs.py --samples 01_mandelbrot` のように実行できます。
  - 画像を出力するサンプルは `output:` で示されたファイルのバイナリ一致も検証します。

例:
- 性能優先（既定）:
  - `python src/py2x.py --target cpp INPUT.py -o OUT.cpp --preset native`
- 互換性バランス:
  - `python src/py2x.py --target cpp INPUT.py -o OUT.cpp --preset balanced`
- 互換性優先（注: `int-width=bigint` は未実装）:
  - `python src/py2x.py --target cpp INPUT.py -o OUT.cpp --preset python --int-width 64`
- 最終解決オプション確認:
  - `python src/py2x.py --target cpp INPUT.py --preset balanced --mod-mode native --dump-options`
- selfhost 調査向け（最適化なし）:
  - `python src/py2x.py --target cpp INPUT.py -o OUT.cpp -O0`
- トップ namespace を付ける:
  - `python src/py2x.py --target cpp INPUT.py -o OUT.cpp --top-namespace myproj`

### 画像ランタイム一致チェック（Python正本 vs C++）

次のコマンドで、`src/pytra/utils/png.py` / `src/pytra/utils/gif.py` の出力と `src/runtime/cpp/generated/utils/png.cpp` / `src/runtime/cpp/generated/utils/gif.cpp`（bridge）経由の C++ 出力が一致するかを確認できます。

```bash
python3 tools/verify_image_runtime_parity.py
```

</details>

<details>
<summary>Rust</summary>

```bash
python src/py2x.py --target rs test/fixtures/collections/iterable.py -o test/transpile/rs/iterable.rs
rustc -O test/transpile/rs/iterable.rs -o test/transpile/obj/iterable_rs.out
./test/transpile/obj/iterable_rs.out
```

補足:
- 入力コードで使う Python モジュールに対応する実装は、canonical lane として `src/runtime/rs/{native,generated}/` に置いてください。`src/runtime/rs/pytra/` は互換 lane です。

</details>

<details>
<summary>Ruby</summary>

```bash
python src/py2x.py --target ruby test/fixtures/collections/iterable.py -o test/transpile/ruby/iterable.rb
ruby test/transpile/ruby/iterable.rb
```

補足:
- `py2x.py --target ruby` は EAST3 から Ruby native emitter（`src/backends/ruby/emitter/ruby_native_emitter.py`）で直接コード生成します。
- 画像出力 API（`png.write_rgb_png` / `save_gif`）は現状 no-op runtime hook で受けるため、まずは出力一致よりも構文/実行導線の回帰監視に使ってください。
- 変換回帰は `python3 tools/check_py2rb_transpile.py` で確認できます。
- parity 導線は `python3 tools/runtime_parity_check.py --case-root sample --targets ruby` で実行できます（toolchain 未導入環境では `toolchain_missing` として記録されます）。`elapsed_sec` など不安定行はデフォルトで比較から除外されます。

</details>

<details>
<summary>Lua</summary>

```bash
python src/py2x.py --target lua test/fixtures/collections/iterable.py -o test/transpile/lua/iterable.lua
lua test/transpile/lua/iterable.lua
```

補足:
- `py2x.py --target lua` は EAST3 から Lua native emitter（`src/backends/lua/emitter/lua_native_emitter.py`）で直接コード生成します。
- 画像 API（`png.write_rgb_png` / `save_gif`）は現状 stub/no-op runtime で受けます。
- 変換回帰は `python3 tools/check_py2lua_transpile.py` で確認できます（現状は expected-fail を除外して監視）。
- parity 導線は `python3 tools/runtime_parity_check.py --case-root sample --targets lua 17_monte_carlo_pi` で実行できます（toolchain 未導入環境では `toolchain_missing` として記録されます）。`elapsed_sec` など不安定行はデフォルトで比較から除外されます。
- `sample/lua` は現時点で `02_raytrace_spheres` / `03_julia_set` / `04_orbit_trap_julia` / `17_monte_carlo_pi` を再生成済みです。

</details>

<details>
<summary>PHP</summary>

```bash
python src/py2x.py --target php test/fixtures/collections/iterable.py -o test/transpile/php/iterable.php
php test/transpile/php/iterable.php
```

補足:
- `py2x.py --target php` は EAST3 から PHP native emitter（`src/backends/php/emitter/php_native_emitter.py`）で直接コード生成します。
- runtime は `src/runtime/php/pytra/` を正本とし、生成時に `test/transpile/php/pytra/**` へ同期コピーされます。
- 変換回帰は `python3 tools/check_py2php_transpile.py` で確認できます。
- parity 導線は `python3 tools/runtime_parity_check.py --case-root sample --targets php` で実行できます（toolchain 未導入環境では `toolchain_missing` として記録されます）。

</details>

<details>
<summary>C#</summary>

```bash
python src/py2x.py --target cs test/fixtures/collections/iterable.py -o test/transpile/cs/iterable.cs
python3 tools/check_py2cs_transpile.py
```

補足:
- `py2x.py --target cs` は EAST ベースの変換器です（`.py/.json -> EAST -> C#`）。
- C# 出力品質の段階改善は `docs/ja/todo/index.md` を参照してください。

</details>

<details>
<summary>JavaScript</summary>

```bash
python src/py2x.py --target js test/fixtures/collections/iterable.py -o test/transpile/js/iterable.js
node test/transpile/js/iterable.js
```

補足:
- `browser` / `browser.widgets.dialog` は外部参照として扱われ、`py2x.py --target js` は import 本体を生成しません。

</details>

<details>
<summary>TypeScript</summary>

```bash
python src/py2x.py --target ts test/fixtures/collections/iterable.py -o test/transpile/ts/iterable.ts
npx tsx test/transpile/ts/iterable.ts
```

補足:
- `py2x.py --target ts` は EAST ベースのプレビュー出力です（専用 TSEmitter へ段階移行中）。
- 現在の出力は JavaScript 互換コードをベースにした TypeScript です。

</details>

<details>
<summary>Go</summary>

```bash
python src/py2x.py --target go test/fixtures/collections/iterable.py -o test/transpile/go/iterable.go
go run test/transpile/go/iterable.go
```

補足:
- `py2x.py --target go` は EAST3 から Go native emitter（`src/backends/go/emitter/go_native_emitter.py`）で直接コード生成します。
- 既定出力は Go 単体で実行可能です（sidecar JS は既定では生成しません）。
- sidecar 互換モードは撤去済みで、native 経路のみ利用可能です。

</details>

<details>
<summary>Java</summary>

```bash
python src/py2x.py --target java test/fixtures/collections/iterable.py -o test/transpile/java/iterable.java
javac test/transpile/java/iterable.java
java -cp test/transpile/java iterable
```

補足:
- `py2x.py --target java` は EAST3 から Java native emitter（`src/backends/java/emitter/java_native_emitter.py`）で直接コード生成します。
- 既定出力は Java 単体で実行可能です（sidecar JS は既定では生成しません）。
- sidecar 互換モードは撤去済みで、native 経路のみ利用可能です。

</details>

<details>
<summary>Swift</summary>

```bash
python src/py2x.py --target swift test/fixtures/collections/iterable.py -o test/transpile/swift/iterable.swift
swiftc test/transpile/swift/iterable.swift -o test/transpile/obj/iterable_swift.out
./test/transpile/obj/iterable_swift.out
```

補足:
- `py2x.py --target swift` は EAST3 から Swift native emitter（`src/backends/swift/emitter/swift_native_emitter.py`）で直接コード生成します。
- 既定出力は Swift native 経路で生成され、sidecar JS は既定では生成しません。
- sidecar 互換モードは撤去済みで、native 経路のみ利用可能です。

</details>

<details>
<summary>Kotlin</summary>

```bash
python src/py2x.py --target kotlin test/fixtures/collections/iterable.py -o test/transpile/kotlin/iterable.kt
kotlinc test/transpile/kotlin/iterable.kt -include-runtime -d test/transpile/obj/iterable_kotlin.jar
java -cp test/transpile/obj/iterable_kotlin.jar pytra_iterable
```

補足:
- `py2x.py --target kotlin` は EAST3 から Kotlin native emitter（`src/backends/kotlin/emitter/kotlin_native_emitter.py`）で直接コード生成します。
- 既定出力は Kotlin 単体で実行可能です（sidecar JS は既定では生成しません）。
- sidecar 互換モードは撤去済みで、native 経路のみ利用可能です。

</details>

<details>
<summary>Scala3</summary>

```bash
python src/py2x.py --target scala test/fixtures/collections/iterable.py -o test/transpile/scala/iterable.scala
scala run test/transpile/scala/iterable.scala
```

補足:
- `py2x.py --target scala` は EAST3 から Scala3 native emitter（`src/backends/scala/emitter/scala_native_emitter.py`）で直接コード生成します。
- 変換回帰は `python3 tools/check_py2scala_transpile.py` で確認できます（正例成功 + 既知負例の失敗カテゴリ一致を同時に検証）。
- parity（sample + fixture 正例マニフェスト）は `python3 tools/check_scala_parity.py` で一括確認できます。
- `sample` のみを先に確認する場合は `python3 tools/check_scala_parity.py --skip-fixture` を使用してください。
- `runtime_parity_check` は `elapsed_sec` など不安定行を既定で比較対象から除外します。

</details>

<details>
<summary>EAST (Python -> EAST -> C++)</summary>

```bash
# 1) Python を EAST(JSON) に変換
python src/pytra/compiler/east.py sample/py/01_mandelbrot.py -o test/transpile/east/01_mandelbrot.json --pretty

# 2) EAST(JSON) から C++ へ変換（.py を直接渡しても可）
python src/py2x.py --target cpp test/transpile/east/01_mandelbrot.json -o test/transpile/cpp/01_mandelbrot.cpp

# 3) コンパイルして実行
g++ -std=c++20 -O2 -I src -I src/runtime/cpp test/transpile/cpp/01_mandelbrot.cpp \
  src/runtime/cpp/generated/utils/png.cpp src/runtime/cpp/generated/utils/gif.cpp \
  src/runtime/cpp/generated/built_in/type_id.cpp \
  src/runtime/cpp/native/core/gc.cpp src/runtime/cpp/native/core/io.cpp \
  -o test/transpile/obj/01_mandelbrot
./test/transpile/obj/01_mandelbrot
```

補足:
- EAST 変換器は `src/pytra/compiler/east.py` を使用します。
- EASTベース C++ 生成器は `src/py2x.py --target cpp` を使用します。

</details>
