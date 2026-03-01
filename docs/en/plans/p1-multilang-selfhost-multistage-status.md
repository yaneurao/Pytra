# P1-MQ-05 Multistage Selfhost Status

Measurement date: 2026-03-01

Command:

```bash
python3 tools/check_multilang_selfhost_multistage.py
```

| lang | stage1 (self-transpile) | stage2 (self->self) | stage3 (sample) | category | note |
|---|---|---|---|---|---|
| rs | pass | fail | skip | compile_fail | error[E0433]: failed to resolve: could not find `compiler` in `pytra` |
| cs | pass | pass | pass | pass | stage2/stage3 sample transpile ok |
| js | pass | fail | skip | stage1_dependency_transpile_fail | js multistage emit failed at hooks/js/emitter/js_emitter.py: raise _make_east_build_error( |
| ts | pass | skip | skip | runner_not_defined | multistage runner is not defined |
| go | pass | skip | skip | runner_not_defined | multistage runner is not defined |
| java | pass | skip | skip | runner_not_defined | multistage runner is not defined |
| swift | pass | skip | skip | runner_not_defined | multistage runner is not defined |
| kotlin | pass | skip | skip | runner_not_defined | multistage runner is not defined |

Category definitions:
- `preview_only`: stage1 is possible, but the generated transpiler is preview output.
- `toolchain_missing`: runtime/compiler required for stage2 execution is unavailable.
- `compile_fail`: build failure of the stage1-generated transpiler.
- `stage1_dependency_transpile_fail`: failure during stage2 preparation (dependency transpile).
- `self_retranspile_fail`: self-retranspile (stage2) failed using the generated transpiler.
- `stage2_compile_fail`: build failure of the stage2-generated transpiler.
- `sample_transpile_fail`: stage2-generated transpiler failed to transpile `sample/py/01`.
- `stage1_transpile_fail`: stage1 self-transpile itself failed.
