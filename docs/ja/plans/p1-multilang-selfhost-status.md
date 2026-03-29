<a href="../../en/plans/p1-multilang-selfhost-status.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-MQ-04 Stage1 Status

計測日: 2026-03-18

実行コマンド:

```bash
python3 tools/check/check_multilang_selfhost_stage1.py
```

| lang | stage1 (self-transpile) | generated_mode | stage2 (selfhost run) | note |
|---|---|---|---|---|
| rs | fail | unknown | skip | raise self._raise_expr_build_error( |
| cs | fail | unknown | skip | raise self._raise_expr_build_error( |
| js | fail | unknown | skip | raise self._raise_expr_build_error( |
| ts | fail | unknown | skip | raise self._raise_expr_build_error( |
| go | fail | unknown | skip | raise self._raise_expr_build_error( |
| java | fail | unknown | skip | raise self._raise_expr_build_error( |
| swift | fail | unknown | skip | raise self._raise_expr_build_error( |
| kotlin | fail | unknown | skip | raise self._raise_expr_build_error( |

備考:
- `stage1`: `src/pytra-cli.py --target <lang>` を同言語へ自己変換できるか。
- `generated_mode`: 生成物が preview かどうか。
- `stage2`: 生成された変換器で `sample/py/01_mandelbrot.py` を再変換できるか。
