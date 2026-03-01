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
- compile note: `/tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(7046,20): error CS0019: Operator `>=' cannot be applied to operands of type `char' and `string'`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 11 |
| CS0030 | 2 |
| CS0103 | 1 |
| CS0173 | 1 |
| CS0411 | 1 |
| CS1729 | 1 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(1600,140): error CS0411: The type arguments for method `System.Linq.ParallelEnumerable.Count<TSource>(this System.Linq.ParallelQuery<TSource>)' cannot be inferred from the usage. Try specifying the type arguments explicitly
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(1631,20): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(1635,24): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(1992,20): error CS0019: Operator `!=' cannot be applied to operands of type `object' and `int'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(2015,34): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(2019,38): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(2924,120): error CS0173: Type of conditional expression cannot be determined because there is no implicit conversion between `System.Collections.Generic.Dictionary<string,object>' and `System.Collections.Generic.Dictionary<object,object>'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(3049,12): error CS1729: The type `CodeEmitter' does not contain a constructor that takes `0' arguments
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(3967,25): error CS0019: Operator `+' cannot be applied to operands of type `System.Collections.Generic.List<object>' and `System.Collections.Generic.List<System.Collections.Generic.Dictionary<string,object>>'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(4698,171): error CS0103: The name `v' does not exist in the current context
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(6254,90): error CS0030: Cannot convert type `System.Collections.Generic.Dictionary<string,System.Collections.Generic.List<string>>' to `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(6254,207): error CS0030: Cannot convert type `System.Collections.Generic.Dictionary<string,System.Collections.Generic.List<string>>' to `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(6274,47): error CS0019: Operator `>' cannot be applied to operands of type `string' and `string'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(6868,113): error CS0019: Operator `==' cannot be applied to operands of type `object' and `int'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(6875,112): error CS0019: Operator `>' cannot be applied to operands of type `object' and `int'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(6895,115): error CS0019: Operator `==' cannot be applied to operands of type `object' and `int'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(6911,21): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `object'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(7037,27): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmp9l6hdud1/cs_selfhost_full_stage1.cs(7046,20): error CS0019: Operator `>=' cannot be applied to operands of type `char' and `string'

