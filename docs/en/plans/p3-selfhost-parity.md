<a href="../../ja/plans/p3-selfhost-parity.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P3-SELFHOST-PARITY: fixture/sample parity verification using a selfhosted compiler

Last updated: 2026-03-30
Status: Not started

## Background

The selfhost matrix shows "can toolchain2 be converted to language X, and can the resulting compiler generate language Y code?" However, "can emit" alone is insufficient — it must also be verified that "the emitted code runs correctly" via fixture/sample parity.

## Flow

Example: selfhost language = C++, emit target = Go:

```
1. Python toolchain2 → convert to C++ (pytra-cli2 -build --target cpp)
2. Compile C++ (g++ → generate selfhost binary)
3. Use selfhost binary to convert fixture .py → Go
4. Run Go code with go run
5. Compare stdout against direct Python execution (parity check)
```

Step 3 is new: "use the selfhosted binary instead of Python's pytra-cli2." Steps 4–5 can reuse the existing parity check infrastructure.

## Design

### Script

Create `tools/run/run_selfhost_parity.py`.

```bash
# Verify Go fixture parity using C++ selfhost
python3 tools/run/run_selfhost_parity.py \
  --selfhost-lang cpp --emit-target go --case-root fixture

# Verify all-language sample parity using C++ selfhost
python3 tools/run/run_selfhost_parity.py \
  --selfhost-lang cpp --emit-target go,rs,ts --case-root sample
```

### Processing steps

1. **selfhost build**: Convert toolchain2 with `pytra-cli2 -build --target <selfhost-lang>`. Generate a binary using the target language's compiler.
2. **emit**: Use the selfhost binary to convert fixture/sample `.py` files to the target language.
3. **parity check**: Reuse the existing parity check compile + run + stdout comparison logic.
4. **Result recording**: Record emit/build/parity results in `.parity-results/selfhost_<selfhost-lang>.json`.

### JSON format

```json
{
  "selfhost_lang": "cpp",
  "stages": {
    "emit": {"status": "ok", "timestamp": "2026-03-30T15:00:00"},
    "build": {"status": "ok", "timestamp": "2026-03-30T15:01:00"},
    "parity": {"status": "ok", "timestamp": "2026-03-30T15:10:00"}
  },
  "emit_targets": {
    "go": {
      "status": "ok",
      "fixture_pass": 144,
      "fixture_fail": 2,
      "sample_pass": 18,
      "sample_fail": 0,
      "timestamp": "2026-03-30T15:10:00"
    },
    "rs": {"status": "not_tested", "timestamp": ""},
    "ts": {"status": "not_tested", "timestamp": ""}
  }
}
```

### Reflection in the matrix

`gen_backend_progress.py` already has a mechanism to read `.parity-results/selfhost_<lang>.json`. Once this script writes the JSON, the selfhost matrix will be updated automatically.

PASS condition: `emit_targets.<lang>.fixture_fail == 0 && sample_fail == 0 && stdlib_fail == 0` (all of fixture + sample + stdlib must PASS)

### Removing hardcoded Python row

The Python row in the current selfhost matrix is hardcoded inside `_build_selfhost_matrix` (only C++ and Go are 🟩). This script will also verify parity for Python → each language and record results in `.parity-results/selfhost_python.json`, transitioning away from hardcoding.

## Prerequisites

- The fixture/sample parity check infrastructure must be working (P0-CLI2-RS-TS etc. completed).
- A successful selfhost build for each language is not a prerequisite. The script skeleton can be written first, and languages can be verified as their builds succeed. Languages whose builds fail will simply have `build: fail` recorded in `selfhost_<lang>.json`.

## Decision Log

- 2026-03-30: Decided on the approach of running fixture/sample parity through a selfhosted compiler. Emit alone will not qualify as 🟩.
