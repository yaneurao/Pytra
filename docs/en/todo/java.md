<a href="../../en/todo/java.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — JVM backend (Java / Scala / Kotlin)

> Domain-specific TODO. See [index.md](./index.md) for the full index.
> Java / Scala / Kotlin all target the JVM, so they are managed together in this file.

Last updated: 2026-04-02

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/{java,scala,kotlin}/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/{java,scala,kotlin}/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P numbers first).
- Progress notes and commit messages must always include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/ja/todo/archive/`.
- **Completion criteria for parity tests: "emit + compile + run + stdout match".**
- **You must read the [emitter implementation guide](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## References

### Java
- Old toolchain1 Java emitter: `src/toolchain/emit/java/`
- toolchain2 Java emitter: `src/toolchain2/emit/java/`
- Java runtime: `src/runtime/java/`

### Scala
- Old toolchain1 Scala emitter: `src/toolchain/emit/scala/`
- Scala runtime: `src/runtime/scala/`

### Kotlin
- Old toolchain1 Kotlin emitter: `src/toolchain/emit/kotlin/`
- Kotlin runtime: `src/runtime/kotlin/`

### Common
- toolchain2 TS emitter (reference implementation): `src/toolchain2/emit/ts/`
- Emitter implementation guide: `docs/ja/spec/spec-emitter-guide.md`
- mapping.json spec: `docs/ja/spec/spec-runtime-mapping.md`

## Incomplete Tasks

### P1-SCALA-EMITTER: Implement a new Scala emitter in toolchain2

1. [x] [ID: P1-SCALA-EMITTER-S1] Implement a new Scala emitter in `src/toolchain2/emit/scala/` — CommonRenderer + override structure. Reference the old `src/toolchain/emit/scala/` and the TS emitter
2. [x] [ID: P1-SCALA-EMITTER-S2] Create `src/runtime/scala/mapping.json` — define `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions`
3. [ ] [ID: P1-SCALA-EMITTER-S3] Confirm Scala emit success for all fixtures
4. [ ] [ID: P1-SCALA-EMITTER-S4] Align the Scala runtime with toolchain2 emit output
5. [ ] [ID: P1-SCALA-EMITTER-S5] Pass fixture Scala run parity (`scala`)
6. [ ] [ID: P1-SCALA-EMITTER-S6] Pass stdlib Scala parity (`--case-root stdlib`)
7. [ ] [ID: P1-SCALA-EMITTER-S7] Pass sample Scala parity (`--case-root sample`)

### P1-KOTLIN-EMITTER: Implement a new Kotlin emitter in toolchain2

1. [x] [ID: P1-KOTLIN-EMITTER-S1] Implement a new Kotlin emitter in `src/toolchain2/emit/kotlin/` — CommonRenderer + override structure. Reference the old `src/toolchain/emit/kotlin/` and the TS emitter
2. [x] [ID: P1-KOTLIN-EMITTER-S2] Create `src/runtime/kotlin/mapping.json` — define `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions`
3. [ ] [ID: P1-KOTLIN-EMITTER-S3] Confirm Kotlin emit success for all fixtures
4. [ ] [ID: P1-KOTLIN-EMITTER-S4] Align the Kotlin runtime with toolchain2 emit output
5. [ ] [ID: P1-KOTLIN-EMITTER-S5] Pass fixture Kotlin run parity (`kotlinc` + `java -jar`)
6. [ ] [ID: P1-KOTLIN-EMITTER-S6] Pass stdlib Kotlin parity (`--case-root stdlib`)
7. [ ] [ID: P1-KOTLIN-EMITTER-S7] Pass sample Kotlin parity (`--case-root sample`)

### P2-JVM-LINT: Resolve emitter hardcode lint violations for Scala / Kotlin

1. [x] [ID: P2-JVM-LINT-S1] Confirm 0 violations in all categories for `check_emitter_hardcode_lint.py --lang scala`
2. [x] [ID: P2-JVM-LINT-S2] Confirm 0 violations in all categories for `check_emitter_hardcode_lint.py --lang kotlin`

### P3-JAVA-SELFHOST: Convert toolchain2 to Java via the Java emitter and pass build

Context: [docs/ja/plans/p3-java-selfhost.md](../plans/p3-java-selfhost.md)

1. [ ] [ID: P3-JAVA-SELFHOST-S0] Add return type annotations to functions in the selfhost target code (`src/toolchain2/` all .py) that are missing them — get resolve to a state with no `inference_failure` (shared with other languages; share results from whichever side completes first)
2. [ ] [ID: P3-JAVA-SELFHOST-S1] Emit all toolchain2 .py files to Java and confirm the build passes
3. [ ] [ID: P3-JAVA-SELFHOST-S2] Resolve build failures by fixing the emitter/runtime (no EAST workarounds)
4. [ ] [ID: P3-JAVA-SELFHOST-S3] Place Java selfhost golden files and maintain them as regression tests
5. [ ] [ID: P3-JAVA-SELFHOST-S4] Confirm fixture parity PASS with `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root fixture`
6. [ ] [ID: P3-JAVA-SELFHOST-S5] Confirm sample parity PASS with `run_selfhost_parity.py --selfhost-lang java --emit-target java --case-root sample`
