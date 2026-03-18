# 利用仕様（Pytra）

<a href="../../en/spec/spec-user.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


このドキュメントは、Pytra の利用方法と入力制約をまとめた仕様です。
本書は仕様定義にフォーカスし、実行コマンドや実行手順は [tutorial/how-to-use.md](../tutorial/how-to-use.md) で管理します。

## 1. 目的

Pytra は、型注釈付き Python コードを複数言語へ変換するトランスパイラです。正規 CLI は `src/py2x.py` です。

- Python -> C#（`python src/py2x.py --target cs ...`）
- Python -> C++（`python src/py2x.py --target cpp ...`）
- Python -> Rust（`python src/py2x.py --target rs ...`）
- Python -> JavaScript（`python src/py2x.py --target js ...`）
- Python -> TypeScript（`python src/py2x.py --target ts ...`）
- Python -> Go（`python src/py2x.py --target go ...`）
- Python -> Java（`python src/py2x.py --target java ...`）
- Python -> Swift（`python src/py2x.py --target swift ...`）
- Python -> Kotlin（`python src/py2x.py --target kotlin ...`）
- Python -> Ruby（`python src/py2x.py --target ruby ...`）
- Python -> Lua（`python src/py2x.py --target lua ...`）
- Python -> PHP（`python src/py2x.py --target php ...`）

## 2. Python 入力仕様

- 入力 Python は、基本的に型注釈付きコードを前提とします。
- 型注釈は次の条件では省略できます（暗黙の型推論）。
  - 右辺がリテラルで型が一意な代入（例: `x = 1`, `y = 1.5`, `s = "abc"`）。
  - 右辺の変数型が既知な単純代入（例: `y = x` で `x` の型が確定済み）。
- self_hosted parser の関数シグネチャでは、引数の型注釈は推奨です。
  - 無注釈引数（例: `def f(x): ...`）は受理し、`unknown` として扱います。
  - `def f(...): return ...` 形式の 1 行定義（class 内メソッドを含む）を受理します。
- `class` は単一継承をサポートします。
- `self.xxx` に対する `__init__` 内代入はインスタンスメンバーとして扱います。
- class 本体で宣言されたメンバーは class member（C# では `static`、C++ では `inline static`）として扱います。
- `@dataclass` を付けた class は dataclass として扱い、フィールドとコンストラクタを生成します。
- nominal ADT の declaration surface v1 は次を正本とします。
  - family 宣言は top-level `class` に `@sealed` を付けて表します。
  - variant 宣言は top-level `class` とし、family を単一継承しなければなりません。
  - payload を持つ variant は `@dataclass` を付け、unit variant は通常の class body で表します。
  - constructor surface は variant class への通常の call (`Ok(...)`, `Err(...)`) を正本とし、family class 自体は constructor entrypoint にしません。
  - canonical な variant access surface は `isinstance(x, Variant)` と、その成功 branch での field access です。
  - nested variant class、`adt` 専用 block、`Result.Ok(...)` のような namespace sugar は v1 に含めません。
- `match/case` による nominal ADT 分解は statement-first の Stage B surface として契約を固定します。
  - 現時点で selfhost parser から直接使う canonical source surface は Stage A の `isinstance` + field access です。
  - representative な EAST3 / backend lane では `Match` / `VariantPattern` / `PatternBind` metadata が固定済みで、source parser が `match/case` を受理するときも同じ contract を使います。
  - closed family に対する `match` は exhaustive でなければなりません。v1 では「各 variant を 1 回ずつ列挙する」か「末尾の `_` wildcard で残りを受ける」のどちらかを正本とします。
  - 同じ variant を複数回書くこと、または coverage が閉じた後ろに branch を置くことは error です。
  - `match` expression、guard pattern、nested pattern は v1 の受理対象に含めません。
- `import` / `from ... import ...` をサポートします。
- `from ... import *`（ワイルドカード import）をサポートします。
- relative `from-import` の canonical surface v1 は次を正本とします。
  - `from .m import x`
  - `from ..pkg import y`
  - `from .. import helper`
  - `from . import x`
  - `from .m import *`
  - 解決基準は importing file path と entry root に対する static な module 正規化であり、runtime の `__package__` は見ません。
  - entry root より上へ出る relative import は `input_invalid(kind=relative_import_escape)` で fail-closed です。
  - 正規化後 module が存在しない場合は `input_invalid(kind=missing_module)` です。
  - Python 非合法構文である `import .m` はサポート対象外です。
- 文末セミコロン（`;`）はサポート対象外です（self_hosted parser では入力エラーとして扱います）。
- `# type:ignore` はコメントとして扱い、構文/意味解釈には使いません。
- `pytra.types` モジュールは Pytra 固有のスカラー型（`int8`, `uint8`, `int64`, `float64` 等）を提供します。
  - Python 実行時は `int` / `float` のエイリアスとして動作します。
  - `from pytra.types import int64, uint8` のように import して使用します。
  - 変換器はこの import を無視します（型名はパーサーが既に認識しているため）。
  - VS Code の Pylance で未定義警告が出る場合はこの import を追加してください。
- `type X = A | B | ...`（PEP 695）で union 型（tagged union）を宣言できます。
  - 各ターゲット言語のネイティブな tagged union に変換されます。
  - 再帰型（`type JsonVal = ... | list[JsonVal]`）もサポートします。
  - union 変数から値を取り出すには `typing.cast(T, v)` を使用します。
  - 詳細は [tagged union 仕様](./spec-tagged-union.md) を参照してください。
- トランスパイル対象コードでは、**Python 標準モジュールの直接 import は禁止**です。すべて `pytra.*` 経由で import してください。
  - `from pytra.typing import cast` — `typing.cast` の代わり
  - `from pytra.enum import Enum, IntEnum, IntFlag` — `enum` の代わり
  - `from pytra.dataclasses import dataclass, field` — `dataclasses` の代わり
  - `from pytra.types import int64, uint8` — Pytra 固有スカラー型
  - `from pytra.std.collections import deque` — `collections.deque` の代わり
  - `from pytra.std.math import sqrt` — `math` 等の実行時モジュール
  - `pytra.typing` / `pytra.enum` / `pytra.dataclasses` / `pytra.types` は言語機能の補助モジュールであり、変換器はこれらの import を無視します（パーサーが `cast` / `Enum` / `dataclass` / `int64` 等を既に認識しているため）。Python 実行時は標準モジュールを re-export するため、そのまま動作します。
  - `pytra.std.*` は実行時ライブラリであり、変換器は依存解決・ヘッダ生成に使用します。
  - `from typing import ...` / `from enum import ...` / `from dataclasses import ...` 等の Python 標準モジュールからの直接 import はエラーになります。
- import 可能なのは `pytra.*` 配下のモジュールと、ユーザーが作成した自作 `.py` モジュールです。
- 自作モジュール import は仕様上合法ですが、複数ファイル依存解決は段階的に実装中です。
- `object` 型（`Any` 由来を含む）に対する属性アクセス・メソッド呼び出しは禁止です。
  - 例: `x: object` に対して `x.foo()` / `x.bar` は不可。
  - 必要な場合は、明示的に型を確定させた変数へ代入してからアクセスしてください。
- `getattr(...)` / `setattr(...)` は user language surface に含めません。
  - 文字列名による汎用の動的属性参照・更新は、仕様として unsupported by design です。
  - これは `object` / `Any` 経由の open object model を各 backend に持ち込まないための制約で、現時点で一般サポートする予定はありません。
  - 必要な場合は、具体型に対する通常の `x.field` アクセス、`dict` / JSON オブジェクト、または `@extern` / ambient binding の専用 seam を使ってください。
- C++ 向けには、コメントによるパススルーを利用できます。
  - `# Pytra::cpp ...` / `# Pytra::pass ...` を文の直前に置くと、生成 C++ へその行をそのまま挿入します。
  - 複数行は `# Pytra::cpp begin` ... `# Pytra::cpp end`（または `pass`）で指定できます。
  - 詳細仕様は `docs/ja/spec/spec-east.md` を参照してください。

## 3. テストケース方針

- 入力 Python は `test/fixtures/` 配下に配置します（カテゴリ別サブディレクトリ）。
- 言語別の変換結果は `test/transpile/cs/`, `test/transpile/cpp/`, `test/transpile/rs/`, `test/transpile/js/`, `test/transpile/ts/`, `test/transpile/go/`, `test/transpile/java/`, `test/transpile/swift/`, `test/transpile/kotlin/`, `test/transpile/ruby/`, `test/transpile/lua/`, `test/transpile/php/` に配置します。
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
    imports/
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
- 言語別の変換結果は `sample/cpp/`, `sample/rs/`, `sample/cs/`, `sample/js/`, `sample/ts/`, `sample/go/`, `sample/java/`, `sample/swift/`, `sample/kotlin/`, `sample/ruby/`, `sample/lua/`, `sample/php/` に配置します。
- バイナリや中間生成物は `sample/obj/`, `sample/out/` を利用します（Git 管理外）。
- Python から import する自作ライブラリは `src/pytra/` 配下（`pytra.std.*`, `pytra.utils.*`）を使用します。
  - 画像: `from pytra.utils import png`, `from pytra.utils.gif import save_gif`
  - テスト補助: `from pytra.utils.assertions import py_assert_eq` など
  - EAST 変換器: `python src/toolchain/compiler/east.py <input.py> ...`
- 画像出力サンプル（`sample/py/01`, `02`, `03`）は PNG 形式で出力します。
- GIF サンプルは `sample/out/*.gif` に出力します。

## 5. ユニットテスト実行方法

プロジェクトルート (`Pytra/`) で次を実行します。

```bash
python -m unittest discover -s test/unit -p "test_*.py" -v
```

共通エミッタ基盤（`src/backends/common/emitter/code_emitter.py`）のみを確認したい場合:

```bash
python -m unittest discover -s test/unit/common -p "test_code_emitter.py" -v
```

`test/fixtures/**/*.py` を一括実行して末尾出力 `True` を検証する専用テスト:

```bash
python -m unittest discover -s test/unit/common -p "test_fixtures_truth.py" -v
```

## 6. 利用時の注意

- C++ の速度比較は `-O3 -ffast-math -flto` を使用します。
- 未対応構文はトランスパイル時に `TranspileError` で失敗します。
- `test/transpile/obj/`, `test/transpile/cpp2/`, `sample/obj/`, `sample/out/` は生成物ディレクトリです。
- `src/pytra/` 配下モジュールを使う Python サンプルは、必要に応じて `PYTHONPATH=src` を付与して実行します。

## 7. 関連ドキュメント

- 使い方: [tutorial/how-to-use.md](../tutorial/how-to-use.md)
- py2cpp 機能対応表（テスト根拠）: [py2cpp サポートマトリクス](../language/cpp/spec-support.md)
- サンプルコード: [サンプルコード案内](../../sample/readme-ja.md)
- 実装状況詳細: [実装状況メモ（WIP）](../plans/archive/pytra-wip.md)
