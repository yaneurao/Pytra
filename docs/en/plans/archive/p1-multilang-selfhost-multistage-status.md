<a href="../../../ja/plans/archive/p1-multilang-selfhost-multistage-status.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1-MQ-05 Multistage Selfhost Status

Measurement date: 2026-03-13

Command:

```bash
python3 tools/check_multilang_selfhost_multistage.py
```

| lang | stage1 (self-transpile) | stage2 (self->self) | stage3 (sample) | category | note |
|---|---|---|---|---|---|
| rs | fail | skip | skip | stage1_transpile_fail | raise self._raise_expr_build_error( |
| cs | fail | skip | skip | stage1_transpile_fail | raise self._raise_expr_build_error( |
| js | fail | skip | skip | stage1_transpile_fail | raise self._raise_expr_build_error( |
| ts | fail | skip | skip | stage1_transpile_fail | raise self._raise_expr_build_error( |
| go | fail | skip | skip | stage1_transpile_fail | raise self._raise_expr_build_error( |
| java | fail | skip | skip | stage1_transpile_fail | raise self._raise_expr_build_error( |
| swift | fail | skip | skip | stage1_transpile_fail | raise self._raise_expr_build_error( |
| kotlin | fail | skip | skip | stage1_transpile_fail | raise self._raise_expr_build_error( |

Category definitions:
- `preview_only`: stage1 is possible, but the generated transpiler is preview output.
- `toolchain_missing`: runtime/compiler required for stage2 execution is unavailable.
- `compile_fail`: build failure of the stage1-generated transpiler.
- `stage1_dependency_transpile_fail`: failure during stage2 preparation (dependency transpile).
- `self_retranspile_fail`: self-retranspile (stage2) failed using the generated transpiler.
- `stage2_compile_fail`: build failure of the stage2-generated transpiler.
- `sample_transpile_fail`: stage2-generated transpiler failed to transpile `sample/py/01`.
- `stage1_transpile_fail`: stage1 self-transpile itself failed.
- `unsupported_by_design`: the current multistage runner intentionally treats this lane as an expected failure.
