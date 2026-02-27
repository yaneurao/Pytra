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
- compile note: `/tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(3544,11): error CS1525: Unexpected symbol `void', expecting `class', `delegate', `enum', `interface', `partial', `ref', or `struct'`

## Error Code Counts

| code | count |
|---|---:|
| CS0136 | 2 |
| CS1002 | 21 |
| CS1519 | 6 |
| CS1520 | 3 |
| CS1525 | 175 |

## Heuristic Categories

| category | count |
|---|---:|
| call_signature_shape | 32 |
| shadowed_local | 2 |
| template_or_placeholder_fragment | 42 |

## Top Errors (first 20)

- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(616,13): error CS1525: Unexpected symbol `{'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(616,25): error CS1525: Unexpected symbol `,'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(616,35): error CS1525: Unexpected symbol `,'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(616,47): error CS1525: Unexpected symbol `,'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(616,58): error CS1525: Unexpected symbol `,'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(616,71): error CS1002: ; expected
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(616,71): error CS1525: Unexpected symbol `)'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(616,87): error CS1525: Unexpected symbol `)', expecting `;' or `}'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(622,13): error CS1525: Unexpected symbol `{'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(622,20): error CS1525: Unexpected symbol `,'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(622,32): error CS1525: Unexpected symbol `,'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(622,46): error CS1002: ; expected
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(622,46): error CS1525: Unexpected symbol `)'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(622,62): error CS1525: Unexpected symbol `)', expecting `;' or `}'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(789,18): error CS1525: Unexpected symbol `{prefix}_{self.tmp_id}'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(798,22): error CS1525: Unexpected symbol `{rename_prefix}{name}'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(869,17): error CS1525: Unexpected symbol `{'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(869,24): error CS1525: Unexpected symbol `,'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(869,33): error CS1525: Unexpected symbol `,'
- /tmp/tmpecnouh74/cs_selfhost_full_stage1.cs(869,42): error CS1525: Unexpected symbol `,'

