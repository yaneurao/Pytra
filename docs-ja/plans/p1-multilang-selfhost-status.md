# P1-MQ-04 Stage1 Status

計測日: 2026-02-24

実行コマンド:

```bash
python3 tools/check_multilang_selfhost_stage1.py
```

| lang | stage1 (self-transpile) | generated_mode | stage2 (selfhost run) | note |
|---|---|---|---|---|
| rs | fail | unknown | skip | RuntimeError: unsupported_syntax: unsupported from-import clause: ( add_common_transpile_args at 9:0 hint=Use `from module import name` or `... as alias`. |
| cs | pass | native | skip | stage2 runner not automated |
| js | pass | native | fail | SyntaxError: Unexpected token ']' |
| ts | pass | preview | blocked | generated transpiler is preview-only |
| go | pass | preview | blocked | generated transpiler is preview-only |
| java | pass | preview | blocked | generated transpiler is preview-only |
| swift | pass | preview | blocked | generated transpiler is preview-only |
| kotlin | pass | preview | blocked | generated transpiler is preview-only |

備考:
- `stage1`: `src/py2<lang>.py` を同言語へ自己変換できるか。
- `generated_mode`: 生成物が preview かどうか。
- `stage2`: 生成された変換器で `sample/py/01_mandelbrot.py` を再変換できるか。
