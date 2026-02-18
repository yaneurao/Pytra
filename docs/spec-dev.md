# 実装仕様（Pytra）

このドキュメントは、トランスパイラの実装方針・構成・変換仕様をまとめた仕様です。

## 1. リポジトリ構成

- `src/`
  - `py2cs.py`, `py2cpp.py`, `py2rs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2swift.py`, `py2kotlin.py`
  - `src/` 直下にはトランスパイラ本体（`py2*.py`）のみを配置する
  - `common/`: 複数言語で共有する基底実装・共通ユーティリティ
  - `cpp_module/`, `cs_module/`, `rs_module/`, `js_module/`, `ts_module/`, `go_module/`, `java_module/`, `swift_module/`, `kotlin_module/`: 各ターゲット言語向けランタイム補助
  - `py_module/`: Python 側の自作ライブラリ
- `test/`: `py`（入力）と各ターゲット言語の変換結果
- `sample/`: 実用サンプル入力と各言語変換結果
- `docs/`: 仕様・使い方・実装状況

## 2. C# 変換仕様（`py2cs.py`）

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

## 3. C++ 変換仕様（`py2cpp.py`）

- Python AST を解析し、単一 `.cpp`（必要 include 付き）を生成します。
- 生成コードは `src/cpp_module/` のランタイム補助実装を利用します。
- 補助関数は生成 `.cpp` に直書きせず、`cpp_module/py_runtime.h` 側を利用します。
- class は `pytra::gc::PyObj` 継承の C++ class として生成します（例外クラスを除く）。
- class member は `inline static` として生成します。
- `@dataclass` はフィールド定義とコンストラクタ生成を行います。
- `raise` / `try` / `except` / `while` をサポートします。
- `%`（剰余）は C++ の `%` をそのまま生成します。
- `%` の負数オペランドは現行仕様の対象外です（入力は非負整数を前提とします）。
- list/str の負数添字（例: `a[-1]`）は `--negative-index-mode` で制御します。
  - デフォルトは `const_only`（定数の負数添字のみ Python 互換処理を有効化）。
  - `always`: すべての添字アクセスで Python 互換の負数添字処理を有効化。
  - `off`: Python 互換の負数添字処理を行わず、通常の `[]` を生成。
- PNG 画像の一致判定は、ファイルバイト列ではなく raw scanline（復号後画素）を優先します。
  - raw scanline が一致し、IDAT のみ差がある場合は「圧縮差」として許容します。
  - 現時点では IDAT 圧縮バイト列の完全一致は目標にしません。

### 3.1 import と `cpp_module` 対応

`py2cpp.py` は import 文に応じて include を生成します。

- `import math` -> `#include "cpp_module/math.h"`
- `import pathlib` -> `#include "cpp_module/pathlib.h"`
- `import time` / `from time import ...` -> `#include "cpp_module/time.h"`
- `from dataclasses import dataclass` -> `#include "cpp_module/dataclasses.h"`
- `from py_module import png_helper` / `import png_helper` -> `#include "cpp_module/png.h"`
- GC は常時 `#include "cpp_module/gc.h"` を利用

主な補助モジュール実装:

- `src/cpp_module/math.h`, `src/cpp_module/math.cpp`
- `src/cpp_module/pathlib.h`, `src/cpp_module/pathlib.cpp`
- `src/cpp_module/time.h`, `src/cpp_module/time.cpp`
- `src/cpp_module/dataclasses.h`, `src/cpp_module/dataclasses.cpp`
- `src/cpp_module/gc.h`, `src/cpp_module/gc.cpp`
- `src/cpp_module/sys.h`, `src/cpp_module/sys.cpp`
- `src/cpp_module/py_runtime.h`

制約:

- Python 側で import するモジュールは、原則として各ターゲット言語ランタイムにも対応実装を用意する必要があります。
- 生成コードで使う補助関数は、各言語のランタイムモジュールへ集約し、生成コードへの重複定義を避けます。

### 3.2 関数引数の受け渡し方針

- コピーコストが高い型（`string`, `vector<...>`, `unordered_map<...>`, `unordered_set<...>`, `tuple<...>`）は、関数内で直接変更されない場合に `const T&` で受けます。
- 引数の直接変更が検出された場合は値渡し（または非 const）を維持します。
- 直接変更判定は、代入・拡張代入・`del`・破壊的メソッド呼び出し（`append`, `extend`, `insert`, `pop` など）を対象に行います。

## 4. 検証手順（C++）

1. Python 版トランスパイラで `test/fixtures` を `test/transpile/cpp` へ変換
2. 生成 C++ を `test/transpile/obj/` にコンパイル
3. 実行結果を Python 実行結果と比較
4. セルフホスティング検証時は自己変換実行ファイルで `test/fixtures` -> `test/transpile/cpp2` を生成
5. `test/transpile/cpp` と `test/transpile/cpp2` の一致を確認

### 4.1 selfhost 検証のゴール条件

- 必須条件:
  - `selfhost/py2cpp.py` から生成した `selfhost/py2cpp.cpp` がコンパイル成功する。
  - その実行ファイルで `sample/py/01_mandelbrot.py` を C++ へ変換できる。
- 推奨確認:
  - `src/py2cpp.py` 生成版と `selfhost` 生成版の C++ ソース差分を確認する（差分自体は許容）。
  - 変換後 C++ をコンパイル・実行し、Python 実行結果と一致することを確認する。

### 4.2 一致判定条件（selfhost / 通常比較）

- ソース一致:
  - 生成 C++ の全文一致は「参考指標」であり、必須条件ではない。
- 実行一致:
  - 同じ入力に対して、Python 実行結果と生成 C++ 実行結果が一致することを必須とする。
- 画像一致:
  - PNG は raw scanline（復号後画素）一致を優先する。
  - PPM 出力を使う場合はファイルバイト列一致でも比較可能。

## 5. EASTベース C++ 経路

- `src/common/east.py`: Python -> EAST JSON
- `src/py2cpp.py`: EAST JSON -> C++
- `src/cpp_module/py_runtime.h`: C++ ランタイム集約
- 責務分離:
  - `range(...)` の意味解釈は EAST 構築側で完了させる
  - `src/py2cpp.py` は正規化済み EAST を文字列化する

## 6. 実装上の共通ルール

- `src/common/` には言語非依存で再利用される処理のみを配置します。
- 言語固有仕様（型マッピング、予約語、ランタイム名など）は `src/common/` に置きません。
- class 名・関数名・メンバー変数名には、日本語コメント（用途説明）を付与します。
- 標準ライブラリ対応の記載は、モジュール名だけでなく関数単位で明記します。
- ドキュメント未記載の関数は未対応扱いです。

## 7. 各ターゲットの実行モード注記

- `py2rs.py`: ネイティブ変換モード（Python インタプリタ非依存）
- `py2js.py` / `py2ts.py`: ネイティブ変換モード（Node.js ランタイム）
- `py2go.py` / `py2java.py`: ネイティブ変換モード（Python インタプリタ非依存）
- `py2swift.py` / `py2kotlin.py`: Node バックエンド実行モード（Python インタプリタ非依存）
