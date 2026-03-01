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
- compile note: `/usr/lib/mono/4.5/mscorlib.dll (Location of the symbol related to previous error)`

## Error Code Counts

| code | count |
|---|---:|
| CS0019 | 21 |
| CS0021 | 3 |
| CS0029 | 16 |
| CS0030 | 2 |
| CS0103 | 1 |
| CS0119 | 3 |
| CS0131 | 12 |
| CS0150 | 1 |
| CS0173 | 4 |
| CS0246 | 1 |
| CS0266 | 26 |
| CS0411 | 1 |
| CS0815 | 3 |
| CS1061 | 50 |
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

- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(29,26): error CS1061: Type `object' does not contain a definition for `Key' and no extension method `Key' of type `object' could be found. Are you missing an assembly reference?
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(30,26): error CS1061: Type `object' does not contain a definition for `Value' and no extension method `Value' of type `object' could be found. Are you missing an assembly reference?
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(31,19): error CS0131: The left-hand side of an assignment must be a variable, a property or an indexer
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(126,14): error CS1502: The best overloaded method match for `CodeEmitter.require_dep(string)' has some invalid arguments
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(126,26): error CS1503: Argument `#1' cannot convert `object' expression to type `string'
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(139,20): error CS0103: The name `sorted' does not exist in the current context
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(241,30): error CS1061: Type `object' does not contain a definition for `Key' and no extension method `Key' of type `object' could be found. Are you missing an assembly reference?
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(242,30): error CS1061: Type `object' does not contain a definition for `Value' and no extension method `Value' of type `object' could be found. Are you missing an assembly reference?
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(243,23): error CS0131: The left-hand side of an assignment must be a variable, a property or an indexer
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(247,26): error CS1061: Type `object' does not contain a definition for `Key' and no extension method `Key' of type `object' could be found. Are you missing an assembly reference?
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(248,26): error CS1061: Type `object' does not contain a definition for `Value' and no extension method `Value' of type `object' could be found. Are you missing an assembly reference?
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(250,23): error CS0131: The left-hand side of an assignment must be a variable, a property or an indexer
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(274,24): error CS0019: Operator `*' cannot be applied to operands of type `string' and `long'
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(292,26): error CS1061: Type `object' does not contain a definition for `Key' and no extension method `Key' of type `object' could be found. Are you missing an assembly reference?
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(293,24): error CS1061: Type `object' does not contain a definition for `Value' and no extension method `Value' of type `object' could be found. Are you missing an assembly reference?
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(344,24): error CS1061: Type `object' does not contain a definition for `Key' and no extension method `Key' of type `object' could be found. Are you missing an assembly reference?
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(345,24): error CS1061: Type `object' does not contain a definition for `Value' and no extension method `Value' of type `object' could be found. Are you missing an assembly reference?
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(347,19): error CS0131: The left-hand side of an assignment must be a variable, a property or an indexer
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(444,21): error CS0266: Cannot implicitly convert type `object' to `bool'. An explicit conversion exists (are you missing a cast?)
- /tmp/tmp41m68cfo/cs_selfhost_full_stage1.cs(452,13): error CS0019: Operator `&&' cannot be applied to operands of type `bool' and `bool?'

