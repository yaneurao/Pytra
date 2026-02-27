# P4 C# Single-Source Selfhost Compile Status

計測日: 2026-02-27

実行コマンド:

```bash
python3 tools/check_cs_single_source_selfhost_compile.py
```

## Summary

- prepare: `python3 tools/prepare_selfhost_source_cs.py`
- transpile selfhost source: `rc=0`
- mcs compile: `rc=1`
- compile note: `/tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(7898,13): error CS0815: An implicitly typed local variable declaration cannot be initialized with `method group'`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 14 |
| CS0029 | 18 |
| CS0103 | 36 |
| CS0119 | 3 |
| CS0120 | 5 |
| CS0122 | 8 |
| CS0173 | 5 |
| CS0246 | 1 |
| CS0266 | 34 |
| CS0815 | 5 |
| CS0841 | 2 |
| CS1061 | 20 |
| CS1501 | 6 |
| CS1502 | 34 |
| CS1503 | 48 |
| CS1579 | 4 |
| CS1729 | 1 |
| CS1929 | 2 |
| CS1950 | 14 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(31,19): error CS1502: The best overloaded method match for `System.Collections.Generic.Dictionary<string,object>.this[string]' has some invalid arguments
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(31,20): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(96,98): error CS1950: The best overloaded collection initalizer method `System.Collections.Generic.List<System.Collections.Generic.HashSet<string>>.Add(System.Collections.Generic.HashSet<string>)' has some invalid arguments
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(96,98): error CS1503: Argument `#1' cannot convert `System.Collections.Generic.HashSet<object>' expression to type `System.Collections.Generic.HashSet<string>'
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(134,32): error CS0120: An object reference is required to access non-static member `CodeEmitter.escape_string_for_literal(string)'
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(146,23): error CS0103: The name `json' does not exist in the current context
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(152,20): error CS0029: Cannot implicitly convert type `System.Collections.Generic.Dictionary<object,object>' to `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(176,40): error CS0120: An object reference is required to access non-static member `CodeEmitter._resolve_src_root(string)'
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(185,32): error CS0120: An object reference is required to access non-static member `CodeEmitter._load_json_dict(Pytra.CsModule.py_path)'
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(191,33): error CS1061: Type `System.Collections.Generic.Dictionary<string,object>' does not contain a definition for `get' and no extension method `get' of type `System.Collections.Generic.Dictionary<string,object>' could be found. Are you missing an assembly reference?
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(199,26): error CS1502: The best overloaded method match for `System.Collections.Generic.List<string>.Add(string)' has some invalid arguments
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(199,30): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(203,37): error CS0120: An object reference is required to access non-static member `CodeEmitter._load_json_dict(Pytra.CsModule.py_path)'
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(204,42): error CS1061: Type `System.Collections.Generic.Dictionary<string,object>' does not contain a definition for `items' and no extension method `items' of type `System.Collections.Generic.Dictionary<string,object>' could be found. Are you missing an assembly reference?
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(210,37): error CS1061: Type `System.Collections.Generic.Dictionary<string,object>' does not contain a definition for `items' and no extension method `items' of type `System.Collections.Generic.Dictionary<string,object>' could be found. Are you missing an assembly reference?
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(238,24): error CS0019: Operator `*' cannot be applied to operands of type `string' and `long'
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(342,34): error CS1061: Type `CodeEmitter' does not contain a definition for `class_field_owner_unique' and no extension method `class_field_owner_unique' of type `CodeEmitter' could be found. Are you missing an assembly reference?
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(343,36): error CS1061: Type `CodeEmitter' does not contain a definition for `class_method_owner_unique' and no extension method `class_method_owner_unique' of type `CodeEmitter' could be found. Are you missing an assembly reference?
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(344,37): error CS1929: Type `System.Collections.Generic.HashSet<string>' does not contain a member `Contains' and the best extension method overload `System.Linq.ParallelEnumerable.Contains<<error>>(this System.Linq.ParallelQuery<<error>>, <error>)' requires an instance of type `System.Linq.ParallelQuery<<error>>'
- /tmp/tmp9nzan76a/cs_selfhost_full_stage1.cs(372,13): error CS0266: Cannot implicitly convert type `object' to `string'. An explicit conversion exists (are you missing a cast?)

