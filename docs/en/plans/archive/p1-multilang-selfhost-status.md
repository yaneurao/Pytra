<a href="../../../ja/plans/archive/p1-multilang-selfhost-status.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1-MQ-04 Stage1 Status

Measurement date: 2026-03-13

Command:

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

Notes:
- `stage1`: whether `src/py2x.py --target <lang>` can self-transpile into the same language.
- `generated_mode`: whether the generated output is preview.
- `stage2`: whether the generated transpiler can re-transpile `sample/py/01_mandelbrot.py`.
