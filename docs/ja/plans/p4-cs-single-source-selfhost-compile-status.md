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
- compile note: `/tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(7194,34): error CS1579: foreach statement cannot operate on variables of type `object' because it does not contain a definition for `GetEnumerator' or is inaccessible`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 22 |
| CS0021 | 3 |
| CS0029 | 16 |
| CS0030 | 4 |
| CS0119 | 3 |
| CS0173 | 4 |
| CS0266 | 27 |
| CS0411 | 1 |
| CS0815 | 3 |
| CS1502 | 26 |
| CS1503 | 39 |
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

- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(200,28): error CS0266: Cannot implicitly convert type `object' to `System.Collections.Generic.List<object>'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(204,26): error CS1502: The best overloaded method match for `System.Collections.Generic.List<string>.Add(string)' has some invalid arguments
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(204,30): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(243,24): error CS0019: Operator `*' cannot be applied to operands of type `string' and `long'
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(413,21): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(421,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `bool?'
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(425,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `object'
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(440,13): error CS0029: Cannot implicitly convert type `System.Collections.Generic.Dictionary<string,object>' to `string'
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(448,20): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(461,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(470,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(479,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(488,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(497,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(506,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(522,18): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(525,51): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(526,40): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(533,31): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmp6e6o2o8t/cs_selfhost_full_stage1.cs(534,31): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'

