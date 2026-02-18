# 利用仕様（Pytra）

このドキュメントは、Pytra の利用方法と入力制約をまとめた仕様です。

## 1. 目的

Pytra は、型注釈付き Python コードを次の言語へ変換するトランスパイラ群です。

- Python -> C# (`src/py2cs.py`)
- Python -> C++ (`src/py2cpp.py`)
- Python -> Rust (`src/py2rs.py`)
- Python -> JavaScript (`src/py2js.py`)
- Python -> TypeScript (`src/py2ts.py`)
- Python -> Go (`src/py2go.py`)
- Python -> Java (`src/py2java.py`)
- Python -> Swift (`src/py2swift.py`)
- Python -> Kotlin (`src/py2kotlin.py`)

## 2. Python 入力仕様

- 入力 Python は、基本的に型注釈付きコードを前提とします。
- 型注釈は次の条件では省略できます（暗黙の型推論）。
  - 右辺がリテラルで型が一意な代入（例: `x = 1`, `y = 1.5`, `s = "abc"`）。
  - 右辺の変数型が既知な単純代入（例: `y = x` で `x` の型が確定済み）。
- `class` は単一継承をサポートします。
- `self.xxx` に対する `__init__` 内代入はインスタンスメンバーとして扱います。
- class 本体で宣言されたメンバーは class member（C# では `static`、C++ では `inline static`）として扱います。
- `@dataclass` を付けた class は dataclass として扱い、フィールドとコンストラクタを生成します。
- `import` / `from ... import ...` をサポートします。

## 3. テストケース方針

- 入力 Python は `test/fixtures/` 配下に配置します（カテゴリ別サブディレクトリ）。
- 言語別の変換結果は `test/transpile/cs/`, `test/transpile/cpp/`, `test/transpile/rs/`, `test/transpile/js/`, `test/transpile/ts/`, `test/transpile/go/`, `test/transpile/java/`, `test/transpile/swift/`, `test/transpile/kotlin/` に配置します。
- 変換器都合で `test/fixtures/` の入力ケースを変更してはなりません。変換失敗時は、トランスパイラ実装側を修正します。
- ケース命名は説明的な `snake_case`（例: `dict_get_items.py`）を基本とします。

`test/` の標準構成は次のとおりです。

```text
test/
  unit/         # unittest のテストコード（test_*.py）
  integration/  # 統合テストコード
  fixtures/     # 変換元 Python ケース（*.py, カテゴリ別）
    core/
    control/
    strings/
    collections/
    oop/
    typing/
    stdlib/
    signature/
  transpile/    # 変換生成物と実行生成物（Git管理外）
```

- `test/transpile/` は使い捨ての生成物置き場です。必要に応じて全削除して再生成します。

## 4. サンプルプログラム方針

- 実用サンプルは `sample/py/` に配置します。
- 言語別の変換結果は `sample/cpp/`, `sample/rs/`, `sample/cs/`, `sample/js/`, `sample/ts/`, `sample/go/`, `sample/java/`, `sample/swift/`, `sample/kotlin/` に配置します。
- バイナリや中間生成物は `sample/obj/`, `sample/out/` を利用します（Git 管理外）。
- Python から import する自作ライブラリは `src/py_module/` に配置します。
- 画像出力サンプル（`sample/py/01`, `02`, `03`）は PNG 形式で出力します。
- C++ 実行バイナリは起動オプション `--pytra-image-format=png|ppm` を受け付けます。
  - `ppm` 指定時、`png_helper.write_rgb_png(...)` は PPM(P6) で出力され、出力拡張子は `.ppm` に切り替わります。
- GIF サンプルは `sample/out/*.gif` に出力します。

## 5. ユニットテスト実行方法

プロジェクトルート (`Pytra/`) で次を実行します。

```bash
python -m unittest discover -s test/unit -p "test_*.py" -v
```

`test/fixtures/**/*.py` を一括実行して末尾出力 `True` を検証する専用テスト:

```bash
python -m unittest discover -s test/unit -p "test_fixtures_truth.py" -v
```

## 6. 利用時の注意

- C++ の速度比較は `-O3 -ffast-math -flto` を使用します。
- 未対応構文はトランスパイル時に `TranspileError` で失敗します。
- `test/transpile/obj/`, `test/transpile/cpp2/`, `sample/obj/`, `sample/out/` は生成物ディレクトリです。
- `src/py_module/` を使う Python サンプルは、必要に応じて `PYTHONPATH=src` を付与して実行します。

## 7. 関連ドキュメント

- 使い方: `docs/how-to-use.md`
- サンプルコード: `docs/sample-code.md`
- 実装状況詳細: `docs/pytra-readme.md`
