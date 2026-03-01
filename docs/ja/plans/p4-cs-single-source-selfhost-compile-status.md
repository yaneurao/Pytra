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
- compile note: `/tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(7602,30): error CS0119: Expression denotes a `variable', where a `method group' was expected`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 11 |
| CS0021 | 1 |
| CS0029 | 3 |
| CS0030 | 4 |
| CS0103 | 1 |
| CS0119 | 3 |
| CS0150 | 1 |
| CS0173 | 1 |
| CS0246 | 1 |
| CS0266 | 7 |
| CS0411 | 1 |
| CS1502 | 2 |
| CS1503 | 2 |
| CS1729 | 1 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(1600,140): error CS0411: The type arguments for method `System.Linq.ParallelEnumerable.Count<TSource>(this System.Linq.ParallelQuery<TSource>)' cannot be inferred from the usage. Try specifying the type arguments explicitly
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(1631,20): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(1635,24): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(1992,20): error CS0019: Operator `!=' cannot be applied to operands of type `object' and `int'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(2015,34): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(2019,38): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(2869,51): error CS0266: Cannot implicitly convert type `object' to `System.Collections.Generic.Dictionary<string,object>'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(2922,120): error CS0173: Type of conditional expression cannot be determined because there is no implicit conversion between `System.Collections.Generic.Dictionary<string,object>' and `System.Collections.Generic.Dictionary<object,object>'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(3047,12): error CS1729: The type `CodeEmitter' does not contain a constructor that takes `0' arguments
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(3965,25): error CS0019: Operator `+' cannot be applied to operands of type `System.Collections.Generic.List<object>' and `System.Collections.Generic.List<System.Collections.Generic.Dictionary<string,object>>'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(4639,24): error CS0266: Cannot implicitly convert type `object' to `System.Collections.Generic.Dictionary<string,object>'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(4695,171): error CS0103: The name `v' does not exist in the current context
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(6251,90): error CS0030: Cannot convert type `System.Collections.Generic.Dictionary<string,System.Collections.Generic.List<string>>' to `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(6251,207): error CS0030: Cannot convert type `System.Collections.Generic.Dictionary<string,System.Collections.Generic.List<string>>' to `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(6271,47): error CS0019: Operator `>' cannot be applied to operands of type `string' and `string'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(6378,44): error CS0021: Cannot apply indexing with [] to an expression of type `object'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(6378,27): error CS1502: The best overloaded method match for `System.Collections.Generic.Dictionary<string,object>.this[string]' has some invalid arguments
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(6378,28): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(6870,113): error CS0019: Operator `==' cannot be applied to operands of type `object' and `int'
- /tmp/tmpaaep8o37/cs_selfhost_full_stage1.cs(6871,21): error CS0266: Cannot implicitly convert type `object' to `long'. An explicit conversion exists (are you missing a cast?)

