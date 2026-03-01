# P1-MQ-05 Multistage Selfhost Status

計測日: 2026-03-01

実行コマンド:

```bash
python3 tools/check_multilang_selfhost_multistage.py
```

| lang | stage1 (self-transpile) | stage2 (self->self) | stage3 (sample) | category | note |
|---|---|---|---|---|---|
| rs | pass | fail | skip | compile_fail | error[E0433]: failed to resolve: could not find `compiler` in `pytra` |
| cs | pass | pass | fail | stage2_compile_fail | /tmp/tmpmuc7ie_0/py2cs_stage2.cs(671,57): error CS1525: Unexpected symbol `base' |
| js | pass | fail | skip | stage1_dependency_transpile_fail | js multistage emit failed at hooks/js/emitter/js_emitter.py: raise _make_east_build_error( |
| ts | pass | skip | skip | runner_not_defined | multistage runner is not defined |
| go | pass | skip | skip | runner_not_defined | multistage runner is not defined |
| java | pass | skip | skip | runner_not_defined | multistage runner is not defined |
| swift | pass | skip | skip | runner_not_defined | multistage runner is not defined |
| kotlin | pass | skip | skip | runner_not_defined | multistage runner is not defined |

カテゴリ定義:
- `preview_only`: stage1 は可能だが生成 transpiler が preview 出力。
- `toolchain_missing`: stage2 実行に必要な実行系/コンパイラが無い。
- `compile_fail`: stage1 生成 transpiler のビルド失敗。
- `stage1_dependency_transpile_fail`: stage2 実行準備（依存 transpile）で失敗。
- `self_retranspile_fail`: 生成 transpiler で自己再変換（stage2）に失敗。
- `stage2_compile_fail`: stage2 生成 transpiler のビルド失敗。
- `sample_transpile_fail`: stage2 生成 transpiler で `sample/py/01` 変換に失敗。
- `stage1_transpile_fail`: stage1 自己変換自体が失敗。
