<a href="../../../ja/plans/archive/20260308-p0-backend-runtime-knowledge-leak-retirement.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Remove Runtime Module Knowledge from Backends

Last updated: 2026-03-08

Related TODO:
- Completed. See `ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01` in `docs/en/todo/archive/20260308.md`.

Background:
- `spec-runtime` says backends and emitters must not hardcode source-side module knowledge such as `math`, `gif`, or `png`.
- In practice, several backends still branch on source module names, helper names, or helper-specific ABI quirks. Typical examples were:
  - special-casing `math` imports into target built-ins,
  - collapsing `pytra.utils.{png,gif}` into target helper names inside emitters,
  - interpreting `save_gif` argument rules directly inside target emitters.
- This is not just a leftover string problem. It is a broken responsibility boundary. Module, symbol, signature, semantic tag, and adapter requirements must be decided before backend emission.
- Linked-program work clarified the responsibilities of the global optimizer and ProgramWriter, but if emitters still depend on source-side module names afterward, the multi-target architecture remains fragile.

Objective:
- Remove emitter branches that depend on source-side runtime module names or ad-hoc helper names.
- Standardize runtime lowering around the runtime symbol index, semantic tags, and resolved runtime call metadata.
- Confine backend-specific variation to target syntax rendering only. Module resolution, helper selection, and ABI adapter selection must live in linker/index/lowering layers.

In scope:
- `src/backends/**`
- `src/toolchain/frontends/runtime_symbol_index.py`
- `tools/gen/gen_runtime_symbol_index.py`
- IR metadata and semantic tags where needed
- representative backend tests, tooling tests, and spec updates

Out of scope:
- blindly forcing all `math/gif/png` strings to zero by grep alone
- banning target-side standard library names themselves (`Math.max`, `scala.math.Pi`, `_G.math.max`, etc.)
- rewriting the runtime implementation itself
- introducing linked-program / ProgramWriter from scratch

Acceptance criteria:
- backends no longer branch on source-side module names such as `math`, `pytra.utils`, or `pytra.std.*`
- backends no longer interpret helper-specific ABI for `save_gif`, `write_rgb_png`, or `pyMath*`
- runtime symbol resolution is data-driven, and backends consume resolved metadata only
- representative regressions for math constants/functions, png/gif calls, module import, and from-import are covered by tests
- `spec-runtime`, `spec-dev`, and related plan docs document both the banned knowledge leaks and the canonical resolution path

Planned verification:
- `python3 tools/check/check_todo_priority.py`
- `python3 -m unittest discover -s tools/unittest/tooling -p 'test_runtime_symbol_index.py'`
- `python3 -m unittest discover -s tools/unittest/common -p 'test_py2x_entrypoints_contract.py'`
- `python3 -m unittest discover -s tools/unittest/backends -p 'test_*.py' -k runtime`

## 1. Problem Breakdown

The leakage fell into four broad categories.

1. Source-module branching
   - emitters changed behavior based on values like `owner == "math"` or `module_id == "math"`
2. Runtime-helper branching
   - emitters knew helper names such as `pyMathPi`, `pyMathE`, or `save_gif`
3. Direct helper ABI interpretation
   - emitters manually rewrote positional/default/keyword rules for helpers such as `save_gif`
4. Import-construction leakage
   - module-object import, function import, and constant import resolution were still partly reassembled inside emitters

These looked separate on the surface, but the root cause was the same: runtime module resolution and call lowering had leaked into backend emitters.

## 2. Target Responsibility Boundary

The target architecture is:

- EAST / linker / runtime symbol index
  - determine canonical runtime module, runtime symbol, semantic tag, and adapter requirements from import bindings
- backend lowerer
  - normalize the above into target-independent call/import/constant nodes
- backend emitter
  - render target syntax only
  - do not interpret source module names or helper semantics

An emitter should do:
- “render `scala.math.sqrt` because the resolved runtime call says so”

It should not do:
- “special-case `math.sqrt` because this looks like the source `math` module”

## 3. Phases

### Phase 1: Inventory and contract

- inventory leakage by target and category
- document, in `spec-runtime` and `spec-dev`, what metadata backends may consume and what source-side knowledge they must not interpret

### Phase 2: Data-driven metadata

- extend the runtime symbol index and import-binding API so module functions, module constants, semantic tags, and adapter kinds can all be resolved outside the backend
- represent helper ABI differences such as `save_gif` with semantic tags or adapter kinds instead of emitter-local branches

### Phase 3: Emitter family migration

- migrate the common `CodeEmitter` family first
- migrate native emitters so they use resolved symbol / adapter metadata rather than source module names

### Phase 4: Guards and regressions

- add representative regressions so that source-module branching re-entry is caught immediately
- supplement grep-based guards with contract tests from input AST to resolved metadata to emitted text

## 4. Task Breakdown

- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S1-01] Inventory `math/gif/png/save_gif/write_rgb_png/pyMath*` leakage under `src/backends/**` and record it by target and category.
- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S1-02] Document backend prohibitions and the data-driven canonical path in `spec-runtime` and `spec-dev`.
- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S2-01] Extend the runtime symbol index / import-binding API so module imports, function imports, constant imports, and semantic tags can be resolved outside the backend.
- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S2-02] Normalize helper ABI differences into adapter kinds and remove direct emitter-side argument rules such as `save_gif`.
- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-01] Migrate representative backends such as C++, JS, C#, and Rust to resolved runtime symbol / adapter rendering.
- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-02] Move Go, Swift, Kotlin, Java, Scala, Ruby, Lua, PHP, and Nim to the same contract.
- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S4-01] Add representative regression tests and tooling guards to prevent source-side knowledge from re-entering.
- [x] [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S4-02] Synchronize docs and full smoke coverage, then close the plan.

## 5. Inventory Highlights

### 5.1 Affected backends

- As of 2026-03-08, direct leakage was confirmed in 10 backends:
  - `cpp`, `cs`, `go`, `kotlin`, `lua`, `php`, `rs`, `ruby`, `scala`, `swift`
- In the same audit, `java`, `js`, `nim`, and `ts` did not show direct hits of the same kind, though some still needed better fail-closed or positive-path tests.

### 5.2 Representative leakage

- source-module branching remained in emitters that watched `math` or `pytra.utils`
- helper-name branching remained in emitters that treated `pyMath*` or `scala.math.*` as canonical inputs
- helper-ABI interpretation remained especially around `save_gif`
- import-construction leakage remained in emitters that rebuilt runtime imports from dotted names rather than canonical resolution metadata

### 5.3 Main gaps before the fix

- Go and Scala still interpreted `save_gif` keyword/default rules directly in the emitter
- Go, Kotlin, and Swift still depended on `pyMath*` helper naming in practice
- Java, JS, TS, Nim, C#, and Rust still needed stronger representative success-path or fail-closed coverage for runtime resolution
- tooling still needed direct assertions for `gif` lookup and `pyMath`-style re-entry guards

## Decision Log

- 2026-03-07: An `audit-runtime` sweep over `src/backends/` found multiple backends still branching on source-side runtime module names and helper names. This was recorded as a responsibility-boundary problem rather than a simple string-cleanup issue.
- 2026-03-07: This work remains independent from linked-program introduction, but it intentionally builds on the resolved-metadata path prepared there.
- 2026-03-08 [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S1-01]: The inventory fixed the representative retirement targets: Go/Scala for direct `save_gif` ABI interpretation, Lua/C#/Rust for source-module-driven import completion, and Go/Kotlin/PHP/Ruby/Swift/Scala for `pyMath*` / `scala.math.*` helper branching.
- 2026-03-08 [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S1-02]: `spec-runtime` and `spec-dev` were updated so target helper names may appear only as render results, never as branching conditions.
- 2026-03-08 [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S2-01]: The runtime symbol index was extended to carry annotated constants (`math.pi`, `math.e`), semantic tags, and richer `import_resolution.bindings` metadata without breaking legacy `meta.import_bindings`.
- 2026-03-08 [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S2-02]: `pytra.utils.gif.save_gif` was normalized through the `image.save_gif.keyword_defaults` adapter kind so Go and Scala could consume shared argument normalization instead of re-implementing helper ABI locally.
- 2026-03-08 [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-01]: The common `CodeEmitter` path was switched to resolved runtime metadata, and representative JS/C#/Rust/C++ routes were migrated to use canonical runtime module/symbol resolution rather than source-side names.
- 2026-03-08 [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S3-02]: Kotlin/Swift/PHP/Ruby/Nim/Go/Java/Scala/Lua were moved to the same contract. The remaining helper naming or source-module branches were replaced with canonical runtime module / runtime symbol metadata.
- 2026-03-08 [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S4-01]: `check_emitter_runtimecall_guardrails.py` was tightened so canonical runtime module/symbol usage is allowed while source-module branches, `binding_module.startswith("pytra.utils.")`, `runtime_symbol.startswith("pyMath")`, and `resolved_runtime.endswith(".pi"|".e")` are flagged at a zero-findings baseline.
- 2026-03-08 [ID: P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01-S4-02]: Representative tooling and backend regressions were expanded so canonical runtime metadata, `gif` module import resolution, and `save_gif` adapter metadata are fixed outside the emitters.
