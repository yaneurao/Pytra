<a href="../../en/plans/p0-test-reorg.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0-TEST-REORG: test/ ディレクトリ再編 + pytra 実装本体の golden 生成

最終更新: 2026-03-25
ステータス: 着手前

## 背景

現在の test/ ディレクトリ構成:
- `test/builtin/` — `src/include/py/pytra/built_in/` の v2 extern 宣言の EAST1
- `test/stdlib/` — `src/include/py/pytra/std/` の v2 extern 宣言の EAST1

問題:
1. `test/builtin/` と `test/stdlib/` は `src/include/` の宣言 golden だが、名前からそれが読み取れない
2. `src/pytra/` の実装本体（`re.py`, `json.py`, `png.py`, `sequence.py` 等）の golden が存在しない
3. トランスパイル対象である `src/pytra/` のコードがパイプラインを通るか検証する手段がない

## 対象

### 1. 既存ディレクトリの移動

| 現在 | 移動先 |
|---|---|
| `test/builtin/` | `test/include/builtin/` |
| `test/stdlib/` | `test/include/stdlib/` |

### 2. pytra 実装本体の golden 新規生成

`src/pytra/` の実装本体をパイプライン全段（parse→resolve→compile→optimize）で処理し、golden を配置する。

```
test/
  pytra/
    east1/py/
      std/
        re.py.east1
        json.py.east1
        pathlib.py.east1
        ...
      built_in/
        sequence.py.east1
        io_ops.py.east1
        numeric_ops.py.east1
        ...
      utils/
        png.py.east1
        gif.py.east1
    east2/
      std/
        re.east2
        json.east2
        ...
      built_in/
        sequence.east2
        ...
      utils/
        png.east2
        gif.east2
    east3/
      ...
    east3-opt/
      ...
```

### 3. regenerate_golden.py の対応

`tools/gen/regenerate_golden.py` に `--case-root=include` と `--case-root=pytra` を追加する。

### 4. 既存パイプラインの参照パス更新

resolve 等が `test/builtin/east1/py/` を参照している箇所を `test/include/builtin/east1/py/` に更新する。

## 非対象

- fixture / sample のディレクトリ構成は変更しない
- selfhost（`test/selfhost/`）は P2-SELFHOST で別途対応

## 受け入れ基準

1. `test/builtin/` と `test/stdlib/` が `test/include/` に移動済み
2. `src/pytra/` の全 .py ファイルが parse 成功
3. parse → resolve → compile → optimize の全段が通り、golden が `test/pytra/` に配置済み
4. `regenerate_golden.py` が test/include/ と test/pytra/ に対応
5. `pytra-cli2` の resolve/compile/optimize/link が test/include/ の新パスで動作（parity 維持）
