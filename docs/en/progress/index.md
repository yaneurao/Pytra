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

[Fixture matrix](./backend-progress-fixture.md)
— Unit tests for language features (146 cases). One feature per file, verifying emit + compile + run + stdout match for each target language.

[Sample matrix](./backend-progress-sample.md)
— Real applications (18 cases). Mandelbrot set, ray tracing, Game of Life, etc. Run in each language and verify identical output to Python. See [samples list](../tutorial/samples.md).

[Selfhost matrix](./backend-progress-selfhost.md)
— Transpile Pytra's own compiler (toolchain2) to each language and verify the resulting compiler can emit all targets.

## Task list

[TODO index](../todo/index.md)
— Tasks managed per area (C++ / Go / Rust / TS / infra). Each agent reads and writes only its own area file.

## Changelog

[Changelog](../changelog.md)
— Daily record of changes including spec updates, new features, bug fixes, and documentation.

## Documentation

- [Tutorial](../tutorial/README.md)
- [Guides](../guide/README.md)
- [Specification](../spec/index.md)
