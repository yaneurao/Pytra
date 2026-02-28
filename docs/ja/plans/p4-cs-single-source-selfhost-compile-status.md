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
- compile note: `/tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(8157,52): error CS1503: Argument `#1' cannot convert `System.Collections.Generic.Dictionary<string,string>' expression to type `System.Collections.Generic.Dictionary<string,object>'`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 22 |
| CS0021 | 3 |
| CS0029 | 18 |
| CS0030 | 4 |
| CS0119 | 3 |
| CS0173 | 5 |
| CS0246 | 1 |
| CS0266 | 34 |
| CS0411 | 1 |
| CS0815 | 3 |
| CS0841 | 2 |
| CS1502 | 46 |
| CS1503 | 60 |
| CS1579 | 6 |
| CS1729 | 1 |
| CS1929 | 1 |
| CS1950 | 14 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(31,19): error CS1502: The best overloaded method match for `System.Collections.Generic.Dictionary<string,object>.this[string]' has some invalid arguments
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(31,20): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(100,98): error CS1950: The best overloaded collection initalizer method `System.Collections.Generic.List<System.Collections.Generic.HashSet<string>>.Add(System.Collections.Generic.HashSet<string>)' has some invalid arguments
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(100,98): error CS1503: Argument `#1' cannot convert `System.Collections.Generic.HashSet<object>' expression to type `System.Collections.Generic.HashSet<string>'
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(199,28): error CS0266: Cannot implicitly convert type `object' to `System.Collections.Generic.List<object>'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(203,26): error CS1502: The best overloaded method match for `System.Collections.Generic.List<string>.Add(string)' has some invalid arguments
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(203,30): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(242,24): error CS0019: Operator `*' cannot be applied to operands of type `string' and `long'
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(376,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(377,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(378,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(379,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(380,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(381,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(382,13): error CS0029: Cannot implicitly convert type `long' to `string'
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(420,21): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(428,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `bool?'
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(432,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `object'
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(447,13): error CS0029: Cannot implicitly convert type `System.Collections.Generic.Dictionary<string,object>' to `string'
- /tmp/tmpj_1e9dzq/cs_selfhost_full_stage1.cs(455,20): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)

