<a href="../../../en/plans/archive/p1-multilang-selfhost-multistage-status.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1-MQ-05 Multistage Selfhost Status

計測日: 2026-03-13

実行コマンド:

```bash
python3 tools/check/check_multilang_selfhost_multistage.py
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

カテゴリ定義:
- `preview_only`: stage1 は可能だが生成 transpiler が preview 出力。
- `toolchain_missing`: stage2 実行に必要な実行系/コンパイラが無い。
- `compile_fail`: stage1 生成 transpiler のビルド失敗。
- `stage1_dependency_transpile_fail`: stage2 実行準備（依存 transpile）で失敗。
- `self_retranspile_fail`: 生成 transpiler で自己再変換（stage2）に失敗。
- `stage2_compile_fail`: stage2 生成 transpiler のビルド失敗。
- `sample_transpile_fail`: stage2 生成 transpiler で `sample/py/01` 変換に失敗。
- `stage1_transpile_fail`: stage1 自己変換自体が失敗。
- `unsupported_by_design`: 現在の multistage runner 対象外で expected failure として扱う。
