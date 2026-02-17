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

## 4. テストコードとの関係

`test/` は小規模な機能確認ケース、`sample/` は実用寄り・負荷高めケースという役割分担です。

- [test/py](../test/py): 変換元テストコード
- [test/cpp](../test/cpp): C++ 変換結果
- [test/cs](../test/cs): C# 変換結果
- [test/rs](../test/rs): Rust 変換結果
- [test/js](../test/js): JavaScript 変換結果
- [test/ts](../test/ts): TypeScript 変換結果
- [test/go](../test/go): Go 変換結果
- [test/java](../test/java): Java 変換結果
- [test/swift](../test/swift): Swift 変換結果
- [test/kotlin](../test/kotlin): Kotlin 変換結果
