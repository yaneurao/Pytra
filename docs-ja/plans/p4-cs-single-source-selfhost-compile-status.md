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
- compile note: `/tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(7761,13): error CS0815: An implicitly typed local variable declaration cannot be initialized with `method group'`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 37 |
| CS0029 | 18 |
| CS0103 | 81 |
| CS0119 | 3 |
| CS0120 | 5 |
| CS0122 | 8 |
| CS0173 | 2 |
| CS0246 | 1 |
| CS0266 | 34 |
| CS0815 | 5 |
| CS0841 | 2 |
| CS1061 | 109 |
| CS1501 | 6 |
| CS1502 | 32 |
| CS1503 | 45 |
| CS1579 | 4 |
| CS1729 | 1 |
| CS1929 | 2 |
| CS1950 | 13 |
| CS8135 | 2 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(31,19): error CS1502: The best overloaded method match for `System.Collections.Generic.Dictionary<string,object>.this[string]' has some invalid arguments
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(31,20): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(79,38): error CS0103: The name `set' does not exist in the current context
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(81,44): error CS0103: The name `set' does not exist in the current context
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(82,27): error CS0029: Cannot implicitly convert type `System.Collections.Generic.Dictionary<object,object>' to `System.Collections.Generic.Dictionary<string,string>'
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(85,28): error CS0103: The name `set' does not exist in the current context
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(96,98): error CS0103: The name `set' does not exist in the current context
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(103,17): error CS0019: Operator `==' cannot be applied to operands of type `char' and `string'
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(106,21): error CS0019: Operator `==' cannot be applied to operands of type `char' and `string'
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(109,25): error CS0019: Operator `==' cannot be applied to operands of type `char' and `string'
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(112,29): error CS0019: Operator `==' cannot be applied to operands of type `char' and `string'
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(115,33): error CS0019: Operator `==' cannot be applied to operands of type `char' and `string'
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(118,43): error CS1502: The best overloaded method match for `System.Collections.Generic.List<string>.Add(string)' has some invalid arguments
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(118,47): error CS1503: Argument `#1' cannot convert `char' expression to type `string'
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(134,32): error CS0120: An object reference is required to access non-static member `CodeEmitter.escape_string_for_literal(string)'
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(146,23): error CS0103: The name `json' does not exist in the current context
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(152,20): error CS0029: Cannot implicitly convert type `System.Collections.Generic.Dictionary<object,object>' to `System.Collections.Generic.Dictionary<string,object>'
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(165,31): error CS1061: Type `string' does not contain a definition for `rfind' and no extension method `rfind' of type `string' could be found. Are you missing an assembly reference?
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(176,40): error CS0120: An object reference is required to access non-static member `CodeEmitter._resolve_src_root(string)'
- /tmp/tmpr4w6gvr6/cs_selfhost_full_stage1.cs(185,32): error CS0120: An object reference is required to access non-static member `CodeEmitter._load_json_dict(Pytra.CsModule.py_path)'

