# チュートリアル

Pytra を初めて触る人向けの入口です。
まずはここから読み進めてください。

## 3分で触る最小例

まずは次の 1 ファイルだけで十分です。

```python
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    print(add(3, 4))
```

この `add.py` を用意したら、まずは C++ に変換して実行します。

```bash
./pytra add.py --output-dir out/add_case --build --run --exe add.out
```

想定される標準出力:

```text
7
```

生成コードだけ先に見たいなら、次でも構いません。

```bash
./pytra add.py --output out/add.cpp
```

Rust に変換したいなら target を変えるだけです。

```bash
./pytra add.py --target rs --output out/add.rs
```

この最小例が通ってから、下のページへ進むのがいちばんわかりやすいです。

## 最初に読む順番

1. 実行手順を確認する: [使い方](./how-to-use.md)
2. 言語仕様の入口を確認する: [仕様書トップ](../spec/index.md)
3. 型推論の詳細を確認する: [EAST仕様の型推論ルール](../spec/spec-east.md#7-型推論ルール)
4. `@extern` / `extern(...)` を確認する: [extern.md](./extern.md)
5. `py2x.py` / `ir2lang.py` を直接使う: [transpiler-cli.md](./transpiler-cli.md)
6. エラーの見方と詰まりどころを確認する: [troubleshooting.md](./troubleshooting.md)
7. 高度な変換ルートを確認する: [発展的な使い方](./advanced-usage.md)
8. parity / selfhost / local CI を確認する: [開発運用ガイド](./dev-operations.md)

## 読み分け

- `.py` を各ターゲット言語へ変換して実行したい
  - [使い方](./how-to-use.md)
- 型推論の詳細を確認したい
  - [EAST仕様の型推論ルール](../spec/spec-east.md#7-型推論ルール)
- 仕様の正本を確認したい
  - [仕様書トップ](../spec/index.md)
- `py2x.py` / `ir2lang.py` を直接使いたい
  - [transpiler-cli.md](./transpiler-cli.md)
- エラーカテゴリや詰まりどころを確認したい
  - [troubleshooting.md](./troubleshooting.md)
- Pytra独自のdecoratorについて
  - `@template` : C++テンプレートみたいなもの。現状の v1 は linked runtime helper 限定です。
    - [template 仕様（案）](../spec/spec-template.md)
  - `@extern` / `extern(...)` : 外部関数、外部classを呼び出すためのもの。
    - [extern.md](./extern.md)
  - `@abi` : ABIを定義するためのもの。
    - [発展的な使い方](./advanced-usage.md)
- parity checkの方法 や selfhost を含む開発運用を確認したい
  - [開発運用ガイド](./dev-operations.md)

## Pytra独自decoratorの最小例

`@extern`:

```python
from pytra.std import extern

@extern
def sin(x: float) -> float:
    ...
```

`@abi`:

```python
from pytra.std import abi

@abi(args={"parts": "value"}, ret="value")
def py_join(sep: str, parts: list[str]) -> str:
    ...
```

`@template`:

```python
from pytra.std.template import template

@template("T")
def py_min(a: T, b: T) -> T:
    ...
```

補足:
- `@template` は現状 user code 全般ではなく、linked runtime helper 向けの v1 です。
- ふつうに `.py` を変換して動かすだけなら、最初は `@extern` / `@abi` / `@template` を使わなくて構いません。

## 関連リンク

- 仕様書トップ: [index.md](../spec/index.md)
- 利用仕様: [spec-user.md](../spec/spec-user.md)
- オプション仕様: [spec-options.md](../spec/spec-options.md)
- ツール一覧: [spec-tools.md](../spec/spec-tools.md)
