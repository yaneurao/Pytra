# P1-MQ-04 Stage1 Status

計測日: 2026-02-27

実行コマンド:

```bash
python3 tools/check_multilang_selfhost_stage1.py
```

| lang | stage1 (self-transpile) | generated_mode | stage2 (selfhost run) | note |
|---|---|---|---|---|
| rs | pass | native | fail | For more information about an error, try `rustc --explain E0061`. |
| cs | pass | native | fail | /tmp/tmpj3k9gov7/cs_selfhost_stage1.cs(83,22): error CS0103: The name `transpile_to_csharp' does not exist in the current context |
| js | pass | native | fail | js stage2 emit failed at hooks/js/emitter/js_emitter.py: RuntimeError: unsupported_syntax: object receiver attribute/method access is forbidden by language constraints at 90:39 hint=Cast or assign to a concrete type before attribute/method access. |
| ts | pass | preview | blocked | generated transpiler is preview-only |
| go | pass | native | skip | stage2 scope is rs/cs/js only |
| java | pass | native | skip | stage2 scope is rs/cs/js only |
| swift | pass | native | skip | stage2 scope is rs/cs/js only |
| kotlin | pass | native | skip | stage2 scope is rs/cs/js only |

備考:
- `stage1`: `src/py2<lang>.py` を同言語へ自己変換できるか。
- `generated_mode`: 生成物が preview かどうか。
- `stage2`: 生成された変換器で `sample/py/01_mandelbrot.py` を再変換できるか。
