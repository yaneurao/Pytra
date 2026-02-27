# P1-MQ-05 Multistage Selfhost Status

計測日: 2026-02-24

実行コマンド:

```bash
python3 tools/check_multilang_selfhost_multistage.py
```

| lang | stage1 (self-transpile) | stage2 (self->self) | stage3 (sample) | category | note |
|---|---|---|---|---|---|
| rs | fail | skip | skip | stage1_transpile_fail | RuntimeError: unsupported_syntax: unsupported from-import clause: ( add_common_transpile_args at 9:0 hint=Use `from module import name` or `... as alias`. |
| cs | pass | blocked | blocked | toolchain_missing | mcs/mono not found |
| js | pass | fail | skip | stage1_dependency_transpile_fail | js multistage emit failed at hooks/js/emitter/js_emitter.py: RuntimeError: unsupported_syntax: object receiver attribute/method access is forbidden by language constraints at 73:39 hint=Cast or assign to a concrete type before attribute/method access. |
| ts | pass | blocked | blocked | preview_only | generated transpiler is preview-only |
| go | pass | blocked | blocked | preview_only | generated transpiler is preview-only |
| java | pass | blocked | blocked | preview_only | generated transpiler is preview-only |
| swift | pass | blocked | blocked | preview_only | generated transpiler is preview-only |
| kotlin | pass | blocked | blocked | preview_only | generated transpiler is preview-only |

カテゴリ定義:
- `preview_only`: stage1 は可能だが生成 transpiler が preview 出力。
- `toolchain_missing`: stage2 実行に必要な実行系/コンパイラが無い。
- `compile_fail`: stage1 生成 transpiler のビルド失敗。
- `stage1_dependency_transpile_fail`: stage2 実行準備（依存 transpile）で失敗。
- `self_retranspile_fail`: 生成 transpiler で自己再変換（stage2）に失敗。
- `stage2_compile_fail`: stage2 生成 transpiler のビルド失敗。
- `sample_transpile_fail`: stage2 生成 transpiler で `sample/py/01` 変換に失敗。
- `stage1_transpile_fail`: stage1 自己変換自体が失敗。
