<a href="../../ja/plans/p0-selfhost-golden-unified.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P0-SELFHOST-GOLDEN-UNIFIED: Consolidate selfhost golden generation and verification into a single script

Last updated: 2026-03-30
Status: Not started

## Background

Each backend team is creating its own selfhost golden script (e.g. the C++ team's `test_cpp_selfhost_golden.py`). If left as-is, similar scripts will proliferate as new languages are added, increasing maintenance costs.

Consolidate golden generation and verification into a single script shared across all languages.

## Design

### Generation script

`tools/gen/regenerate_selfhost_golden.py`

```bash
# Generate selfhost golden for all languages at once
python3 tools/gen/regenerate_selfhost_golden.py

# For a specific language only
python3 tools/gen/regenerate_selfhost_golden.py --target cpp,go
```

Steps:
1. Emit all toolchain2 `.py` files to the specified language (`pytra-cli2 -build --target <lang>`)
2. Place emit results under `test/selfhost/<lang>/`
3. If existing golden files are present, report the diff

### Regression tests

`tools/unittest/selfhost/test_selfhost_golden.py`

Common to all languages:
1. Verify that golden files match the latest emit results
2. Verify that the target language's compiler accepts the output (`g++`, `go build`, `rustc`, `tsc`, etc.)

Per-language parameters (compile command, file extension, etc.) are defined in a table, eliminating the need for language-specific scripts.

### Placement

```
test/selfhost/
  cpp/         ← C++ selfhost golden
  go/          ← Go selfhost golden
  rs/          ← Rust selfhost golden
  ts/          ← TS selfhost golden
```

### Scripts to retire

Language-specific scripts (e.g. `test_cpp_selfhost_golden.py`) are moved to `tools/unregistered/`.

## Decision Log

- 2026-03-30: The C++ team created `test_cpp_selfhost_golden.py` independently. Confirmed the need for a unified script to prevent language-specific script proliferation.
