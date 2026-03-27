<a href="../../ja/plans/plan-pod-isinstance.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/plan-pod-isinstance.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/plan-pod-isinstance.md`

# POD 型判定と汎用 deep copy の設計案

最終更新: 2026-03-24
ステータス: 案（未着手）

## 1. 動機

汎用的な `deep_copy` を `pytra.std` に実装したいが、「この値はプリミティブ（コピー不要）か、コンテナ（再帰コピー必要）か」の判定がトランスパイル先で動かない。

Python では `isinstance(val, (bool, int, float, str))` で全整数型（`int8`, `int64` 等）を捕捉できるが、C++ / Go / Rust では `int8_t != int` であり、同じ判定が成立しない。

## 2. 提案: `POD` 特殊型

`pytra.types` に `POD` を定義し、`isinstance(x, POD)` で「プリミティブか否か」を全言語で判定可能にする。

### Python 側の定義

```python
# pytra/types.py
POD = (type(None), bool, int, float, str)
```

Python では `isinstance(val, POD)` がそのまま動く。

### EAST での扱い

- `isinstance(x, POD)` を EAST が認識し、`semantic_tag: "type.isinstance.pod"` 等を付与する。
- emitter はこの semantic_tag を見て言語固有の判定コードを emit する。

### 各言語の emit 例

| 言語 | `isinstance(x, POD)` の emit |
|---|---|
| Python | `isinstance(x, (type(None), bool, int, float, str))` |
| C++ | `is_pod_v<decltype(x)>` （カスタム trait） |
| Go | 型 switch で `bool, int8, int16, ..., int64, float32, float64, string` + `nil` |
| Rust | `T: Copy` trait bound、または `matches!` で判定 |
| Java | `x instanceof Number \|\| x instanceof String \|\| x instanceof Boolean \|\| x == null` |

### POD に含まれる型

- `None`
- `bool`
- `int8`, `uint8`, `int16`, `uint16`, `int32`, `uint32`, `int64`, `uint64`
- `float32`, `float64`
- `str`

### POD に含まれない型

- `list[T]`, `set[T]`, `dict[K,V]`, `tuple[T1,...]`（コンテナ）
- クラスインスタンス
- `Path`, `Exception` 等の拡張型

## 3. 汎用 deep copy の実装

`POD` があれば `pytra.std.copy` に全言語対応の `deep_copy` を書ける:

```python
from pytra.types import POD

def deep_copy(val):
    if val is None:
        return None
    if isinstance(val, POD):
        return val
    if isinstance(val, list):
        return [deep_copy(item) for item in val]
    if isinstance(val, dict):
        return {k: deep_copy(v) for k, v in val.items()}
    # dataclass: フィールド単位で再帰コピー（将来拡張）
    return val
```

## 4. 未決事項

- `tuple` は POD かコンテナか（Python では immutable だが、中身が mutable な場合がある）
- `bytes` / `bytearray`（`list[uint8]` に正規化されるが、POD 的な扱いをしたい場合がある）
- dataclass の deep copy 対応（フィールド列挙の仕組みが必要）
- `isinstance(x, POD)` の EAST ノード表現（専用ノードか、semantic_tag か）
- 循環参照がある場合の対応（現時点では「循環なし」を前提とする）
