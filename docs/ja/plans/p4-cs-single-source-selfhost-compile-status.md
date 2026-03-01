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
- compile note: `/tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(7522,63): error CS1503: Argument `#3' cannot convert `object' expression to type `string'`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 11 |
| CS0021 | 1 |
| CS0029 | 17 |
| CS0030 | 4 |
| CS0119 | 3 |
| CS0150 | 1 |
| CS0173 | 1 |
| CS0246 | 1 |
| CS0266 | 9 |
| CS0411 | 1 |
| CS0815 | 3 |
| CS1502 | 26 |
| CS1503 | 39 |
| CS1729 | 1 |
| CS1929 | 1 |
| CS1950 | 13 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(1169,76): error CS1502: The best overloaded method match for `System.Collections.Generic.Dictionary<string,object>.Dictionary(int)' has some invalid arguments
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(1169,134): error CS1503: Argument `#1' cannot convert `object' expression to type `int'
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(1186,76): error CS1502: The best overloaded method match for `System.Collections.Generic.Dictionary<string,object>.Dictionary(int)' has some invalid arguments
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(1186,134): error CS1503: Argument `#1' cannot convert `object' expression to type `int'
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(1420,13): error CS0815: An implicitly typed local variable declaration cannot be initialized with `null'
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(1589,140): error CS0411: The type arguments for method `System.Linq.ParallelEnumerable.Count<TSource>(this System.Linq.ParallelQuery<TSource>)' cannot be inferred from the usage. Try specifying the type arguments explicitly
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(1620,20): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(1624,24): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(1981,20): error CS0019: Operator `!=' cannot be applied to operands of type `object' and `int'
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(2004,34): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(2008,38): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(2216,63): error CS1502: The best overloaded method match for `CodeEmitter.any_dict_get_str(System.Collections.Generic.Dictionary<string,object>, string, string)' has some invalid arguments
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(2216,80): error CS1503: Argument `#1' cannot convert `object' expression to type `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(2216,105): error CS1502: The best overloaded method match for `CodeEmitter.any_dict_get_str(System.Collections.Generic.Dictionary<string,object>, string, string)' has some invalid arguments
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(2216,122): error CS1503: Argument `#1' cannot convert `object' expression to type `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(2244,55): error CS1502: The best overloaded method match for `CodeEmitter.any_dict_get_str(System.Collections.Generic.Dictionary<string,object>, string, string)' has some invalid arguments
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(2244,72): error CS1503: Argument `#1' cannot convert `object' expression to type `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(2244,97): error CS1502: The best overloaded method match for `CodeEmitter.any_dict_get_str(System.Collections.Generic.Dictionary<string,object>, string, string)' has some invalid arguments
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(2244,114): error CS1503: Argument `#1' cannot convert `object' expression to type `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmp5t_za2zg/cs_selfhost_full_stage1.cs(2858,51): error CS0266: Cannot implicitly convert type `object' to `System.Collections.Generic.Dictionary<string,object>'. An explicit conversion exists (are you missing a cast?)

