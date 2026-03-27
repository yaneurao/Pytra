<a href="../../en/tutorial/extern.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# `@extern` / `extern(...)` の使い方

`@extern` と `extern(...)` は、Pytra から外部実装や ambient global を参照するための独自記法です。  
正規仕様は [ABI仕様](../spec/spec-abi.md) を参照してください。

## 関数 extern

- トップレベル関数を外部実装へ委譲したいときは `@extern` を使います。
- 変換器は本体を生成せず、ターゲット側の実装を呼び出す前提で扱います。

```python
from pytra.std import extern

@extern
def sin(x: float) -> float:
    ...
```

### v2 extern: `extern_fn` / `extern_var` / `extern_class`

新パイプライン（toolchain2）では `@extern` を用途別に分離し、runtime 情報を必須で指定します。

```python
# pytra: builtin-declarations

# 関数
@extern_fn(module="my_game.physics", symbol="apply_gravity", tag="user.physics.gravity")
def apply_gravity(x: float, y: float, dt: float) -> float: ...

# 変数
gravity: float = extern_var(module="my_game.physics", symbol="GRAVITY", tag="user.physics.const_gravity")

# クラス
@extern_class(module="my_game.entity", symbol="Player", tag="user.entity.player")
class Player:
    def move(self, dx: float, dy: float) -> None: ...
```

| 関数 | 用途 |
|---|---|
| `extern_fn` | 外部関数宣言（decorator） |
| `extern_var` | 外部変数宣言 |
| `extern_class` | 外部クラス宣言（decorator） |

| 引数 | 意味 |
|---|---|
| `module` | 実装がある runtime モジュール（言語非依存） |
| `symbol` | runtime モジュール内での名前 |
| `tag` | semantic_tag（emitter が意味を識別するキー） |

全引数が必須です。詳細は [spec-builtin-functions.md §10](../spec/spec-builtin-functions.md) を参照。

## 変数 extern

- 変数に `@extern` は付けられません。
- 変数 extern は `name = extern(...)` で書きます。

使い分けは次の 3 つです。

- `name: T = extern(expr)`
  - host fallback や runtime hook 初期化を行う変数 extern
- `name: Any = extern()`
  - 同名 ambient global
- `name: Any = extern("symbol")`
  - 別名 ambient global

```python
from typing import Any
from pytra.std import extern

document: Any = extern()
console: Any = extern("console")
```

補足:

- ambient global は現状 JS/TS backend 限定です。
- `document: Any = extern()` は `document` を、`console: Any = extern("console")` は `console` をそのまま参照する形に lower します。
