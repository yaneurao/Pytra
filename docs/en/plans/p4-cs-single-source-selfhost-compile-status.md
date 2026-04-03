<a href="../../ja/plans/p4-cs-single-source-selfhost-compile-status.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-DC2626?style=flat-square">
</a>

# P4 C# Single-Source Selfhost Compile Status

Measured: 2026-04-01

Command:

```bash
python3 tools/check_cs_single_source_selfhost_compile.py
```

## Summary

- prepare: `python3 tools/prepare_selfhost_source_cs.py`
- transpile selfhost source: `rc=0`
- mcs compile: `rc=1`
- compile note: `Time Elapsed 00:00:00.87`

## Error Code Counts

| code | count |
|---|---:|
| CS0101 | 2 |
| CS0111 | 2 |
| CS0234 | 6 |
| CS0246 | 30 |

## Heuristic Categories

| category | count |
|---|---:|
| (none) | 0 |

## Top Errors (first 20)

- /workspace/Pytra/src/runtime/cs/generated/utils/assertions.cs(14,21): error CS0101: The namespace '<global namespace>' already contains a definition for 'Program' [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /tmp/tmpgpms36tj/cs_selfhost_full_stage1.cs(10,29): error CS0234: The type or namespace name 'Path' does not exist in the namespace 'Pytra.CsModule' (are you missing an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /tmp/tmpgpms36tj/cs_selfhost_full_stage1.cs(9,28): error CS0234: The type or namespace name 'sys' does not exist in the namespace 'Pytra.CsModule' (are you missing an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /tmp/tmpgpms36tj/cs_selfhost_full_stage1.cs(11,39): error CS0234: The type or namespace name 'run' does not exist in the namespace 'Pytra.CsModule' (are you missing an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /tmp/tmpgpms36tj/cs_selfhost_full_stage1.cs(39,19): error CS0246: The type or namespace name 'CompletedProcess' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/utils/assertions.cs(75,24): error CS0111: Type 'Program' already defines a member called 'Main' with the same parameter types [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/numeric_ops.cs(17,61): error CS0246: The type or namespace name 'T' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/numeric_ops.cs(17,23): error CS0246: The type or namespace name 'T' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/predicates.cs(17,35): error CS0246: The type or namespace name 'T' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/numeric_ops.cs(32,32): error CS0246: The type or namespace name 'T' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/numeric_ops.cs(32,37): error CS0246: The type or namespace name 'T' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/numeric_ops.cs(32,23): error CS0246: The type or namespace name 'T' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/predicates.cs(27,35): error CS0246: The type or namespace name 'T' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/numeric_ops.cs(40,32): error CS0246: The type or namespace name 'T' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/numeric_ops.cs(40,37): error CS0246: The type or namespace name 'T' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/numeric_ops.cs(40,23): error CS0246: The type or namespace name 'T' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/zip_ops.cs(17,99): error CS0246: The type or namespace name 'A' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/zip_ops.cs(17,139): error CS0246: The type or namespace name 'B' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/zip_ops.cs(17,56): error CS0246: The type or namespace name 'A' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
- /workspace/Pytra/src/runtime/cs/generated/built_in/zip_ops.cs(17,59): error CS0246: The type or namespace name 'B' could not be found (are you missing a using directive or an assembly reference?) [/tmp/tmpgpms36tj/SelfhostCheck.csproj]
