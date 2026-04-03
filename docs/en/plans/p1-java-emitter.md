<a href="../../ja/plans/p1-java-emitter.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1-JAVA-EMITTER: Implement a new Java emitter in toolchain2

Last updated: 2026-03-30
Status: Not started

## Background

Java is widely used in Android development and server-side applications, and there is high user demand for it as a Pytra target language. A Java emitter (`src/toolchain/emit/java/`) and runtime (`src/runtime/java/`) exist in the old toolchain1, but they need to be migrated to the new toolchain2 pipeline.

Getting Java working will also bring a Kotlin (JVM-based) backend closer.

## Design

### Emitter structure

- Implemented in `src/toolchain2/emit/java/` using CommonRenderer + override structure
- Reference the old `src/toolchain/emit/java/` and TS emitter (`src/toolchain2/emit/ts/`)
- Only override nodes specific to Java (mandatory class structure, package, static methods, checked exceptions, type erasure, etc.)

### mapping.json

Define the following in `src/runtime/java/mapping.json`:
- `calls`: runtime_call mappings
- `types`: EAST3 type names → Java type names (`int64` → `long`, `float64` → `double`, `str` → `String`, `bool` → `boolean`, `Exception` → `Exception`, etc.)
- `env.target`: `"\"java\""`
- `builtin_prefix`: `"py_"`
- `implicit_promotions`: Java implicit promotion pairs (nearly the same as C++)

### Java-specific considerations

- Java has no top-level functions; all code must be placed inside a class
- `main_guard_body` maps to `public static void main(String[] args)`
- Generics cannot use primitive types directly (`List<int>` is not allowed; `List<Long>` is needed)
- Handling of checked exceptions (`throws` declaration)

### parity check

- Support for `pytra-cli2 -build --target java` is needed (request to infrastructure team)
- Verify with `runtime_parity_check_fast.py --targets java`
- Three stages: fixture + sample + stdlib

## Decision Log

- 2026-03-30: Java backend role established. Approach: implement toolchain2 emitter following the emitter guide. Getting Java working will bring a Kotlin backend closer.
