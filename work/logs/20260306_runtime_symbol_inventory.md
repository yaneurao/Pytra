# runtime symbol 棚卸しメモ（2026-03-06）

対象 ID:
- `P0-RUNTIME-SYMBOL-INDEX-01-S1-01`
- `P0-RUNTIME-SYMBOL-INDEX-01-S1-02`

## 1. 目的

`runtime symbol -> module/file` 対応がどの層に散っているかを固定し、以後の JSON index 化で何をどこから除去するかを明確にする。

## 2. 現状観測

### IR 構築

- `src/toolchain/ir/core.py`
  - `enumerate -> py_enumerate`
  - `any -> py_any`
  - `all -> py_all`
  - `reversed -> py_reversed`
  - `ord -> py_ord`
  - `chr -> py_chr`
  - `list/set/dict ctor`

観測:
- 裸の `runtime_call` はあるが、所属 module がない。

### frontend

- `src/toolchain/frontends/signature_registry.py`
  - `_FUNCTION_RUNTIME_CALLS`
  - `_IMPORTED_SYMBOL_RUNTIME_CALLS`
  - `_NONCPP_IMPORTED_SYMBOL_RUNTIME_CALLS`
  - `_NONCPP_MODULE_ATTR_RUNTIME_CALLS`
  - `_OWNER_METHOD_RUNTIME_CALLS`
  - `_OWNER_ATTRIBUTE_TYPES`

観測:
- `perf_counter`, `Path`, `json.loads`, `write_rgb_png`, `save_gif`, `math.sqrt`, `dict.get`, `list.append` などがコード直書きで管理されている。
- 型推定と runtime symbol 所属と target 別事情が同じファイルに混在している。

### C++ backend

- `src/backends/cpp/emitter/module.py`
  - Python module 名から include path / namespace を推定
- `src/backends/cpp/emitter/runtime_paths.py`
  - `module_tail -> *.gen.h`
  - `module_name -> runtime/cpp/...`
- `src/backends/cpp/profiles/runtime_calls.json`
  - `os.path.join`, `glob.glob`, `ArgumentParser`, `re.sub`, `sys.stdout.write`

観測:
- module 所属決定と C++ 描画決定が混在している。

### tooling

- `tools/build_multi_cpp.py`
- `tools/gen_makefile_from_manifest.py`

観測:
- include 起点で runtime source を再帰収集している。
- 現時点では module/symbol index を持たないため、artifact 対応を build graph 側で再推論している。

## 3. 固定した責務境界

### IR に残す

- `runtime_module_id`
- `runtime_symbol`
- 必要最小限の dispatch 情報

### index に移す

- target 別 header path
- target 別 compile source
- `gen/ext` companion 情報

### backend/tooling が導出

- C++ namespace
- include 並び順
- dedupe / sort
- 最終的な fully-qualified call 名

## 4. schema 方針

index は次の 2 層に分ける。

1. `modules`
   - target 非依存
   - SoT module と exported symbol を保持
2. `targets`
   - target 依存
   - `public_headers`
   - `compile_sources`
   - `companions`

## 5. 禁止

- `py_enumerate -> iter_ops` を hand-written JSON や Python dict へ直書きすること
- `runtime/cpp/std/time.gen.h` などの path を IR へ埋めること
- `signature_registry.py` を index の source-of-truth にすること
