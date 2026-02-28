# P4 C# Single-Source Selfhost Compile Status

計測日: 2026-02-28

実行コマンド:

```bash
python3 tools/check_cs_single_source_selfhost_compile.py
```

## Summary

- prepare: `python3 tools/prepare_selfhost_source_cs.py`
- transpile selfhost source: `rc=0`
- mcs compile: `rc=1`
- compile note: `/tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(7914,13): error CS0029: Cannot implicitly convert type `string' to `Pytra.CsModule.py_path'`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 22 |
| CS0021 | 3 |
| CS0029 | 18 |
| CS0030 | 4 |
| CS0119 | 3 |
| CS0173 | 4 |
| CS0246 | 1 |
| CS0266 | 33 |
| CS0411 | 1 |
| CS0815 | 3 |
| CS0841 | 2 |
| CS1502 | 33 |
| CS1503 | 46 |
| CS1579 | 6 |
| CS1729 | 1 |
| CS1929 | 1 |
| CS1950 | 13 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(200,28): error CS0266: Cannot implicitly convert type `object' to `System.Collections.Generic.List<object>'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(204,26): error CS1502: The best overloaded method match for `System.Collections.Generic.List<string>.Add(string)' has some invalid arguments
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(204,30): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(243,24): error CS0019: Operator `*' cannot be applied to operands of type `string' and `long'
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(377,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(378,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(379,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(380,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(381,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(382,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(383,13): error CS0029: Cannot implicitly convert type `long' to `string'
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(421,21): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(429,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `bool?'
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(433,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `object'
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(448,13): error CS0029: Cannot implicitly convert type `System.Collections.Generic.Dictionary<string,object>' to `string'
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(456,20): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(469,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(478,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(487,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp2o527d0h/cs_selfhost_full_stage1.cs(496,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)

