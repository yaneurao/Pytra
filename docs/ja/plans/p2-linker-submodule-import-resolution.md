# P2: linker が from package import module 形式のサブモジュール依存を解決しない

最終更新: 2026-03-21

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-LINKER-SUBMODULE-IMPORT`

## 背景

`from pytra.utils import png` のように、パッケージからサブモジュールを import する形式を linker が依存として解決できない。

### 問題の詳細

`program_loader.py` の `add_runtime_east_to_module_map` は `ImportFrom` ノードの `module` フィールドのみを `_resolve_runtime_east_path` に渡す:

```python
if kind == "ImportFrom":
    mod = stmt.get("module")  # "pytra.utils"
    east_path = _resolve_runtime_east_path(mod)  # → None（マッチせず）
```

- `from pytra.utils.gif import save_gif` → `module="pytra.utils.gif"` → `utils/gif.east` ✓
- `from pytra.utils import png` → `module="pytra.utils"` → `_RUNTIME_MODULE_BUCKETS` にマッチせず → None ✗

`png` はシンボルではなくサブモジュール `pytra.utils.png` だが、linker は import names を解決対象として見ていない。

### 影響

sample/py の 01〜04（`from pytra.utils import png` を使用）が link 時に `png.east` を含まず、emit 後のコードで png モジュールが欠落する。

## 対象

| ファイル | 変更内容 |
|---|---|
| `src/toolchain/link/program_loader.py` | `ImportFrom` 処理で import names についても `{module}.{name}` としてサブモジュール解決を試みる |

## 非対象

- `_resolve_runtime_east_path` のバケット定義変更
- emitter 側の修正

## 受け入れ基準

- [ ] `from pytra.utils import png` で `png.east` が link-output に含まれる
- [ ] `from pytra.std.time import perf_counter` 等の既存シンボル import がリグレッションしない
- [ ] sample 01〜04 の link が正しく png モジュールを含む

## 子タスク

- [x] [ID: P2-LINKER-SUBMODULE-IMPORT-01] `program_loader.py` の `ImportFrom` 処理で import names のサブモジュール解決を追加する
- [x] [ID: P2-LINKER-SUBMODULE-IMPORT-02] 既存テストのリグレッションがないことを検証する

## 決定ログ

- 2026-03-21: Dart backend の parity check で sample 01〜04 が FAIL。Julia backend 担当が link-output に `png.east` が含まれないことを特定。`from pytra.utils import png`（モジュール import）を linker が依存解決していないことが root cause。
