# サンプルコードについて

## 1. 目的

`sample/` は、実用寄りの Python サンプルを各言語へトランスパイルし、実行結果と実行時間を比較するためのディレクトリです。

## 2. ディレクトリ構成

- [sample/py](../sample/py): 変換元 Python サンプル（現在 `01`〜`16`）
- [sample/cpp](../sample/cpp): C++ 変換結果
- [sample/cs](../sample/cs): C# 変換結果
- [sample/rs](../sample/rs): Rust 変換結果
- [sample/js](../sample/js): JavaScript 変換結果
- [sample/ts](../sample/ts): TypeScript 変換結果
- [sample/go](../sample/go): Go 変換結果
- [sample/java](../sample/java): Java 変換結果
- [sample/swift](../sample/swift): Swift 変換結果
- [sample/kotlin](../sample/kotlin): Kotlin 変換結果
- `sample/obj`: 各言語のビルド生成物（Git管理外）
- `sample/out`: 実行時の出力画像（PNG/GIF、Git管理外）

## 3. 計測条件（README 表の前提）

- Python: `PYTHONPATH=src python3 sample/py/<file>.py`
- C++: `g++ -std=c++20 -O3 -ffast-math -flto -I src ...`
- C#: `mcs ...` + `mono ...`
- Rust: `rustc -O ...`
- JavaScript: `node sample/js/<file>.js`
- TypeScript: `tsc ...` でコンパイル後 `node ...`
- Go: `go run` または `go build` 後に実行
- Java: `javac` + `java`
- Swift: `swiftc` でビルドした実行ファイル
- Kotlin: `kotlinc -include-runtime` でビルドした `jar`

注:
- `py2swift.py` / `py2kotlin.py` は現在 Node バックエンド方式で、実行時に `node` を使用します（`python3` は呼び出しません）。

## 4. 実行時の注意

- `sample/py/` を Python のまま実行する場合は、`pylib` 解決のため `PYTHONPATH=src` を付けます。

```bash
PYTHONPATH=src python3 sample/py/01_mandelbrot.py
```

## 5. テストコードとの関係

`test/` は小規模な機能確認ケース、`sample/` は実用寄り・負荷高めケースという役割分担です。

- [test/fixtures](../test/fixtures): 変換元テストコード
- [test/unit](../test/unit): ユニットテスト
- `test/transpile/`: 変換生成物の作業ディレクトリ（Git管理外）
  - GitHub上では閲覧できません。必要な場合はローカルでトランスパイル実行して生成してください。

## 6. 画像一致に関する補足

- 画像サンプルの一致判定は、Python 実行結果と C++ 実行結果の **出力ファイルバイト列完全一致** を基準とします。
- PNG/GIF を区別せず、バイト列不一致は不一致（要修正）として扱います。

画像一致検証を自動実行する場合:

```bash
python3 tools/verify_sample_outputs.py --compile-flags="-O2"
```

- `stdout` 差分と、画像ファイルのバイト列差分をまとめて確認できます。
- `sample/12_sort_visualizer` と `sample/16_glass_sculpture_chaos` では、GIF フレームブロック（遅延値 + LZW 圧縮データ）が一致することを確認済みです。

実行時間などの `stdout` 差分を無視して、画像一致のみ確認したい場合:

```bash
python3 tools/verify_sample_outputs.py --ignore-stdout --compile-flags="-O2"
```
