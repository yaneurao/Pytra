<a href="../../en/plans/p3-cs-selfhost.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P3-CS-SELFHOST: Transpile toolchain2 to C# with the C# emitter and get it to build

Last updated: 2026-03-30
Status: Not started

## Background

After implementing the C# emitter in P1-CS-EMITTER, convert Pytra's own transpiler (toolchain2) to C# and verify that the converted compiler operates correctly.

## Flow

1. Use `pytra-cli2 -build --target cs` to convert all toolchain2 `.py` files to C#
2. Compile with `mcs` or `dotnet build` to produce a binary
3. Use the binary to convert fixture/sample/stdlib and verify that the output matches Python (P3-SELFHOST-PARITY)

## Design decisions

- No EAST workarounds. Build failures are resolved by fixing the emitter/runtime.
- Type annotation completion (S0) is shared with other language selfhosts. Use the results from whichever language finishes first.
- golden files are placed under `test/selfhost/cs/` and managed by the unified script (`regenerate_selfhost_golden.py`).

## Decision Log

- 2026-03-30: Filed the C# selfhost task. Start after P1-CS-EMITTER is Completed.
