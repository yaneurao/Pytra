<a href="../../ja/plans/p0-pytra-import-unify.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-pytra-import-unify.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-pytra-import-unify.md`

# P0: Python 標準モジュール import を pytra.* 経由に統一

最終更新: 2026-03-19

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PYTRA-IMPORT-UNIFY-01`

## 背景

現在、`typing` / `enum` / `dataclasses` の import は Python 標準モジュールからの直接 import を no-op として許可している。
これにより「どの標準モジュールが使えてどれが使えないか」をユーザーが覚える必要があり、ルールが複雑になっている。

## 方針

**「Python 標準モジュールの import は一切認めない。Pytra が提供する `pytra.*` モジュールのみ import 可能」** というルールに統一する。

### 提供するダミーモジュール

| モジュール | 内容 | Python 実行時 | 変換器 |
|-----------|------|---------------|--------|
| `pytra.typing` | `cast` 等を re-export | `from typing import *` で動く | import を無視 |
| `pytra.enum` | `Enum`, `IntEnum`, `IntFlag` を re-export | `from enum import *` で動く | import を無視 |
| `pytra.dataclasses` | `dataclass`, `field` を re-export | `from dataclasses import *` で動く | import を無視 |
| `pytra.types` | `int8`, `uint8`, `int64` 等のスカラー型 | `int`/`float` エイリアス | import を無視 |

### ユーザーの書き方

```python
from pytra.typing import cast
from pytra.enum import Enum, IntEnum
from pytra.dataclasses import dataclass, field
from pytra.types import int64, uint8
from pytra.std import sys
from pytra.std.math import sqrt
```

## 実装ステップ

1. `src/pytra/typing.py` 新規作成（`from typing import *` で re-export）
2. `src/pytra/enum.py` 新規作成（`from enum import *` で re-export）
3. `src/pytra/dataclasses.py` 新規作成（`from dataclasses import *` で re-export）
4. `core_module_parser.py` で `pytra.typing` / `pytra.enum` / `pytra.dataclasses` を no-op import に追加
5. 既存の `typing` / `enum` / `dataclasses` 直接 import の no-op 処理は後方互換として維持（将来的に警告→エラー化）
6. フィクスチャ・サンプルの import を `pytra.*` 経由に修正
7. `docs/ja/spec/spec-user.md` を更新

## 対象

- `src/pytra/typing.py` — 新規
- `src/pytra/enum.py` — 新規
- `src/pytra/dataclasses.py` — 新規
- `src/toolchain/compile/core_module_parser.py` — no-op import 追加
- `test/fixtures/` — import 修正
- `docs/ja/spec/spec-user.md` — import ルール更新

## 非対象

- 既存の `typing` / `enum` / `dataclasses` 直接 import のエラー化（後方互換で当面維持）

## 受け入れ基準

- `pytra.typing` / `pytra.enum` / `pytra.dataclasses` が存在し、Python 実行時に動作する。
- 変換器がこれらの import を無視する。
- フィクスチャが `pytra.*` 経由の import に修正されている。
- `docs/ja/spec/spec-user.md` に import ルールが記載されている。
- fixture / sample pass。

## 決定ログ

- 2026-03-19: ユーザー提案。Python 標準モジュールの import を一切認めず、pytra.* 経由に統一する方針を決定。ダミーモジュールで Python 実行時互換を維持。
