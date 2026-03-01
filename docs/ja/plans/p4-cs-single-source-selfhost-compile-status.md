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
- compile note: `/tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(7518,63): error CS1503: Argument `#3' cannot convert `object' expression to type `string'`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 11 |
| CS0021 | 3 |
| CS0029 | 17 |
| CS0030 | 4 |
| CS0119 | 3 |
| CS0150 | 1 |
| CS0173 | 1 |
| CS0246 | 1 |
| CS0266 | 9 |
| CS0411 | 1 |
| CS0815 | 3 |
| CS1502 | 27 |
| CS1503 | 40 |
| CS1729 | 1 |
| CS1929 | 1 |
| CS1950 | 13 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1172,32): error CS0021: Cannot apply indexing with [] to an expression of type `object'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1173,27): error CS1502: The best overloaded method match for `System.Collections.Generic.Dictionary<string,object>.this[string]' has some invalid arguments
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1173,28): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1187,32): error CS0021: Cannot apply indexing with [] to an expression of type `object'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1188,27): error CS1502: The best overloaded method match for `System.Collections.Generic.Dictionary<string,object>.this[string]' has some invalid arguments
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1188,28): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1330,66): error CS1502: The best overloaded method match for `CodeEmitter.fallback_tuple_target_names_from_repr(System.Collections.Generic.Dictionary<string,object>)' has some invalid arguments
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1330,104): error CS1503: Argument `#1' cannot convert `System.Collections.Generic.Dictionary<string,string>' expression to type `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1416,13): error CS0815: An implicitly typed local variable declaration cannot be initialized with `null'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1585,140): error CS0411: The type arguments for method `System.Linq.ParallelEnumerable.Count<TSource>(this System.Linq.ParallelQuery<TSource>)' cannot be inferred from the usage. Try specifying the type arguments explicitly
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1616,20): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1620,24): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(1977,20): error CS0019: Operator `!=' cannot be applied to operands of type `object' and `int'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(2000,34): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(2004,38): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(2212,63): error CS1502: The best overloaded method match for `CodeEmitter.any_dict_get_str(System.Collections.Generic.Dictionary<string,object>, string, string)' has some invalid arguments
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(2212,80): error CS1503: Argument `#1' cannot convert `object' expression to type `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(2212,105): error CS1502: The best overloaded method match for `CodeEmitter.any_dict_get_str(System.Collections.Generic.Dictionary<string,object>, string, string)' has some invalid arguments
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(2212,122): error CS1503: Argument `#1' cannot convert `object' expression to type `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmpqmcg2s66/cs_selfhost_full_stage1.cs(2240,55): error CS1502: The best overloaded method match for `CodeEmitter.any_dict_get_str(System.Collections.Generic.Dictionary<string,object>, string, string)' has some invalid arguments

