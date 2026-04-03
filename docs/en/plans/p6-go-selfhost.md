<a href="../../ja/plans/p6-go-selfhost.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P6-GO-SELFHOST: Convert toolchain2 to Go via the Go emitter and pass go build

Last updated: 2026-03-30
Status: In progress (S1–S2 complete)

## Background

Convert Pytra's own transpiler (toolchain2) to Go and verify that the resulting Go compiler operates correctly. Go has already achieved 100% PASS on fixture + sample, so selfhost can be started.

## Flow

1. Convert all toolchain2 `.py` files to Go with `pytra-cli2 -build --target go`
2. Compile with `go build` to generate a binary
3. Use the binary to convert fixture/sample/stdlib, and verify that it produces the same output as Python (`run_selfhost_parity.py` from P3-SELFHOST-PARITY)

## Subtasks

1. [S0] Complete type annotation coverage for selfhost target code (shared with other languages)
2. [S1] toolchain2 → Go emit + pass go build ✅
3. [S2] Fix emitter/runtime for build failures ✅
4. [S3] Place selfhost Go goldens + regression tests (`regenerate_selfhost_golden.py --target go`)

## Design decisions

- No EAST workarounds. Build failures are resolved by fixing the emitter/runtime.
- Type annotation completion (S0) is shared with other language selfhosts. Whichever finishes first provides the results.
- Goldens are placed in `test/selfhost/go/` and managed by a unified script (`regenerate_selfhost_golden.py`).
- Goldens are not managed in git (they are in `.gitignore`).

## Decision Log

- 2026-03-29: Filed P6-GO-SELFHOST. Start after P1-GO-CONTAINER-WRAPPER is complete.
- 2026-03-30: S1 (go build pass) and S2 (build failure fixes) complete. go build succeeds for all 22 files.
