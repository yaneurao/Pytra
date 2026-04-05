# P0-CPP-MAPPING-CLEANUP

## 背景

- `rt:call_coverage` は `src/runtime/cpp/mapping.json` の `calls` と EAST3 golden の出現値を突き合わせる。
- ただし C++ backend では、通常 golden（`fixture/sample/stdlib`）だけでなく `linked` / `selfhost` / `pytra` / `east3-opt` にも実運用上の EAST3 がある。
- emitter guide の正本は「EAST3 の `runtime_call` / `runtime_symbol` と `mapping.json`」であり、lint 対象 roots の都合だけで key を削るのは誤り。

## 今回の方針

1. `mapping.json` の key は current EAST3 の canonical key に合わせる。
2. lint は actual EAST3 usage を見られるよう coverage roots を拡張する。
3. 以下の 3 分類で整理する。

- canonical key へ移行:
  - `py_len` -> `len`
  - `py_loads` -> `json.loads`
  - `py_loads_arr` -> `json.loads_arr`
  - `py_loads_obj` -> `json.loads_obj`
  - `py_dumps` -> `json.dumps`
  - `py_write_text` -> `Path.write_text`
- roots 外でも EAST3 usage があるため保持:
  - `open`
  - `py_float_from_str`
  - `std::runtime_error`
  - `pytra.std.math.pi`
  - `pytra.std.math.e`
- 現行 EAST3 usage がなく、C++ emitter も mapping 解決に依存しないため削除:
  - `bytearray_ctor`
  - `bytes_ctor`
  - `py_dumps_jv`
  - `py_floordiv`
  - `str.index`

## 検証

- `python3 tools/check/check_emitter_hardcode_lint.py --lang cpp --category rt:call_coverage`
- 必要に応じて `python3 tools/check/check_runtime_call_coverage.py --lang cpp --direction mapping-to-east`
