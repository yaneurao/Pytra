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
- compile note: `/tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(7400,34): error CS1579: foreach statement cannot operate on variables of type `object' because it does not contain a definition for `GetEnumerator' or is inaccessible`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 22 |
| CS0021 | 3 |
| CS0029 | 18 |
| CS0030 | 4 |
| CS0103 | 1 |
| CS0119 | 3 |
| CS0150 | 1 |
| CS0173 | 4 |
| CS0246 | 1 |
| CS0266 | 26 |
| CS0411 | 1 |
| CS0815 | 3 |
| CS1502 | 26 |
| CS1503 | 39 |
| CS1579 | 7 |
| CS1729 | 1 |
| CS1929 | 1 |
| CS1950 | 13 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(126,14): error CS1502: The best overloaded method match for `CodeEmitter.require_dep(string)' has some invalid arguments
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(126,26): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(139,20): error CS0103: The name `sorted' does not exist in the current context
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(274,24): error CS0019: Operator `*' cannot be applied to operands of type `string' and `long'
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(444,21): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(452,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `bool?'
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(456,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `object'
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(471,13): error CS0029: Cannot implicitly convert type `System.Collections.Generic.Dictionary<string,object>' to `string'
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(479,20): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(492,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(501,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(510,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(519,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(528,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(537,20): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(553,18): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(556,51): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(557,40): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(564,31): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpepv6vue9/cs_selfhost_full_stage1.cs(565,31): error CS0019: Operator `<=' cannot be applied to operands of type `string' and `string'

