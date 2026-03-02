# P1-MQ-04 Stage1 Status

計測日: 2026-03-02

実行コマンド:

```bash
python3 tools/check_multilang_selfhost_stage1.py
```

| lang | stage1 (self-transpile) | generated_mode | stage2 (selfhost run) | note |
|---|---|---|---|---|
| rs | pass | native | fail | error[E0433]: failed to resolve: could not find `compiler` in `pytra` |
| cs | pass | native | fail | /tmp/tmp4j3gy4_i/cs_selfhost_stage1.cs(602,18): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string' |
| js | pass | native | pass | sample/py/01 transpile ok |
| ts | pass | native | skip | stage2 scope is rs/cs/js only |
| go | pass | native | skip | stage2 scope is rs/cs/js only |
| java | pass | native | skip | stage2 scope is rs/cs/js only |
| swift | pass | native | skip | stage2 scope is rs/cs/js only |
| kotlin | pass | native | skip | stage2 scope is rs/cs/js only |

備考:
- `stage1`: `src/py2<lang>.py` を同言語へ自己変換できるか。
- `generated_mode`: 生成物が preview かどうか。
- `stage2`: 生成された変換器で `sample/py/01_mandelbrot.py` を再変換できるか。
