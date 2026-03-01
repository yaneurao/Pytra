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
- compile note: `/tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(7706,63): error CS1503: Argument `#3' cannot convert `object' expression to type `string'`

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
| CS1502 | 11 |
| CS1503 | 11 |
| CS1729 | 1 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(1581,140): error CS0411: The type arguments for method `System.Linq.ParallelEnumerable.Count<TSource>(this System.Linq.ParallelQuery<TSource>)' cannot be inferred from the usage. Try specifying the type arguments explicitly
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(1612,20): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(1616,24): error CS8135: Tuple literal `(System.Collections.Generic.List<object>, bool)' cannot be converted to type `(System.Collections.Generic.List<string>, bool)'
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(1973,20): error CS0019: Operator `!=' cannot be applied to operands of type `object' and `int'
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(1996,34): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(2000,38): error CS0019: Operator `>=' cannot be applied to operands of type `string' and `string'
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(2850,51): error CS0266: Cannot implicitly convert type `object' to `System.Collections.Generic.Dictionary<string,object>'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(2903,120): error CS0173: Type of conditional expression cannot be determined because there is no implicit conversion between `System.Collections.Generic.Dictionary<string,object>' and `System.Collections.Generic.Dictionary<object,object>'
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(3028,12): error CS1729: The type `CodeEmitter' does not contain a constructor that takes `0' arguments
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(3942,25): error CS0019: Operator `+' cannot be applied to operands of type `System.Collections.Generic.List<object>' and `System.Collections.Generic.List<System.Collections.Generic.Dictionary<string,object>>'
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(4420,14): error CS1502: The best overloaded method match for `CodeEmitter.emit_scoped_stmt_list(System.Collections.Generic.List<System.Collections.Generic.Dictionary<string,object>>, System.Collections.Generic.HashSet<string>)' has some invalid arguments
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(4420,161): error CS1503: Argument `#2' cannot convert `System.Collections.Generic.HashSet<object>' expression to type `System.Collections.Generic.HashSet<string>'
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(4463,18): error CS1502: The best overloaded method match for `CodeEmitter.emit_scoped_stmt_list(System.Collections.Generic.List<System.Collections.Generic.Dictionary<string,object>>, System.Collections.Generic.HashSet<string>)' has some invalid arguments
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(4463,51): error CS1503: Argument `#2' cannot convert `System.Collections.Generic.HashSet<object>' expression to type `System.Collections.Generic.HashSet<string>'
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(4535,14): error CS1502: The best overloaded method match for `CodeEmitter.emit_scoped_block(string, System.Collections.Generic.List<System.Collections.Generic.Dictionary<string,object>>, System.Collections.Generic.HashSet<string>)' has some invalid arguments
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(4535,126): error CS1503: Argument `#3' cannot convert `System.Collections.Generic.HashSet<object>' expression to type `System.Collections.Generic.HashSet<string>'
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(4616,24): error CS0266: Cannot implicitly convert type `object' to `System.Collections.Generic.Dictionary<string,object>'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(4672,171): error CS0103: The name `v' does not exist in the current context
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(5385,41): error CS1502: The best overloaded method match for `CSharpEmitter._escape_interpolated_literal_text(string)' has some invalid arguments
- /tmp/tmpupjd56qp/cs_selfhost_full_stage1.cs(5385,75): error CS1503: Argument `#1' cannot convert `object' expression to type `string'

