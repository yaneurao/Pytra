# P4 C# Single-Source Selfhost Compile Status

計測日: 2026-03-01

実行コマンド:

```bash
python3 tools/check_cs_single_source_selfhost_compile.py
```

## Summary

- prepare: `python3 tools/prepare_selfhost_source_cs.py`
- transpile selfhost source: `rc=0`
- mcs compile: `rc=1`
- compile note: `/tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(7460,63): error CS1503: Argument `#3' cannot convert `object' expression to type `string'`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 20 |
| CS0021 | 3 |
| CS0029 | 18 |
| CS0030 | 4 |
| CS0119 | 3 |
| CS0150 | 1 |
| CS0173 | 4 |
| CS0246 | 1 |
| CS0266 | 26 |
| CS0411 | 1 |
| CS0815 | 3 |
| CS1502 | 29 |
| CS1503 | 42 |
| CS1729 | 1 |
| CS1929 | 1 |
| CS1950 | 13 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(448,21): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(456,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `bool?'
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(460,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `object'
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(475,13): error CS0029: Cannot implicitly convert type `System.Collections.Generic.Dictionary<string,object>' to `string'
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(483,20): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(496,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(505,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(514,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(523,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(532,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(541,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(557,18): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(560,51): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(561,40): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(568,31): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(569,31): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(584,23): error CS1502: The best overloaded method match for `System.Collections.Generic.List<string>.Add(string)' has some invalid arguments
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(584,27): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(606,21): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpx1wprm2p/cs_selfhost_full_stage1.cs(633,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)

