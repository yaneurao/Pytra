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
- compile note: `/tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(7185,34): error CS1579: foreach statement cannot operate on variables of type `object' because it does not contain a definition for `GetEnumerator' or is inaccessible`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 22 |
| CS0021 | 3 |
| CS0029 | 16 |
| CS0030 | 4 |
| CS0119 | 3 |
| CS0173 | 4 |
| CS0266 | 26 |
| CS0411 | 1 |
| CS0815 | 3 |
| CS1502 | 25 |
| CS1503 | 38 |
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

- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(234,24): error CS0019: Operator `*' cannot be applied to operands of type `string' and `long'
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(404,21): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(412,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `bool?'
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(416,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `object'
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(431,13): error CS0029: Cannot implicitly convert type `System.Collections.Generic.Dictionary<string,object>' to `string'
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(439,20): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(452,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(461,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(470,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(479,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(488,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(497,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(513,18): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(516,51): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(517,40): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(524,31): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(525,31): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(537,18): error CS0019: Operator `==' cannot be applied to operands of type `char' and `string'
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(540,23): error CS1502: The best overloaded method match for `System.Collections.Generic.List<string>.Add(string)' has some invalid arguments
- /tmp/tmpqwq8jurl/cs_selfhost_full_stage1.cs(540,27): error CS1503: Argument `#1' cannot convert `char' expression to type `string'

