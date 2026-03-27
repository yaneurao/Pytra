<a href="../../ja/plans/p2-runtime-sot-linked-program-integration.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2 Proposal: Integrate Runtime SoT into the Linked Program

Last updated: 2026-03-07

Related:
- [archive/20260307-p0-linked-program-global-optimizer-and-program-writer.md](./archive/20260307-p0-linked-program-global-optimizer-and-program-writer.md)
- [archive/20260308-p1-runtime-abi-decorator-for-generated-helpers.md](./archive/20260308-p1-runtime-abi-decorator-for-generated-helpers.md)
- [archive/20260308-p1-cpp-py-runtime-core-slimming.md](./archive/20260308-p1-cpp-py-runtime-core-slimming.md)

Notes:

- This is an unscheduled design memo and is not yet queued in `docs/ja/todo/index.md`.
- Its purpose is to preserve the context for later work, not to start implementation immediately.

Background:
- Today, runtime SoT (`src/pytra/built_in/*.py`, `src/pytra/std/*.py`, `src/pytra/utils/*.py`) is mainly emitted as target-specific pre-generated runtime artifacts.
- That design creates a separate boundary between generated helpers and user code. In backends like C++, where internal representation is ref-first, that boundary forces fixed helper ABIs. `@abi` is the practical answer to that constraint.
- The more natural long-term design is to load pure-Python runtime helpers into the linked program as ordinary modules and let the global optimizer analyze them together with user code.
- In that design, helpers such as `str.join` become ordinary calls rather than external/helper boundaries, greatly reducing `@abi` pressure and allowing stronger call-graph, SCC, alias, escape, and ownership reasoning.

Goal:
- Design a route in which pure-Python runtime SoT is part of the linked program module set and goes through the same IR/optimizer pipeline as user modules.
- Treat generated runtime helpers not as prebuilt side artifacts but as part of the program.
- Reduce `@abi` from a primary permanent mechanism to a transitional annotation for prebuilt-runtime periods.
- Make `py_runtime` slimming and runtime deduplication a whole-program optimization problem instead of a target-specific wrapper problem.

Scope:
- linked-program loader / manifest schema
- runtime-module collection and dependency resolution
- optimizer scope over linked runtime modules
- backend lower / ProgramWriter treatment of runtime modules
- build / restart / debug flows for runtime SoT modules
- responsibility boundaries in docs/spec

Out of scope:
- implementing it immediately
- immediately removing `@abi`
- fully rewriting native runtime (`native/core`, `native/std`, `native/utils`) in pure Python
- pulling truly native facilities (OS, SDK, filesystem, regex, image codecs, etc.) into the linked program
- switching all targets at once

Acceptance criteria for future implementation:
- Pure-Python runtime SoT modules can be loaded as linked-program modules.
- The global optimizer can analyze runtime-helper modules and user modules within the same call graph / SCC / non-escape / ownership domain.
- Representative helpers such as `str.join` can be optimized as ordinary calls without depending on pre-generated helper ABI boundaries.
- `@abi` may still exist, but it is no longer mandatory for runtime helpers in general.
- Only places that genuinely require native companions remain in `@extern` / `native/*`; everything else can move toward linked runtime modules.

## 1. The Core Problem

The current runtime pipeline is effectively split into two layers:

1. user program
   - `py2x -> EAST -> linked program -> backend`
2. runtime SoT
   - emitted separately as per-target artifacts via `emit-runtime-*` or pre-generation

That split is convenient for packaging, but awkward for optimization:

- runtime helpers are written in pure Python, yet do not participate in the ordinary call graph
- helper calls become artificial boundaries
- helper-specific ABI/adapter rules are needed
- alias / escape / ownership cannot be solved uniformly across user code and runtime helpers

So part of the reason `@abi` is needed is precisely that runtime helpers are cut out as separate artifacts too early.

## 2. Target Architecture

```text
user .py
runtime SoT .py
  -> EAST1/EAST2/EAST3 (per module)
  -> LinkedProgramLoader (user + runtime modules)
  -> LinkedProgramOptimizer
  -> BackendLower/Optimize
  -> ModuleEmitter / ProgramWriter
```

The key idea is to stop treating runtime SoT as “special backend runtime modules” and instead treat them as ordinary linked-program modules.

## 3. Relationship to `@abi`

This proposal does not eliminate `@abi`; it shrinks its necessary scope.

### 3.1 Cases where `@abi` becomes less necessary

- pure-Python runtime helpers
- helper-internal `list/dict/set/bytearray` arguments
- ordinary user-code-to-helper calls

These become ordinary intra-program calls, so optimizer judgment can supersede fixed helper ABI rules.

### 3.2 Cases where `@abi` may still remain

- targets that still ship prebuilt runtime artifacts
- helpers whose public boundary must remain fixed
- backend-only restart/debug routes that do not load linked runtime modules
- boundaries to native companions or other external implementations

So the natural long-term role of `@abi` is:

- now: required for helper ABI stabilization
- later: limited to prebuilt / external / public-helper boundaries

## 4. Expected Benefits

### 4.1 Optimization

- call graph / SCC construction including runtime helpers
- non-escape / alias / ownership reasoning across helper boundaries
- inlining candidates inside runtime helpers
- fewer helper-specific ABI adapters

### 4.2 Simpler ownership model

- runtime helpers are treated as ordinary modules
- `emit-runtime-*` can shrink in responsibility
- exception rules around helper ABI decrease
- the set of things that should move from `py_runtime` back into SoT becomes much clearer

### 4.3 Cross-target leverage

- this is not only a C++ problem
- runtime-helper special handling can shrink in other targets too
- backend-specific runtime-artifact differences can be pushed back into packaging

## 5. Hard Parts

### 5.1 Packaging versus ordinary modules

Even if runtime helpers are optimized as ordinary modules, final output still has to decide, per target:

- whether they are emitted as user artifacts
- bundled as runtime artifacts
- or replaced by prebuilt runtime pieces

Optimization integration and packaging policy therefore must be designed separately.

### 5.2 Native companion boundary

Some layers, such as `native/core` or `native/std/*`, cannot be expressed fully in pure Python. A complete removal of runtime artifacts is not the goal.

The real split is:

- pure-Python runtime helpers
  - integrated into the linked program
- native companions / ABI glue / OS access
  - remain in native runtime

### 5.3 Restart/debug flows

Routes such as `ir2lang.py` or backend-only restart need a clear rule for how runtime-helper modules are provided:

- materialize them into linked output too, or
- record runtime-module closure in the manifest

Without that, restart/debug loses reproducibility.

### 5.4 Bootstrap

Both host and selfhost paths need runtime-module collection. The design has to answer whether collection is:

- restricted to actually-used runtime modules, or
- performed in broader family-sized batches

## 6. Staged Implementation Model

### Phase 1: runtime-module collection design

- define how runtime SoT modules enter the linked program
- decide whether runtime modules are explicit in the manifest or auto-collected
- define how entry modules differ from runtime modules

### Phase 2: optimizer integration

- let the global optimizer read runtime-helper modules as ordinary inputs
- include runtime helpers in non-escape / ownership / type-id / call-graph reasoning
- reconcile this with any remaining import-closure logic

### Phase 3: backend / ProgramWriter integration

- make it possible to emit linked runtime modules as ordinary modules
- still allow packaging rules to shape the output tree
- coexist with prebuilt fallback routes

### Phase 4: shrink `@abi`

- audit which helpers no longer need `@abi` in the linked-runtime path
- limit `@abi` to external / prebuilt / public-helper boundaries

## 7. Key Decisions to Make When Implementing

- Is the unit loaded into the linked program a module or a symbol closure?
- Should linked runtime helpers be emitted as the same kind of artifacts as user modules, or packaged separately?
- Should linked runtime start as all-target support or as a C++-first experiment?
- Does `@abi` remain as an optional hint, or become disallowed in linked-runtime-only paths?

## 8. Things That Should Come First

Before serious work on this idea, at least the following should exist:

1. `P0-LINKED-PROGRAM-OPT-01`
   - the linked-program and ProgramWriter foundation
2. `P0-BACKEND-RUNTIME-KNOWLEDGE-LEAK-01`
   - removing backend dependence on handwritten runtime-module names
3. `P1-RUNTIME-ABI-DECORATOR-01`
   - the transitional mechanism for fixed helper ABI boundaries
4. `P2-LINKED-RUNTIME-TEMPLATE-01`
   - fix the v1 syntax / metadata / validation contract for linked runtime helper generics around `@template("T", ...)`

This proposal is the long-term direction, but it should still be treated as a later-stage effort.

## Decision Log

- 2026-03-07: `@abi` is a practical necessity for helper-ABI stabilization right now, but the long-term design should integrate pure-Python runtime SoT into the linked program and optimize helpers as ordinary calls.
- 2026-03-07: Therefore `@abi` should not be treated as something all helpers will carry forever. It should shrink into a transitional feature for pre-generated runtime periods and for external/public helper boundaries.
