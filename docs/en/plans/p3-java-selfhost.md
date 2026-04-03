<a href="../../en/plans/p3-java-selfhost.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P3-JAVA-SELFHOST: Transpile toolchain2 to Java with the Java emitter and get it to build

Last updated: 2026-03-30
Status: Not started

## Background

After implementing the Java emitter in P1-JAVA-EMITTER, convert Pytra's own transpiler (toolchain2) to Java and verify that the converted compiler operates correctly.

## Flow

1. Use `pytra-cli2 -build --target java` to convert all toolchain2 `.py` files to Java
2. Compile with `javac` to produce class files
3. Run with `java` to convert fixture/sample/stdlib and verify that the output matches Python (P3-SELFHOST-PARITY)

## Java-specific considerations

- Java has no top-level functions, so selfhost code must be wrapped in classes
- Java's generic type constraint on primitives (`List<long>` is invalid → `List<Long>`) may affect selfhost code
- Checked exception `throws` declarations may propagate across all methods in selfhost code

## Design decisions

- No EAST workarounds. Build failures are resolved by fixing the emitter/runtime.
- Type annotation completion (S0) is shared with other language selfhosts. Use the results from whichever language finishes first.
- golden files are placed under `test/selfhost/java/` and managed by the unified script (`regenerate_selfhost_golden.py`).

## Decision Log

- 2026-03-30: Filed the Java selfhost task. Start after P1-JAVA-EMITTER is Completed. Once Java passes, expanding to Kotlin selfhost will be within reach.
