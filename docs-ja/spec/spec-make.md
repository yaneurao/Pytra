# Makefile 生成とワンショット build 仕様

この文書は、C++ 向けの build 導線を `py2cpp.py` 直呼びではなく `pytra` 共通 CLI へ集約する運用仕様を定義する。

## 2026-02-24 照合メモ

- `src/pytra/cli.py` / `tools/gen_makefile_from_manifest.py` / `./pytra` は実装済みで、`--target cpp --build` の導線を `./pytra` 経由で提供します。
- `--multi-file` の `manifest.json` 契約と `tools/build_multi_cpp.py` 導線については仕様として継続しています（`docs-ja/spec/spec-dev.md` / `docs-ja/spec/spec-tools.md`）。
- 本文は実装済み仕様として運用し、将来案として扱う部分は追加タスクとして分離されます。

## 1. 決定事項

- ユーザー入口は `./pytra`（拡張子なしランチャー）とする。
- 実処理本体は `src/pytra/cli.py`（`python -m pytra.cli`）とする。
- `py2cpp.py` はトランスパイル backend として維持し、build オーケストレーション責務は持たせない。
- C++ の build は `manifest.json` 正本 + `Makefile` 生成 + `make` 実行で行う。
- `PYTHONPATH` 手動設定は不要にする（`./pytra` が内部で設定）。

## 2. 目的

- 手入力コマンドを短縮し、変換からビルドまでを 1 コマンド化する。
- 既存の multi-file 出力と `manifest.json` を活かして、再現可能な build 手順を提供する。
- 将来の多言語統合 CLI（`--target` 切替）へ拡張可能な入口を確立する。

## 3. 非目標

- いきなり全言語で build 実行まで実装すること（まずは `--target cpp` のみ）。
- IDE 固有プロジェクト（Visual Studio/Xcode）の生成。
- `manifest.json` を介さない自動推測 build。

## 4. エントリポイント仕様

### 4.1 `./pytra` ランチャー

リポジトリルートに `pytra`（拡張子なし実行ファイル）を配置し、次を行う。

1. `ROOT/src` を `PYTHONPATH` へ追加。
2. `python3 -m pytra.cli "$@"` を実行。

意図:

- `PYTHONPATH=src ...` の毎回入力を不要にする。
- 入力プロジェクト側の `pytra.py` と名前衝突しない実行形を提供する。

### 4.2 実体 CLI

- 実体は `src/pytra/cli.py`。
- 直接実行形は `python3 -m pytra.cli ...`。

## 5. 共通 CLI 仕様（v1）

### 5.1 基本形

```bash
./pytra INPUT.py --target cpp [OPTIONS]
```

### 5.2 v1 で必須/対応する引数

- `INPUT.py`
- `--target cpp`
- `--output-dir DIR`（既定: `out`）
- `--build`（指定時のみ build 実行）

### 5.3 `--build` 時の C++ build オプション

- `--compiler CXX`（既定: `g++`）
- `--std STD`（既定: `c++20`）
- `--opt FLAG`（既定: `-O2`）
- `--exe NAME`（既定: `app.out`）
- `--run`（任意: build 成功後に実行）

補足:

- この仕様での `--opt` は「C++ コンパイルフラグ」を指す。
- 生成コード側の最適化レベル（`py2cpp` の `-O0..-O3`）は別引数 `--codegen-opt {0,1,2,3}` として分離してよい（未指定時は既定値を使用）。

### 5.4 制約

- `--build` は `--target cpp` でのみ有効。
- `--compiler/--std/--opt/--exe/--run` は `--build` 指定時のみ有効。
- `--target cpp` 以外で `--build` が指定された場合はエラー終了する。

## 6. C++ build フロー

`./pytra ... --target cpp --build` の処理順は次のとおり。

1. `py2cpp.py --multi-file --output-dir <DIR>` を実行し `manifest.json` を生成する。
2. `tools/gen_makefile_from_manifest.py` で `Makefile` を生成する。
3. `make -f <Makefile>` を実行してバイナリを生成する。
4. `--run` 指定時のみ `make -f <Makefile> run` を実行する。

## 7. `manifest.json` 入力仕様

`manifest.json` は少なくとも次を満たす。

- `modules` は配列である。
- 各要素はオブジェクトであり、`source` は空でない文字列である。
- `include_dir` は文字列である（未指定時は `manifest` 同階層の `include` を既定値として扱ってよい）。

例:

```json
{
  "entry": "path/to/main.py",
  "include_dir": "out/include",
  "src_dir": "out/src",
  "modules": [
    {
      "module": "path/to/main.py",
      "label": "main",
      "header": "out/include/main.h",
      "source": "out/src/main.cpp",
      "is_entry": true
    }
  ]
}
```

## 8. Makefile 生成仕様

`tools/gen_makefile_from_manifest.py` を使用し、次を受け付ける。

- 位置引数
  - `manifest`
- オプション
  - `-o`, `--output`
  - `--exe`
  - `--compiler`
  - `--std`
  - `--opt`

生成する `Makefile` には最低限次を含める。

- 変数: `CXX`, `CXXFLAGS`, `INCLUDES`, `SRCS`, `OBJS`, `TARGET`
- ターゲット: `all`, `$(TARGET)`, `%.o: %.cpp`, `run`, `clean`

## 9. エラー契約

次の場合は非ゼロ終了にする。

- `manifest` が存在しない。
- JSON パースに失敗する。
- `modules` が配列でない。
- 有効な `source` が 1 件もない。
- `--build` なしで `--compiler/--std/--opt/--exe/--run` が指定された。
- `--target cpp` 以外で `--build` が指定された。
- `make` が見つからない。

## 10. 受け入れ基準

- `./pytra sample/py/01_mandelbrot.py --target cpp --output-dir out/mandelbrot` で multi-file 出力が生成される。
- `./pytra sample/py/01_mandelbrot.py --target cpp --build --output-dir out/mandelbrot` で、変換・Makefile 生成・ビルドが連続実行される。
- `./pytra sample/py/01_mandelbrot.py --target cpp --build --compiler g++ --std c++20 --opt -O3 --exe mandelbrot.out` で指定値が `Makefile` と build に反映される。
- `./pytra sample/py/01_mandelbrot.py --target rs --build` は仕様どおりエラー終了する。
- `make -f out/mandelbrot/Makefile` の 2 回目実行で差分なしビルド（再リンク/再コンパイル最小化）になる。

## 11. 段階導入

1. Phase 1: `tools/gen_makefile_from_manifest.py` を追加する。
2. Phase 2: `src/pytra/cli.py` を追加し、`--target cpp --build` を実装する。
3. Phase 3: ルートランチャー `./pytra` を追加し、`PYTHONPATH` 設定を内包する。
4. Phase 4: `--run`、`--codegen-opt`、必要なら `--jobs` を追加する。

## 12. 実使用例

### 12.1 変換のみ

```bash
./pytra sample/py/01_mandelbrot.py --target cpp --output-dir out/mandelbrot
```

### 12.2 ワンショット build

```bash
./pytra sample/py/01_mandelbrot.py \
  --target cpp \
  --build \
  --output-dir out/mandelbrot
```

### 12.3 ワンショット build（コンパイラ設定を明示）

```bash
./pytra sample/py/01_mandelbrot.py \
  --target cpp \
  --build \
  --output-dir out/mandelbrot \
  --compiler g++ \
  --std c++20 \
  --opt -O3 \
  --exe mandelbrot.out
```

### 12.4 build + run

```bash
./pytra sample/py/01_mandelbrot.py \
  --target cpp \
  --build \
  --run \
  --output-dir out/mandelbrot
```

## 13. 補足

- `out/` はローカル生成物ディレクトリとして運用し、Git 管理しません。
- `py2cpp.py` は backend として維持し、共通 CLI から呼び出す。
- 将来は `pip install -e .` + console script 化を行うと `./pytra` なしでも `pytra ...` 実行に移行できる。
