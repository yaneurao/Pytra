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
- compile note: `/tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(7650,63): error CS1503: Argument `#3' cannot convert `object' expression to type `string'`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 11 |
| CS0021 | 1 |
| CS0029 | 16 |
| CS0030 | 4 |
| CS0119 | 3 |
| CS0150 | 1 |
| CS0173 | 1 |
| CS0246 | 1 |
| CS0266 | 10 |
| CS0411 | 1 |
| CS1502 | 18 |
| CS1503 | 18 |
| CS1729 | 1 |
| CS1929 | 1 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(1575,140): error CS0411: The type arguments for method `System.Linq.ParallelEnumerable.Count<TSource>(this System.Linq.ParallelQuery<TSource>)' cannot be inferred from the usage. Try specifying the type arguments explicitly
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(1606,20): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(1610,24): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(1967,20): error CS0019: Operator `!=' cannot be applied to operands of type `object' and `int'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(1990,34): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(1994,38): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(2844,51): error CS0266: Cannot implicitly convert type `object' to `System.Collections.Generic.Dictionary<string,object>'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(2897,120): error CS0173: Type of conditional expression cannot be determined because there is no implicit conversion between `System.Collections.Generic.Dictionary<string,object>' and `System.Collections.Generic.Dictionary<object,object>'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(3022,12): error CS1729: The type `CodeEmitter' does not contain a constructor that takes `0' arguments
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(3035,31): error CS0029: Cannot implicitly convert type `System.Collections.Generic.HashSet<object>' to `System.Collections.Generic.HashSet<string>'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(3040,35): error CS0029: Cannot implicitly convert type `System.Collections.Generic.Dictionary<object,object>' to `System.Collections.Generic.Dictionary<string,string>'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(3041,28): error CS0029: Cannot implicitly convert type `System.Collections.Generic.HashSet<object>' to `System.Collections.Generic.HashSet<string>'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(3042,31): error CS0029: Cannot implicitly convert type `System.Collections.Generic.Dictionary<object,object>' to `System.Collections.Generic.Dictionary<string,string>'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(3044,42): error CS0029: Cannot implicitly convert type `System.Collections.Generic.Dictionary<object,object>' to `System.Collections.Generic.Dictionary<string,string>'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(3049,35): error CS0029: Cannot implicitly convert type `System.Collections.Generic.HashSet<object>' to `System.Collections.Generic.HashSet<string>'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(3087,21): error CS1502: The best overloaded method match for `CodeEmitter.rename_if_reserved(string, System.Collections.Generic.HashSet<string>, string, System.Collections.Generic.Dictionary<string,string>)' has some invalid arguments
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(3087,87): error CS1503: Argument `#4' cannot convert `System.Collections.Generic.Dictionary<object,object>' expression to type `System.Collections.Generic.Dictionary<string,string>'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(3348,29): error CS1929: Type `object' does not contain a member `Contains' and the best extension method overload `System.Linq.ParallelEnumerable.Contains<string>(this System.Linq.ParallelQuery<string>, string)' requires an instance of type `System.Linq.ParallelQuery<string>'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(3349,39): error CS0021: Cannot apply indexing with [] to an expression of type `object'
- /tmp/tmprypqmpub/cs_selfhost_full_stage1.cs(3695,25): error CS1502: The best overloaded method match for `CodeEmitter.quote_string_literal(string, string)' has some invalid arguments

