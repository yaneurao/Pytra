# 仕様書

## 1. 目的

Pytra は、型注釈付き Python コードを次の言語へ変換するトランスパイラ群です。

- Python -> C# (`src/py2cs.py`)
- Python -> C++ (`src/py2cpp.py`)
- Python -> Rust (`src/py2rs.py`)
- Python -> JavaScript (`src/py2js.py`)
- Python -> TypeScript (`src/py2ts.py`)

本仕様書は、現時点の実装に基づく対応範囲・テスト方法・運用上の注意点を定義します。

## 2. リポジトリ構成

- `src/`
  - `py2cs.py`: Python -> C# 変換器
  - `py2cpp.py`: Python -> C++ 変換器
  - `py2rs.py`: Python -> Rust 変換器
  - `py2js.py`: Python -> JavaScript 変換器
  - `py2ts.py`: Python -> TypeScript 変換器
  - `common/`: 複数言語トランスパイラで共有する基底実装・共通ユーティリティ
    - `base_transpiler.py`: `TranspileError` と共通基底クラス
    - `transpile_shared.py`: AST 解析補助（スコープ、main guard 判定など）
    - `node_embedded_python_transpiler.py`: JS/TS 向け埋め込み Python 実行コード生成
  - `cs_type_mappings.py`: C# 専用の型マップ
  - `cpp_type_mappings.py`: C++ 専用の型マップ
  - `cpp_module/`: C++ 側ランタイム補助モジュール
  - `cs_module/`: C# 側ランタイム補助モジュール
  - `py_module/`: Python 側の自作ライブラリ配置先
- `test/`
  - `py/`: 入力 Python サンプル
  - `cs/`: C# 期待結果
  - `cpp/`: C++ 期待結果
  - `rs/`: Rust 変換結果
  - `js/`: JavaScript 変換結果
  - `ts/`: TypeScript 変換結果
  - `cpp2/`: セルフホスティング検証時の出力先（`.gitignore` 対象）
  - `obj/`: C++ コンパイル生成物（`.gitignore` 対象）
- `docs/`
  - `spec.md`: 本仕様
  - `how-to-use.md`: 使い方（CLI / コンパイル手順）
  - `time-comparison.md`: 実行時間比較の測定条件
  - `gc.md`: 参照カウント GC の仕様
- `sample/`
  - `py/`: 実用寄り Python サンプル（入力）
  - `cpp/`: `sample/py` を C++ へ変換した出力
  - `cs/`: `sample/py` を C# へ変換した出力
  - `rs/`: `sample/py` を Rust へ変換した出力
  - `js/`: `sample/py` を JavaScript へ変換した出力
  - `ts/`: `sample/py` を TypeScript へ変換した出力
  - `out/`: サンプル実行時の生成物（PNG / GIF）
  - `obj/`: サンプル実行用のコンパイル生成物

## 3. Python 入力仕様

- 入力 Python は、基本的に型注釈付きコードを前提とします。
- `class` は単一継承をサポートします。
- `self.xxx` に対する `__init__` 内代入はインスタンスメンバーとして扱います。
- class 本体で宣言されたメンバーは class member（C# では `static`、C++ では `inline static`）として扱います。
- `@dataclass` を付けた class は dataclass として扱い、フィールドとコンストラクタを生成します。
- `import` / `from ... import ...` をサポートします。

## 4. C# 変換仕様（`py2cs.py`）

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

## 5. C++ 変換仕様（`py2cpp.py`）

- Python AST を解析し、単一 `.cpp`（必要 include 付き）を生成します。
- 生成コードは `src/cpp_module/` のランタイム補助実装を利用します。
- `py_to_string` などの補助関数は生成 `.cpp` に直書きせず、`cpp_module/py_runtime.h` 側を利用します。
- class は `pycs::gc::PyObj` 継承の C++ class として生成します（例外クラスを除く）。
- class member は `inline static` メンバーとして生成します。
- `__init__` 内 `self.xxx` 代入はインスタンスメンバーとして生成します。
- `@dataclass` はフィールド定義とコンストラクタ生成を行います。
- `raise` / `try` / `except` をサポートし、例外は `std::runtime_error` 等を利用して表現します。
- `while` 文をサポートします。

### 5.1 import と `cpp_module` 対応

`py2cpp.py` は import 文に応じて include を生成します。主な対応は次の通りです。

- `import ast` -> `#include "cpp_module/ast.h"`
- `import math` -> `#include "cpp_module/math.h"`
- `import pathlib` -> `#include "cpp_module/pathlib.h"`
- `import time` / `from time import ...` -> `#include "cpp_module/time.h"`
- `from dataclasses import dataclass` -> `#include "cpp_module/dataclasses.h"`
- `from py_module import png_helper` / `import png_helper` -> `#include "cpp_module/png.h"`
- GC は常時 `#include "cpp_module/gc.h"` を利用

補助モジュール実装:

- `src/cpp_module/ast.h`, `src/cpp_module/ast.cpp`
- `src/cpp_module/math.h`, `src/cpp_module/math.cpp`
- `src/cpp_module/pathlib.h`, `src/cpp_module/pathlib.cpp`
- `src/cpp_module/time.h`, `src/cpp_module/time.cpp`
- `src/cpp_module/dataclasses.h`, `src/cpp_module/dataclasses.cpp`
- `src/cpp_module/gc.h`, `src/cpp_module/gc.cpp`
- `src/cpp_module/sys.h`, `src/cpp_module/sys.cpp`
- `src/cpp_module/py_runtime.h`

注意:

- `import ast` を含むコードの C++ 変換では、`cpp_module/ast` 実装を前提に動作します。
- 制約: Python 側で `import` / `from ... import ...` するモジュールは、原則として `src/cpp_module/` に対応する `*.h` / `*.cpp` 実装を用意する必要があります。
- 制約: 生成 C++ 側で使う補助関数（`py_to_string`, `py_in`, `py_print`, `py_write` など）は `cpp_module/py_runtime.h` に集約し、生成 `.cpp` へ重複定義しません。

### 5.2 関数引数の受け渡し方針

- コピーコストが高い型（`string`, `vector<...>`, `unordered_map<...>`, `unordered_set<...>`, `tuple<...>`）は、関数内で直接変更されない場合に `const T&` で受けます。
- 引数の直接変更が検出された場合は値渡し（または非 const）を維持します。
- 直接変更判定は、代入・拡張代入・`del`・破壊的メソッド呼び出し（`append`, `extend`, `insert`, `pop` など）を対象に行います。

## 6. テストケース方針

- 入力 Python は `test/py/` に配置します。
- C# 期待結果は `test/cs/` に配置します。
- C++ 期待結果は `test/cpp/` に配置します。
- Rust 変換結果は `test/rs/` に配置します。
- JavaScript 変換結果は `test/js/` に配置します。
- TypeScript 変換結果は `test/ts/` に配置します。
- 変換器都合で `test/py/` の入力ケースを変更してはなりません。変換失敗時は、まずトランスパイラ実装（`src/py2cs.py`, `src/py2cpp.py`）側を修正します。
- ケース命名は `caseXX_*` 形式を基本とします。

## 6.1 サンプルプログラム方針

- 実用サンプルは `sample/py/` に配置します。
- C++ 変換結果は `sample/cpp/` に配置します。
- C# 変換結果は `sample/cs/` に配置します。
- Rust 変換結果は `sample/rs/` に配置します。
- バイナリや中間生成物は `sample/obj/`, `sample/out/` を利用します。
- `sample/obj/` と `sample/out/` は生成物ディレクトリであり、Git 管理外（`.gitignore`）を前提とします。
- Python から import する自作ライブラリは `src/py_module/` に配置します（`sample/py/` には置きません）。
- 例: `from py_module import png_helper`, `from py_module.gif_helper import save_gif`
- 画像出力サンプル（`sample/py/01`, `02`, `03`）は **PNG 形式**で出力します（PPMは使用しません）。
- GIF サンプルは `sample/out/*.gif` に出力します。
- Python 側の画像保存は `py_module.png_helper.write_rgb_png(...)` を使用し、C++ 側は `src/cpp_module/png.h/.cpp` を利用します。
- `sample/py` の連番（`01_...`, `02_...`）は README の実行時間比較表と対応づけるため、原則として欠番なしで管理します。
- `sample/py/01_mandelbrot.py` はマンデルブロ集合画像を生成し、Python 実行時と C++ 実行時の画像一致（ハッシュ一致）を確認可能なサンプルです。
- 画像一致検証は、同名出力を言語別に退避してハッシュ（例: `sha256sum`）比較で行います。

## 7. ユニットテスト実行方法

プロジェクトルート (`Pytra/`) で実行します。

```bash
python -m unittest discover -s test -p "test_*.py" -v
```

想定内容:

- `test/test_transpile_cases.py`
  - `test/py/case*.py` (100件) を C# へ変換し、`test/cs/` と比較
- `test/test_self_transpile.py`
  - `src/py2cs.py` 自身の C# 変換が完走することを確認

## 8. C++ 変換結果の検証手順

必要に応じて次を実行します。

1. Python 版トランスパイラで `test/py` を `test/cpp` へ変換
2. 生成 C++ を `test/obj/` にコンパイル
3. 実行結果を Python 実行結果と比較
4. セルフホスティング検証時は、自己変換したトランスパイラ実行ファイルで `test/py` -> `test/cpp2` を生成
5. `test/cpp` と `test/cpp2` の一致を確認

## 9. 注意点

- コンパイル最適化ルール:
  - 実行速度比較・ベンチマーク用途の C++ バイナリは `-O3 -ffast-math -flto` でコンパイルします。
  - `-O2` や `-O3` 単体は、原則として実行時間比較の正式計測には使用しません。
  - 言語間比較の公平性のため、README や計測手順に記載する C++ 実行時間は `-O3 -ffast-math -flto` ビルド結果を使用します。
- 共通化ルール:
  - `src/common/` には、言語非依存で再利用される処理のみを配置します（例: `TranspileError`, 共通基底クラス、AST 補助）。
  - 言語固有の仕様（型マッピング、キーワード予約語、ランタイム名など）は `src/common/` に置きません。
  - 例: 型マップは `src/cpp_type_mappings.py` / `src/cs_type_mappings.py` のように言語別モジュールへ配置します。
  - 新規ターゲット言語（JavaScript / Rust など）追加時は、まず `src/common/` の共通実装を利用し、差分のみ言語別実装へ追加します。
- コメント記述ルール:
  - class 名・関数名・メンバー変数名には、必ず用途が分かる日本語コメント（説明）を付与します。
  - 新規追加時だけでなく、既存コード改修時にも未記載があれば同時に補完します。
- Git 運用ルール:
  - 本プロジェクトでは、作業内容が適切にまとまった時点で、ユーザーの都度許可なしにコミットしてよいものとします。
  - ただし、履歴の可読性を保つため、コミットは論理単位で分割し、コミットメッセージは変更意図が分かる内容にします。
- ドキュメント同期ルール:
  - `README.md` はユーザー向けの一次情報として扱います。機能追加・仕様変更・手順変更時は、必要に応じて `README.md` を更新します。
  - `README.md` からリンクされるドキュメント（`docs/how-to-use.md`, `docs/time-comparison.md`, `docs/spec.md` など）も整合性を確認し、必要なら同時に更新します。
  - 実装とドキュメントの内容が不一致にならないことを、変更完了条件に含めます。
- 現在の `py2rs.py` は最小実装です。生成 Rust は Python ソースを埋め込み、実行時に Python インタプリタ（`python3` 優先、`python` フォールバック）を呼び出します。
- 現在の `py2js.py` / `py2ts.py` は埋め込み Python 実行モードです。生成 JS/TS は Node.js 上で Python ソースを実行します（`python3` 優先、`python` フォールバック）。
- 未対応構文はトランスパイル時に `TranspileError` で失敗します。
- エラー発生時、CLI エントリポイント（`src/py2cs.py`）は `error: ...` を標準エラーへ出力し、終了コード `1` を返します。
- `test/obj/` と `test/cpp2/` は検証用生成物のため Git 管理外です。
- `sample/obj/` と `sample/out/` も同様に検証・出力用生成物のため Git 管理外です。
- `src/py_module/` のライブラリを利用してサンプルを直接実行する場合は、必要に応じて `PYTHONPATH=src` を付与して実行します。
