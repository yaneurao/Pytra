# P0-INCLUDE-REORG: test/include/ のフォルダ構成を他と統一

最終更新: 2026-03-25
ステータス: 着手前

## 背景

test/ 配下のフォルダ構成が test/include/ だけ他と異なる。

現状:
```
test/fixture/east1/py/...       ← east1/py/ が先
test/sample/east1/py/...        ← east1/py/ が先
test/pytra/east1/py/...         ← east1/py/ が先
test/include/builtin/east1/py/  ← builtin/ が先（不統一）
test/include/stdlib/east1/py/   ← stdlib/ が先（不統一）
```

統一後:
```
test/include/east1/py/
  built_in/
    builtins.py.east1
    containers.py.east1
  std/
    math.py.east1
    time.py.east1
    ...
```

## 対象

### 移動

| 現在 | 移動先 |
|---|---|
| `test/include/builtin/east1/py/builtins.py.east1` | `test/include/east1/py/built_in/builtins.py.east1` |
| `test/include/builtin/east1/py/containers.py.east1` | `test/include/east1/py/built_in/containers.py.east1` |
| `test/include/stdlib/east1/py/math.py.east1` | `test/include/east1/py/std/math.py.east1` |
| `test/include/stdlib/east1/py/*.py.east1` | `test/include/east1/py/std/*.py.east1` |

### パス参照の更新

`pytra-cli2.py` の resolve が `test/include/builtin/east1/py/` を参照している箇所を `test/include/east1/py/built_in/` に更新する。

該当箇所:
- `src/pytra-cli2.py` の `_resolve_one()` 内の builtins_path / containers_path
- `tools/regenerate_golden.py` の include golden 生成パス
- `src/toolchain2/resolve/py/` の BuiltinRegistry ロード箇所

### 旧ディレクトリの削除

移動完了後に `test/include/builtin/` と `test/include/stdlib/` を削除する。

## 受け入れ基準

1. `test/include/east1/py/built_in/` と `test/include/east1/py/std/` に golden が配置
2. `test/include/builtin/` と `test/include/stdlib/` が削除済み
3. `pytra-cli2` の resolve が新パスで動作（fixture 132 + sample 18 parity 維持）
4. `regenerate_golden.py` が新パスで golden 生成可能
