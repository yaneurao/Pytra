<a href="../../ja/progress/index.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Project Progress

An overview of Pytra's development status. Links to test results, tasks, changelog, and documentation.

## Frontend (shared pipeline)

[How EAST works](../guide/east-overview.md)
— A guide that walks through how Python code is transformed through EAST1 → EAST2 → EAST3 with concrete examples. For first-time readers.

[How emitters work](../guide/emitter-overview.md)
— A guide showing how EAST3 is converted to C++/Go/Rust etc., with before/after comparisons.

[EAST spec](../spec/spec-east.md) / [EAST1](../spec/spec-east1.md) / [EAST2](../spec/spec-east2.md) / [EAST3 Optimizer](../spec/spec-east3-optimizer.md) / [Linker](../spec/spec-linker.md)
— Formal specifications for each stage.

## Backend support

[Overall summary](./backend-progress-summary.md)
— Overview of fixture / sample / stdlib / selfhost / emitter lint for all languages in one page.

[Parity changelog](./changelog.md)
— Auto-recorded log of when PASS counts increase or decrease. Use this to catch regressions immediately.

Details:
- [fixture](./backend-progress-fixture.md) — language feature unit tests
- [sample](./backend-progress-sample.md) — real applications ([samples list](../tutorial/samples.md))
- [stdlib](./backend-progress-stdlib.md) — Python standard library compatible modules
- [emitter host](./backend-progress-emitter-host.md) — can each language host the C++ emitter? (intermediate milestone)
- [selfhost](./backend-progress-selfhost.md) — transpile the compiler itself. Requires fixture + sample + stdlib all PASS
- [emitter lint](./emitter-hardcode-lint.md) — emitter hardcode violation detection
— Counts grep-detected violations where emitters hardcode module names, runtime symbols, or class names instead of using EAST3 data.
- [Top100 language coverage](./top100-language-coverage.md) — backend / host / interop / syntax / defer classification for the top 100 languages

## Task list

[TODO index](../todo/index.md)
— Tasks managed per area (C++ / Go / Rust / TS / infra). Each agent reads and writes only its own area file.

## Changelog

[Detailed changelog](../changelog.md)
— Daily record of changes including spec updates, new features, bug fixes, and documentation.

## Documentation

- [Tutorial](../tutorial/README.md)
- [Guides](../guide/README.md)
- [Specification](../spec/index.md)
