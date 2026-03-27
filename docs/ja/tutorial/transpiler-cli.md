<a href="../../en/tutorial/transpiler-cli.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# トランスパイラCLIの使い方

このページは、統合 CLI `./pytra` ではなく `pytra-cli.py` / `toolchain/emit/cpp.py` 等を直接使いたい場合の手順をまとめたものです。
まず通常利用は [how-to-use.md](./how-to-use.md) を参照してください。

## パイプライン構成

Pytra の変換パイプラインは gcc の `cc1` / `as` / `ld` のアナロジーに基づき、4 段に分離されています。

```
.py → [frontends] → EAST → [compile] → EAST3 → [link] → linked EAST → [emit] → .cpp/.rs/...
```

| 段 | 責務 | ディレクトリ | エントリポイント |
|---|---|---|---|
| parse | `.py` → EAST | `src/toolchain/frontends/` | `pytra-cli.py compile` |
| compile | EAST1 → EAST2 → EAST3 | `src/toolchain/compile/` | （parse に統合） |
| link | EAST3 modules → linked EAST | `src/toolchain/link/` | `pytra-cli.py --link-only` |
| emit | linked EAST → target source | `src/toolchain/emit/<lang>/` | `toolchain/emit/cpp.py` 等 |

- `pytra-cli.py` は compile + link を担当し、backend（emit）に依存しません。
- emit は言語ごとに独立したエントリポイント（`toolchain/emit/cpp.py`, `toolchain/emit/rs.py`, ...）で実行します。
- `./pytra --build` は内部で compile → link → emit → g++ をサブプロセスで連鎖します。

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

## エントリモジュールと依存解決

- CLI に指定する入力ファイルは **1 つ** です。これがエントリモジュールになります。
- エントリモジュールの `import` を起点に依存先モジュールが **自動的に** 収集されます。ユーザーが依存先を列挙する必要はありません。
- エントリモジュールの `if __name__ == "__main__":` ブロックがターゲット言語の `main` 関数に変換されます。
- 依存先モジュールに `if __name__ == "__main__":` があっても無視されます（Python と同じ挙動です）。

```bash
# エントリ: main.py → import helper → helper.py は自動で収集される
./pytra main.py --target cpp --build --output-dir out
```

## トランスパイラの使い方

以下は言語別の手順です。必要な言語だけ展開して参照してください。

<details>
<summary>C++</summary>

### 最短手順（統合 CLI）

```bash
# transpile + build + run を一発で
./pytra INPUT.py --target cpp --build --run --output-dir out --exe app.out
```

### compile → link → emit パイプライン（pytra-cli.py + toolchain/emit/cpp.py 直接）

C++ 変換は内部で compile → link → emit の 3 段を経由します。

```bash
# 1) multi-file 出力（統合 CLI 経由）
./pytra INPUT.py --output-dir out/cpp_case

# 2) 2 段パイプライン（pytra-cli.py + toolchain/emit/cpp.py を直接使用）
# Stage 1: compile + link → linked EAST（backend 非依存）
PYTHONPATH=src python src/pytra-cli.py INPUT.py --target cpp --link-only --output-dir out/linked/

# Stage 2: linked EAST → C++ multi-file（C++ emitter のみ import）
PYTHONPATH=src python src/toolchain/emit/cpp.py out/linked/manifest.json --output-dir out/cpp/
```

補足:
- 全言語で multi-file 出力（`--output-dir`）が正規パスです。compile → link → emit パイプラインを通るため、出力は常にディレクトリ単位です。
- `toolchain/emit/cpp.py` は C++ backend のみを import する独立エントリポイントです。
- `--link-only` は `manifest.json`（マニフェスト）と linked EAST3 JSON を出力します。
- `pytra-cli.py` は compile + link のみを担当し、backend（emit）に依存しません。

### ランタイム構成

`src/runtime/cpp/` は namespace に従ったフォルダ構成です:
- `core/` — 型定義（`py_types.h`）、GC（`gc.h`）、IO（`io.h`）、プロセス管理
- `built_in/` — 組み込み操作（`base_ops.h`, `contains.h`, `list_ops.h` 等）
- `std/` — 標準ライブラリ対応（`math.cpp`, `time.cpp`, `sys.cpp` 等）

runtime モジュールの Python 正本は `src/pytra/` にあり、`.east`（EAST3 JSON）は `src/runtime/east/` に配置されます。

補足:
- Python 側で import できるのは `src/pytra/` にあるモジュールと、ユーザー自作 `.py` モジュールです。
- ユーザーモジュール import は absolute / relative の `from-import` を受理します。
- `pytra` 名前空間は予約済みです。入力ファイルと同じディレクトリに `pytra.py` を置くことはできません。
- ユーザーモジュール import で未解決・循環参照がある場合、`[input_invalid]` で早期エラーにします。
- C++ の速度比較は `-O3 -ffast-math -flto` を使用します。

### オプション

- 添字境界チェック: `--bounds-check-mode {always,debug,off}`（既定: `off`）
- 除算仕様: `--floor-div-mode {native,python}` / `--mod-mode {native,python}`（既定: `native`）
- 整数ビット幅: `--int-width {32,64}`（既定: `64`）
- EAST3 最適化レベル: `--east3-opt-level {0,1,2}`（既定: `1`）

</details>

<details>
<summary>Rust</summary>

```bash
python src/pytra-cli.py --target rs test/fixtures/collections/iterable.py -o work/transpile/rs/iterable.rs
rustc -O work/transpile/rs/iterable.rs -o work/transpile/obj/iterable_rs.out
./work/transpile/obj/iterable_rs.out
```

補足:
- 入力コードで使う Python モジュールに対応する実装は `src/runtime/rs/` に置いてください。

</details>

<details>
<summary>Ruby</summary>

```bash
python src/pytra-cli.py --target ruby test/fixtures/collections/iterable.py -o work/transpile/ruby/iterable.rb
ruby work/transpile/ruby/iterable.rb
```

補足:
- `pytra-cli.py --target ruby` は EAST3 から Ruby native emitter（`src/toolchain/emit/ruby/emitter/ruby_native_emitter.py`）で直接コード生成します。
- 画像出力 API（`png.write_rgb_png` / `save_gif`）は現状 no-op runtime hook で受けるため、まずは出力一致よりも構文/実行導線の回帰監視に使ってください。
- 変換回帰は `python3 tools/check_py2rb_transpile.py` で確認できます。
- parity 導線は `python3 tools/runtime_parity_check.py --case-root sample --targets ruby` で実行できます（toolchain 未導入環境では `toolchain_missing` として記録されます）。`elapsed_sec` など不安定行はデフォルトで比較から除外されます。

</details>

<details>
<summary>Lua</summary>

```bash
python src/pytra-cli.py --target lua test/fixtures/collections/iterable.py -o work/transpile/lua/iterable.lua
lua work/transpile/lua/iterable.lua
```

補足:
- `pytra-cli.py --target lua` は EAST3 から Lua native emitter（`src/toolchain/emit/lua/emitter/lua_native_emitter.py`）で直接コード生成します。
- 画像 API（`png.write_rgb_png` / `save_gif`）は現状 stub/no-op runtime で受けます。
- 変換回帰は `python3 tools/check_py2lua_transpile.py` で確認できます（現状は expected-fail を除外して監視）。
- parity 導線は `python3 tools/runtime_parity_check.py --case-root sample --targets lua 17_monte_carlo_pi` で実行できます（toolchain 未導入環境では `toolchain_missing` として記録されます）。`elapsed_sec` など不安定行はデフォルトで比較から除外されます。
- `sample/lua` は現時点で `02_raytrace_spheres` / `03_julia_set` / `04_orbit_trap_julia` / `17_monte_carlo_pi` を再生成済みです。

</details>

<details>
<summary>PHP</summary>

```bash
python src/pytra-cli.py --target php test/fixtures/collections/iterable.py -o work/transpile/php/iterable.php
php work/transpile/php/iterable.php
```

補足:
- `pytra-cli.py --target php` は EAST3 から PHP native emitter（`src/toolchain/emit/php/emitter/php_native_emitter.py`）で直接コード生成します。
- runtime helper の正本は `src/runtime/php/{generated,native}/` にあり、変換時は必要な helper だけを `work/transpile/php/` 側へ stage します。
- 変換回帰は `python3 tools/check_py2php_transpile.py` で確認できます。
- parity 導線は `python3 tools/runtime_parity_check.py --case-root sample --targets php` で実行できます（toolchain 未導入環境では `toolchain_missing` として記録されます）。

</details>

<details>
<summary>C#</summary>

```bash
python src/pytra-cli.py --target cs test/fixtures/collections/iterable.py -o work/transpile/cs/iterable.cs
python3 tools/check_py2cs_transpile.py
```

補足:
- `pytra-cli.py --target cs` は EAST ベースの変換器です（`.py/.json -> EAST -> C#`）。
- C# 出力品質の段階改善は `docs/ja/todo/index.md` を参照してください。

</details>

<details>
<summary>JavaScript</summary>

```bash
python src/pytra-cli.py --target js test/fixtures/collections/iterable.py -o work/transpile/js/iterable.js
node work/transpile/js/iterable.js
```

補足:
- `browser` / `browser.widgets.dialog` は外部参照として扱われ、`pytra-cli.py --target js` は import 本体を生成しません。

</details>

<details>
<summary>TypeScript</summary>

```bash
python src/pytra-cli.py --target ts test/fixtures/collections/iterable.py -o work/transpile/ts/iterable.ts
npx tsx work/transpile/ts/iterable.ts
```

補足:
- `pytra-cli.py --target ts` は EAST ベースのプレビュー出力です（専用 TSEmitter へ段階移行中）。
- 現在の出力は JavaScript 互換コードをベースにした TypeScript です。

</details>

<details>
<summary>Go</summary>

```bash
python src/pytra-cli.py --target go test/fixtures/collections/iterable.py -o work/transpile/go/iterable.go
go run work/transpile/go/iterable.go
```

補足:
- `pytra-cli.py --target go` は EAST3 から Go native emitter（`src/toolchain/emit/go/emitter/go_native_emitter.py`）で直接コード生成します。
- 既定出力は Go 単体で実行可能です（sidecar JS は既定では生成しません）。
- sidecar 互換モードは撤去済みで、native 経路のみ利用可能です。

</details>

<details>
<summary>Java</summary>

```bash
python src/pytra-cli.py --target java test/fixtures/collections/iterable.py -o work/transpile/java/iterable.java
javac work/transpile/java/iterable.java
java -cp work/transpile/java iterable
```

補足:
- `pytra-cli.py --target java` は EAST3 から Java native emitter（`src/toolchain/emit/java/emitter/java_native_emitter.py`）で直接コード生成します。
- 既定出力は Java 単体で実行可能です（sidecar JS は既定では生成しません）。
- sidecar 互換モードは撤去済みで、native 経路のみ利用可能です。

</details>

<details>
<summary>Swift</summary>

```bash
python src/pytra-cli.py --target swift test/fixtures/collections/iterable.py -o work/transpile/swift/iterable.swift
swiftc work/transpile/swift/iterable.swift -o work/transpile/obj/iterable_swift.out
./work/transpile/obj/iterable_swift.out
```

補足:
- `pytra-cli.py --target swift` は EAST3 から Swift native emitter（`src/toolchain/emit/swift/emitter/swift_native_emitter.py`）で直接コード生成します。
- 既定出力は Swift native 経路で生成され、sidecar JS は既定では生成しません。
- sidecar 互換モードは撤去済みで、native 経路のみ利用可能です。

</details>

<details>
<summary>Kotlin</summary>

```bash
python src/pytra-cli.py --target kotlin test/fixtures/collections/iterable.py -o work/transpile/kotlin/iterable.kt
kotlinc work/transpile/kotlin/iterable.kt -include-runtime -d work/transpile/obj/iterable_kotlin.jar
java -cp work/transpile/obj/iterable_kotlin.jar pytra_iterable
```

補足:
- `pytra-cli.py --target kotlin` は EAST3 から Kotlin native emitter（`src/toolchain/emit/kotlin/emitter/kotlin_native_emitter.py`）で直接コード生成します。
- 既定出力は Kotlin 単体で実行可能です（sidecar JS は既定では生成しません）。
- sidecar 互換モードは撤去済みで、native 経路のみ利用可能です。

</details>

<details>
<summary>Scala3</summary>

```bash
python src/pytra-cli.py --target scala test/fixtures/collections/iterable.py -o work/transpile/scala/iterable.scala
scala run work/transpile/scala/iterable.scala
```

補足:
- `pytra-cli.py --target scala` は EAST3 から Scala3 native emitter（`src/toolchain/emit/scala/emitter/scala_native_emitter.py`）で直接コード生成します。
- 変換回帰は `python3 tools/check_py2scala_transpile.py` で確認できます（正例成功 + 既知負例の失敗カテゴリ一致を同時に検証）。
- parity（sample + fixture 正例マニフェスト）は `python3 tools/check_scala_parity.py` で一括確認できます。
- `sample` のみを先に確認する場合は `python3 tools/check_scala_parity.py --skip-fixture` を使用してください。
- `runtime_parity_check` は `elapsed_sec` など不安定行を既定で比較対象から除外します。

</details>

<details>
<summary>EAST (Python -> EAST -> linked EAST -> C++)</summary>

compile → link → emit パイプラインで `.east` と linked EAST を経由する手順です。

```bash
# 1) Python を .east (EAST3 JSON) にコンパイル
PYTHONPATH=src python src/pytra-cli.py compile sample/py/01_mandelbrot.py -o out/east/01_mandelbrot.east

# 2) .east を linked EAST にリンク（type_id 解決・最適化を含む）
PYTHONPATH=src python src/pytra-cli.py sample/py/01_mandelbrot.py --target cpp --link-only --output-dir out/linked/

# 3) linked EAST から C++ を生成
PYTHONPATH=src python src/toolchain/emit/cpp.py out/linked/manifest.json --output-dir out/cpp/
```

補足:
- `pytra compile` は `.py` → `.east`（EAST3 JSON）を生成します。
- `--link-only` は compile + link + optimize を実行し、linked EAST を出力します。
- `toolchain/emit/cpp.py` は linked EAST → C++ multi-file 出力の独立エントリポイントです。
- 全言語で multi-file 出力（`--output-dir`）が正規パスです。

</details>
