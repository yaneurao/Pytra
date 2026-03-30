<a href="../../en/spec/spec-python-compat.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Python との互換性ガイド

このページは、**Python を知っているユーザー向け**に「Python ではこう動く / Pytra ではこう動く」を対比してまとめたガイドです。
詳細な入力制約の正本は [利用仕様](./spec-user.md) を参照してください。

## 基本方針

Pytra は「型注釈付きの Python サブセット」をソース言語とします。Python と同じ構文で書けますが、**静的型付けが前提**であり、Python の動的機能の一部は使えません。

表の凡例:
- ✅ 対応
- ⚠️ 部分対応・挙動が Python と異なる
- ❌ 非対応（変換エラー）

---

## 型注釈

| 構文・機能 | Python | Pytra |
|---|---|---|
| 変数の型注釈（`x: int = 1`） | 任意（省略可） | ✅ 省略可（リテラルは推論） |
| 関数の引数・戻り値注釈 | 任意（省略可） | ⚠️ 引数は省略すると `unknown` 型になる。戻り値型は `-> None` のみ省略可（body に `return <値>` がなければ自動的に `None`）。値を返す関数は注釈必須 |
| `from typing import cast` | 実行時に値をそのまま返す | ✅ `from pytra.typing import cast` で使える。`from typing import ...` の直接 import はエラー |
| `typing.TypeVar` によるジェネリクス | 型変数として機能する | ⚠️ 注釈として書くのみ許可。ジェネリック関数を定義したい場合は Pytra 固有の `@template` を使う |
| `type X = A \| B`（PEP 695 型エイリアス） | Python 3.12 以降で型エイリアスとして機能する | ✅ tagged union の宣言として対応。各ターゲット言語のネイティブな tagged union に変換される |

---

## 関数・引数

| 構文・機能 | Python | Pytra |
|---|---|---|
| 通常の引数・デフォルト値 | 動作する | ✅ 動作する |
| キーワード引数呼び出し（`f(a=1, b=2)`） | キーワード名で受け渡される | ✅ 対応。C++ など位置引数のみの言語では、シグネチャ参照で位置に並べ直して出力される |
| 引数の順序を入れ替えた呼び出し（`f(b=2, a=1)`） | 名前で解決されるため順序自由 | ✅ 対応。出力時に定義順へ並べ直す |
| `*args`（型注釈付き） | 任意個の位置引数を受け取る | ✅ `def f(*args: int)` の形式で対応。1つのみ許可 |
| `*args`（型注釈なし） | 動作する | ⚠️ `unknown` 型として扱われる |
| `**kwargs` | 任意個のキーワード引数を受け取る | ❌ パーサーで明示エラー |
| `f(**some_dict)` 呼び出し | dict をアンパックしてキーワード引数として渡す | ❌ 未サポート |
| `*`（keyword-only セパレータ） | `*` 以降の引数をキーワード専用に強制する | ⚠️ 構文はパース可能。ただし keyword-only の強制は未実装（`b` は通常の位置引数として扱われる） |
| `/`（positional-only セパレータ） | `/` より前の引数を位置専用に強制する | ❌ パーサーで明示エラー |
| `lambda` | 動作する | ✅ 対応。キャプチャ・引数渡し・即時呼び出し・三項演算子を含む |
| `@template("T")` によるジェネリック関数定義 | ❌ | ✅ Pytra 固有。型パラメータを持つ関数を定義できる |
| `@extern` による外部関数・クラスの宣言 | ❌ | ✅ Pytra 固有。外部ライブラリの関数・クラスをバインドするための宣言 |

---

## クラス・継承・OOP

| 構文・機能 | Python | Pytra |
|---|---|---|
| `class` 定義 | 動作する | ✅ 動作する |
| 単一継承 | 動作する | ✅ 動作する |
| 多重継承（`class C(A, B)`） | 動作する（MRO で解決） | ❌ 明示エラー |
| mix-in（多重継承によるメソッド注入） | 多重継承で実現する | ❌ 多重継承が非対応のため使えない |
| `__init__` でのインスタンスメンバー定義 | 動作する | ✅ `self.x = ...` の形式で動作する |
| class 本体でのメンバー宣言 | クラス変数として扱われる | ⚠️ C++ では `inline static`、C# では `static` に変換される |
| `super().__init__()` | 動作する | ✅ 動作する |
| `@dataclass` | 動作する | ✅ `field(default=...)` / `field(default_factory=...)` の代表的な使い方に対応 |
| `isinstance(x, T)` | 動作する | ✅ 動作する（ただし下記の `bool`/`int` 非互換を参照） |
| `@sealed` による sealed family 宣言 | ❌ | ✅ Pytra 固有。nominal ADT の family クラスを宣言するデコレータ |
| `getattr(obj, "name")` | 動的に属性を取得する | ❌ 設計上非対応。動的属性参照は unsupported by design |
| `setattr(obj, "name", val)` | 動的に属性を設定する | ❌ 設計上非対応 |
| `object` 型変数へのメソッド呼び出し | 動作する（実行時に解決） | ❌ 明示エラー。型を確定してからアクセスすること |

---

## 制御フロー

| 構文・機能 | Python | Pytra |
|---|---|---|
| `if / elif / else` | 動作する | ✅ 動作する |
| `for` / `while` | 動作する | ✅ 動作する |
| `match / case` | Python 3.10 以降で動作する | ⚠️ `@sealed` family に対する exhaustive マッチのみ対応。guard pattern・nested pattern・match expression は非対応 |
| `try / except / finally` | 動作する | ✅ 基本的な使い方は動作する。複数 except 節の型パターン詳細は未確定 |
| `yield` / ジェネレータ | 動作する | ⚠️ 未確定（専用テスト未整備） |
| 文末セミコロン（`x = 1; y = 2`） | 動作する | ❌ パーサーで入力エラー |

---

## 組み込み型・数値

| 型・機能 | Python | Pytra |
|---|---|---|
| `int` | 任意精度整数（bigint） | ⚠️ `int64`（64ビット整数）。オーバーフローは未検出 |
| `int64`, `int32`, `int16`, `int8` | ❌ | ✅ Pytra 固有の符号付き固定幅整数型。`from pytra.types import int64` などで使える |
| `uint64`, `uint32`, `uint16`, `uint8` | ❌ | ✅ Pytra 固有の符号なし固定幅整数型 |
| `float` | 64ビット浮動小数点 | ✅ `float64` として動作する |
| `float32` | ❌ | ✅ Pytra 固有の 32ビット浮動小数点型。`from pytra.types import float32` で使える |
| `bool` | 動作する | ✅ 動作する（ただし `int` のサブタイプではない。下記参照） |
| `str` | 動作する | ✅ スライス・for-each・f-string 等に対応 |
| `list[T]` | 動作する | ✅ 動作する |
| `dict[K, V]` | 動作する | ✅ 動作する |
| `set[T]` | 動作する | ✅ 動作する |
| `tuple` | 動作する | ✅ 動作する |
| `bytes` / `bytearray` | 動作する | ✅ 基本操作に対応 |
| `None` | 動作する | ✅ 動作する |
| `Any` | 動作する | ✅ 基本的な使い方に対応 |

### `bool` は `int` のサブタイプではない（Python 非互換）

Python では歴史的経緯により `bool` は `int` のサブクラスであり、`isinstance(True, int)` は `True` を返す。Pytra ではこの関係を **採用しない**。

| isinstance | Python | Pytra |
|---|---|---|
| `isinstance(True, bool)` | `True` | `True` |
| `isinstance(True, int)` | `True` | **`False`** |
| `isinstance(Color.RED, Color)` | `True` | `True` |
| `isinstance(Color.RED, IntEnum)` | `True` | `True` |
| `isinstance(Color.RED, int)` | `True` | **`False`** |

理由:
- Python の `bool` が `int` のサブクラスなのは Python 2.3 で `bool` を後付けした歴史的経緯であり、言語設計としては失敗と広く認識されている
- Pytra は型注釈ベースの静的型付けを前提とするため、`bool` を `int` として算術演算に使うケースは想定しない
- `IntEnum` / `IntFlag` の値は `int` として使えるが、`isinstance` で `int` 判定する必要性は薄い
- この非互換により、型判定の実装が全ターゲット言語で大幅に簡素化される

---

## コレクション・内包表記

| 構文・機能 | Python | Pytra |
|---|---|---|
| list 内包表記 | `for` を複数重ねられる | ⚠️ generator は 1 個前提（ネストは別途サポート） |
| set 内包表記 | `for` を複数重ねられる | ⚠️ generator は 1 個前提 |
| dict 内包表記 | `for` を複数重ねられる | ⚠️ generator は 1 個前提 |
| 内包表記の `if` 条件 | 動作する | ✅ 動作する |
| ネスト内包 | 動作する | ✅ 動作する |
| `collections.deque[T]` | `from collections import deque` で使える | ✅ `from pytra.std.collections import deque` で使える。代表的な操作（`append`, `popleft` 等）に対応 |

---

## モジュール・import

| 構文・機能 | Python | Pytra |
|---|---|---|
| `import M` / `from M import S` | 動作する | ✅ 動作する |
| `from M import S as A` / `import M as A` | 動作する | ✅ 動作する |
| `from M import *` | 動作する | ⚠️ 静的に公開シンボルを展開できる場合のみ通る |
| 相対 import（`from .m import x`） | 動作する | ✅ sibling / parent に対応 |
| Python 標準ライブラリの直接 import | 動作する | ❌ 明示エラー。`pytra.std.*` 経由で使うこと（下表参照） |
| ユーザー作成モジュールの import | 動作する | ✅ 対応。複数ファイル依存解決は段階的に実装中 |

### 標準ライブラリの代替 import

Python では直接 import できるモジュールも、Pytra では `pytra.*` 経由が必要です。

| Python での書き方 | Pytra での書き方 |
|---|---|
| `from typing import cast` | `from pytra.typing import cast` |
| `from enum import Enum, IntEnum` | `from pytra.enum import Enum, IntEnum` |
| `from dataclasses import dataclass, field` | `from pytra.dataclasses import dataclass, field` |
| `from collections import deque` | `from pytra.std.collections import deque` |
| `import math` / `from math import sqrt` | `from pytra.std.math import sqrt` など |
| `from pathlib import Path` | `from pytra.std.pathlib import Path` |
| `import re` / `from re import compile` | `from pytra.std.re import compile` など |
| `import sys` | `from pytra.std.sys import ...` |
| `import os` | `from pytra.std.os import ...` |
| `import json` | `from pytra.std.json import ...` |

> `pytra.typing` / `pytra.enum` / `pytra.dataclasses` は変換器が import 文を無視します（パーサーが `cast` / `Enum` / `dataclass` を既に認識しているため）。Python 実行時は標準モジュールを re-export するためそのまま動作します。

---

## Pytra 固有の機能（Python 標準にない記法）

以下は Python にはなく Pytra が独自に提供する機能です。各セクションにも記載しています。

| 機能 | Pytra での記法 | 詳細 |
|---|---|---|
| 固定幅整数型 | `int64`, `int32`, `int16`, `int8`, `uint64`, `uint32`, `uint16`, `uint8` | 組み込み型セクション参照 |
| 32ビット浮動小数点型 | `float32` | 組み込み型セクション参照 |
| union 型宣言（tagged union） | `type X = A \| B`（PEP 695 構文） | 型注釈セクション参照 |
| nominal ADT（sealed family） | `@sealed` class + variant class | クラスセクション参照 |
| generic 関数のテンプレート定義 | `@template("T")` デコレータ | 関数セクション参照 |
| 外部関数・クラスのバインディング宣言 | `@extern` デコレータ | 関数セクション参照 |
| C++ コードの直接埋め込み | `# Pytra::cpp ...` コメント | C++ ターゲット限定 |

---

## 関連ドキュメント

- 入力制約の正本: [利用仕様](./spec-user.md)
- tagged union の詳細: [tagged union 仕様](./spec-tagged-union.md)
- C++ backend サポートマトリクス: [py2cpp サポートマトリクス](../language/cpp/spec-support.md)
- 使い方・実行手順: [チュートリアル](../tutorial/README.md)
