# 仕様書

## 1. 目的

PyCs は、型注釈付き Python コードを次の言語へ変換するトランスパイラ群です。

- Python -> C# (`src/pycs_transpiler.py`)
- Python -> C++ (`src/pycpp_transpiler.py`)

本仕様書は、現時点の実装に基づく対応範囲・テスト方法・運用上の注意点を定義します。

## 2. リポジトリ構成

- `src/`
  - `pycs_transpiler.py`: Python -> C# 変換器
  - `pycpp_transpiler.py`: Python -> C++ 変換器
  - `cpp_module/`: C++ 側ランタイム補助モジュール
- `test/`
  - `py/`: 入力 Python サンプル
  - `cs/`: C# 期待結果
  - `cpp/`: C++ 期待結果
  - `cpp2/`: セルフホスティング検証時の出力先（`.gitignore` 対象）
  - `obj/`: C++ コンパイル生成物（`.gitignore` 対象）
- `docs/`
  - `spec.md`: 本仕様
  - `gc.md`: 参照カウント GC の仕様

## 3. Python 入力仕様

- 入力 Python は、基本的に型注釈付きコードを前提とします。
- `class` は単一継承をサポートします。
- `self.xxx` に対する `__init__` 内代入はインスタンスメンバーとして扱います。
- class 本体で宣言されたメンバーは class member（C# では `static`、C++ では `inline static`）として扱います。
- `@dataclass` を付けた class は dataclass として扱い、フィールドとコンストラクタを生成します。
- `import` / `from ... import ...` をサポートします。

## 4. C# 変換仕様（`pycs_transpiler.py`）

- Python AST を解析し、`Program` クラスを持つ C# コードを生成します。
- `import` / `from ... import ...` は `using` へ変換します。
- 主な型対応:
  - `int -> int`
  - `float -> double`
  - `str -> string`
  - `bool -> bool`
  - `None -> void`（戻り値注釈時）
- class member は `public static` に変換します。
- `__init__` で初期化される `self` 属性はインスタンスメンバーとして生成します。

## 5. C++ 変換仕様（`pycpp_transpiler.py`）

- Python AST を解析し、単一 `.cpp`（必要 include 付き）を生成します。
- 生成コードは `src/cpp_module/` のランタイム補助実装を利用します。
- `py_to_string` などの補助関数は生成 `.cpp` に直書きせず、`cpp_module/py_runtime_modules.h` 側を利用します。
- class は `pycs::gc::PyObj` 継承の C++ class として生成します（例外クラスを除く）。
- class member は `inline static` メンバーとして生成します。
- `__init__` 内 `self.xxx` 代入はインスタンスメンバーとして生成します。
- `@dataclass` はフィールド定義とコンストラクタ生成を行います。
- `raise` / `try` / `except` をサポートし、例外は `std::runtime_error` 等を利用して表現します。
- `while` 文をサポートします。

### 5.1 import と `cpp_module` 対応

`pycpp_transpiler.py` は import 文に応じて include を生成します。主な対応は次の通りです。

- `import ast` -> `#include "cpp_module/ast.h"`
- `import pathlib` -> `#include "cpp_module/pathlib.h"`
- `import time` / `from time import ...` -> `#include "cpp_module/time.h"`
- `from dataclasses import dataclass` -> `#include "cpp_module/dataclasses.h"`
- GC は常時 `#include "cpp_module/gc.h"` を利用

補助モジュール実装:

- `src/cpp_module/ast.h`, `src/cpp_module/ast.cpp`
- `src/cpp_module/pathlib.h`, `src/cpp_module/pathlib.cpp`
- `src/cpp_module/time.h`, `src/cpp_module/time.cpp`
- `src/cpp_module/dataclasses.h`, `src/cpp_module/dataclasses.cpp`
- `src/cpp_module/gc.h`, `src/cpp_module/gc.cpp`
- `src/cpp_module/sys.h`, `src/cpp_module/sys.cpp`
- `src/cpp_module/py_runtime_modules.h`

注意:

- `pycpp_transpiler_runtime.h` は廃止済みであり、使用しません。
- `import ast` を含むコードの C++ 変換では、`cpp_module/ast` 実装を前提に動作します。
- 制約: Python 側で `import` / `from ... import ...` するモジュールは、原則として `src/cpp_module/` に対応する `*.h` / `*.cpp` 実装を用意する必要があります。
- 制約: 生成 C++ 側で使う補助関数（`py_to_string`, `py_in`, `py_print`, `py_write` など）は `cpp_module/py_runtime_modules.h` に集約し、生成 `.cpp` へ重複定義しません。

### 5.2 関数引数の受け渡し方針

- コピーコストが高い型（`string`, `vector<...>`, `unordered_map<...>`, `unordered_set<...>`, `tuple<...>`）は、関数内で直接変更されない場合に `const T&` で受けます。
- 引数の直接変更が検出された場合は値渡し（または非 const）を維持します。
- 直接変更判定は、代入・拡張代入・`del`・破壊的メソッド呼び出し（`append`, `extend`, `insert`, `pop` など）を対象に行います。

## 6. テストケース方針

- 入力 Python は `test/py/` に配置します。
- C# 期待結果は `test/cs/` に配置します。
- C++ 期待結果は `test/cpp/` に配置します。
- ケース命名は `caseXX_*` 形式を基本とし、特別ケースとして以下を含みます。
  - `case99_dataclass`
  - `case100_class_instance`

## 6.1 サンプルプログラム方針

- 実用サンプルは `sample/py/` に配置します。
- C++ 変換結果は `sample/cpp/` に配置します。
- バイナリや中間生成物は `sample/obj/`, `sample/out/` を利用します。
- `sample/py/01_mandelbrot.py` はマンデルブロ集合画像を生成し、Python 実行時と C++ 実行時の画像一致（ハッシュ一致）を確認可能なサンプルです。

## 7. ユニットテスト実行方法

プロジェクトルート (`PyCs/`) で実行します。

```bash
python -m unittest discover -s test -p "test_*.py" -v
```

想定内容:

- `test/test_transpile_cases.py`
  - `test/py/case*.py` (100件) を C# へ変換し、`test/cs/` と比較
- `test/test_self_transpile.py`
  - `src/pycs_transpiler.py` 自身の C# 変換が完走することを確認

## 8. C++ 変換結果の検証手順

必要に応じて次を実行します。

1. Python 版トランスパイラで `test/py` を `test/cpp` へ変換
2. 生成 C++ を `test/obj/` にコンパイル
3. 実行結果を Python 実行結果と比較
4. セルフホスティング検証時は、自己変換したトランスパイラ実行ファイルで `test/py` -> `test/cpp2` を生成
5. `test/cpp` と `test/cpp2` の一致を確認

## 9. 注意点

- 未対応構文はトランスパイル時に `TranspileError` で失敗します。
- エラー発生時、CLI エントリポイント（例: `pycs.py`）は `error: ...` を標準エラーへ出力し、終了コード `1` を返します。
- `test/obj/` と `test/cpp2/` は検証用生成物のため Git 管理外です。
