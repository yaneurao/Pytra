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
- compile note: `/tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(7725,63): error CS1503: Argument `#3' cannot convert `object' expression to type `string'`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 11 |
| CS0029 | 3 |
| CS0030 | 4 |
| CS0103 | 1 |
| CS0119 | 3 |
| CS0150 | 1 |
| CS0173 | 1 |
| CS0246 | 1 |
| CS0266 | 10 |
| CS0411 | 1 |
| CS1502 | 8 |
| CS1503 | 8 |
| CS1729 | 1 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(1600,140): error CS0411: The type arguments for method `System.Linq.ParallelEnumerable.Count<TSource>(this System.Linq.ParallelQuery<TSource>)' cannot be inferred from the usage. Try specifying the type arguments explicitly
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(1631,20): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(1635,24): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(1992,20): error CS0019: Operator `!=' cannot be applied to operands of type `object' and `int'
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(2015,34): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(2019,38): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(2869,51): error CS0266: Cannot implicitly convert type `object' to `System.Collections.Generic.Dictionary<string,object>'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(2922,120): error CS0173: Type of conditional expression cannot be determined because there is no implicit conversion between `System.Collections.Generic.Dictionary<string,object>' and `System.Collections.Generic.Dictionary<object,object>'
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(3047,12): error CS1729: The type `CodeEmitter' does not contain a constructor that takes `0' arguments
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(3961,25): error CS0019: Operator `+' cannot be applied to operands of type `System.Collections.Generic.List<object>' and `System.Collections.Generic.List<System.Collections.Generic.Dictionary<string,object>>'
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(4635,24): error CS0266: Cannot implicitly convert type `object' to `System.Collections.Generic.Dictionary<string,object>'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(4691,171): error CS0103: The name `v' does not exist in the current context
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(5404,41): error CS1502: The best overloaded method match for `CSharpEmitter._escape_interpolated_literal_text(string)' has some invalid arguments
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(5404,75): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(5514,32): error CS1502: The best overloaded method match for `CodeEmitter.hook_on_render_call(System.Collections.Generic.Dictionary<string,object>, System.Collections.Generic.Dictionary<string,object>, System.Collections.Generic.List<string>, System.Collections.Generic.Dictionary<string,string>)' has some invalid arguments
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(5514,194): error CS1503: Argument `#3' cannot convert `System.Collections.Generic.List<object>' expression to type `System.Collections.Generic.List<string>'
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(6247,90): error CS0030: Cannot convert type `System.Collections.Generic.Dictionary<string,System.Collections.Generic.List<string>>' to `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(6247,207): error CS0030: Cannot convert type `System.Collections.Generic.Dictionary<string,System.Collections.Generic.List<string>>' to `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(6267,47): error CS0019: Operator `>' cannot be applied to operands of type `string' and `string'
- /tmp/tmpcl2gdc3g/cs_selfhost_full_stage1.cs(6342,24): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)

