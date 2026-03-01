# P1-MQ-04 Stage1 Status

Measurement date: 2026-03-01

Command:

```bash
python3 tools/check_multilang_selfhost_stage1.py
```

| lang | stage1 (self-transpile) | generated_mode | stage2 (selfhost run) | note |
|---|---|---|---|---|
| rs | pass | native | fail | error[E0433]: failed to resolve: could not find `compiler` in `pytra` |
| cs | pass | native | pass | sample/py/01 transpile ok |
| js | pass | native | fail | js stage2 emit failed at hooks/js/emitter/js_emitter.py: raise _make_east_build_error( |
| ts | pass | native | skip | stage2 scope is rs/cs/js only |
| go | pass | native | skip | stage2 scope is rs/cs/js only |
| java | pass | native | skip | stage2 scope is rs/cs/js only |
| swift | pass | native | skip | stage2 scope is rs/cs/js only |
| kotlin | pass | native | skip | stage2 scope is rs/cs/js only |

Notes:
- `stage1`: whether `src/py2<lang>.py` can self-transpile into the same language.
- `generated_mode`: whether the generated output is preview.
- `stage2`: whether the generated transpiler can re-transpile `sample/py/01_mandelbrot.py`.
