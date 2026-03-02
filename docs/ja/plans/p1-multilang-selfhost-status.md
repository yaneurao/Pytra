# P1-MQ-04 Stage1 Status

計測日: 2026-03-02

実行コマンド:

```bash
python3 tools/check_multilang_selfhost_stage1.py
```

| lang | stage1 (self-transpile) | generated_mode | stage2 (selfhost run) | note |
|---|---|---|---|---|
| rs | pass | native | fail | error[E0433]: failed to resolve: could not find `compiler` in `pytra` |
| cs | pass | native | fail | /tmp/tmpqj8hajx2/cs_selfhost_stage1.cs(1657,28): error CS1929: Type `System.Collections.Generic.Dictionary<string,object>' does not contain a member `Contains' and the best extension method overload `System.Linq.ParallelEnumerable.Contains<string>(this System.Linq.ParallelQuery<string>, string)' requires an instance of type `System.Linq.ParallelQuery<string>' |
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
