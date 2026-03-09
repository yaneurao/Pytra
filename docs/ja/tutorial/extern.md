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
