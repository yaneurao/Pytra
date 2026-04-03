<a href="../../en/plans/p2-link-input-completeness.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2-LINK-INPUT-COMPLETENESS: Link layer input completeness verification

Last updated: 2026-03-26
Status: Not started

## Background

The primary cause of Go build failures in selfhost (P2-SELFHOST-S4) is that the EAST3 module set passed to link-input is incomplete. Six dependency modules that are imported from the 37 seed files but not included in the seeds are missing, causing undefined symbols in the emitted Go code.

This problem is not specific to selfhost — it occurs generally when converting multi-module Python projects. The link layer is where information from all modules converges, and verifying input completeness here is the correct design.

## Design

### Link layer input completeness verification

The link layer (`LinkedProgramLoader`) verifies the following upon receiving `link-input.v1`:

1. **Import resolution check**: Confirm that all `module_id` values in `meta.import_bindings` / `meta.import_modules` / `meta.import_symbols` of every linked module exist as modules within link-input.
2. **Unresolved import enumeration**: Report missing `module_id` values as missing modules in an error.
3. **Fail-closed**: Stop linking if even one unresolved import exists (do not silently ignore).

Error message format:

```
link error: unresolved import dependency
  resolver.py imports builtin_registry (module_id: toolchain2.resolve.py.builtin_registry)
  but no link unit provides this module.

  Missing modules:
    - toolchain2.compile.jv
    - toolchain2.resolve.py.builtin_registry
    - toolchain2.resolve.py.normalize_order
    - toolchain2.parse.py.nodes
    - toolchain2.parse.py.parser
    - toolchain2.link.expand_defaults
```

### Completion via type stubs (for modules that cannot be parsed)

Provide a mechanism for supplying type stubs (in EAST3 format) that can be fed into link-input when a dependency module cannot be parsed.

- Stubs are regular EAST3 documents with `east_stage=3` but empty function bodies (or the equivalent of `raise NotImplementedError`)
- They retain only type annotations, function signatures, and class definitions
- The goal is to pass the Go compiler's type check with stubs; execution is not intended
- Sources:
  - When EAST1/EAST2 is available: extract signatures automatically from there
  - When parsing itself fails: generate from a hand-written declaration file (`.pyi` equivalent)

### Relationship to existing implementation

- `_analyze_import_graph_impl` (canonical in `src/toolchain2/frontends/east1_build.py`) is the prototype for import graph analysis. Reuse it for link layer input verification as well.
- The existing responsibilities of `LinkedProgramLoader` (type_id finalization, non-escape summary, etc.) are not changed. Input verification is added as a pre-processing step before those.

## Risks

- Runtime modules such as `pytra.std.*` / `pytra.built_in.*` may not be included in link-input by design. A whitelist of "known external modules" to exclude from verification is needed.
- Verification ordering when circular imports are present.

## Subtasks

1. [ID: P2-LINK-COMPLETE-S1] Implement import resolution completeness verification in the link layer (report unresolved imports fail-closed)
2. [ID: P2-LINK-COMPLETE-S2] Define the whitelist of runtime / stdlib modules to exclude from verification
3. [ID: P2-LINK-COMPLETE-S3] Design and implement the type stub generation mechanism (for modules that cannot be parsed)
4. [ID: P2-LINK-COMPLETE-S4] Run the completeness check against the 37 selfhost files and confirm missing modules

## Acceptance Criteria

1. When an incomplete module set is passed to link-input, the missing modules are enumerated and the process stops with an error.
2. Imports from runtime / stdlib do not produce false positives.
3. Feeding type stubs into link-input allows linking to succeed.
4. Existing fixture / sample / selfhost pipelines do not regress.

## Decision Log

- 2026-03-26: Identified that the root cause of the selfhost Go build failure is the incompleteness of link-input. Decided to implement this as input verification that the link layer should already have, rather than as a new mechanism. Transitive closure computation is a responsibility of the link layer; the design should not depend on manual file selection.
