<a href="../../ja/spec/spec-folder.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Folder Responsibility Map Specification (Pytra)

This document is the source of truth for placement decisions: which folder should contain what.
Algorithm details belong to other specs (`spec-dev.md`, `spec-east123.md`, `spec-runtime.md`); this file defines boundaries only.

## 1. Scope

- In scope:
  - Repository top-level folders
  - Major responsibility boundaries under `src/`
  - `docs/ja/todo/` operation boundaries
- Out of scope:
  - Detailed algorithms
  - Full per-language support matrix

## 2. Top-Level Folder Responsibilities

### 2.1 `src/`

- Purpose: transpiler implementation, shared libraries, and target runtimes.
- Allowed: `py2*.py`, `src/pytra/`, `src/runtime/<lang>/pytra/`, `src/backends/`.
- Not allowed: logs, temporary outputs, process docs.

### 2.2 `test/`

- Purpose: regression tests and fixtures.
- Allowed: unit/integration tests, fixtures.
- Not allowed: production implementation.

### 2.3 `sample/`

- Purpose: public sample inputs/outputs and comparison artifacts.
- Allowed: `sample/py`, `sample/<lang>`, `sample/images`, `sample/golden`.
- Not allowed: unorganized local experiments.

### 2.4 `docs/ja/`

- Purpose: source of truth documentation.
- Allowed: `spec/`, `plans/`, `todo/`, `language/`, `news/`.
- Not allowed: implementation code.

### 2.5 `docs/en/`

- Purpose: English translation mirror of `docs/ja/`.
- Allowed: translated counterparts of `docs/ja/`.
- Not allowed: upstream-first edits diverging from `docs/ja/`.

### 2.6 `materials/`

- Purpose: user-provided references and source materials.
- Allowed: `materials/refs/`, `materials/inbox/`, `materials/archive/`.
- Not allowed: modifying original source files for transpiler convenience.

### 2.7 `work/`

- Purpose: isolated temporary workspace for Codex.
- Allowed: `work/out/`, `work/selfhost/`, `work/tmp/`, `work/logs/`.
- Not allowed: canonical source artifacts.

### 2.8 `out/`, `selfhost/`, `archive/` (compat operation)

- Purpose: backward-compatible operation during phased cleanup.
- Allowed: outputs from existing scripts.
- Not allowed: new permanent storage policy.
- Note: use `work/` first for new temporary outputs.

## 3. Responsibilities Under `src/`

### 3.1 `src/pytra/compiler/east_parts/`

- Purpose: EAST1/EAST2/EAST3 stage processing.
- Allowed: `east1.py`, `east2.py`, `east3.py`, `east3_lowering.py`, `east_io.py`, `core.py`.
- Not allowed: target-language-specific final emission branches.
- Dependency rule: allow `pytra.*` shared layers; avoid direct dependency on `backends/lang>`.

### 3.2 `src/backends/`

- Purpose: absorb target-language syntax differences.
- Allowed: backend-specific hook implementations.
- Not allowed: language-agnostic semantic lowering.

#### 3.2.1 Standard backend pipeline directories

- The standard backend layout is `src/backends/<lang>/{lower,optimizer,emitter}/`.
- Responsibilities are fixed as:
  - `lower/`: language-specific lowering from `EAST3 -> <LangIR>`
  - `optimizer/`: language-specific optimization on `<LangIR> -> <LangIR>`
  - `emitter/`: final rendering from `<LangIR> -> source text`
- New implementation work must be placed in these three layers, and must not add semantic lowering or optimizer-equivalent logic into `emitter/`.
- Existing backends may migrate in phases, but the target shape must converge to this same directory contract.
- The canonical guard for non-C++ 3-layer wiring and reverse-import prevention is `python3 tools/check_noncpp_east3_contract.py`.

#### 3.2.2 Extension directories (plan-2) and final target shape (plan-3)

- Current operation uses plan-2 (`core + extensions`).
  - core (required): `lower/`, `optimizer/`, `emitter/`
  - extension (optional): `extensions/<topic>/`
- Use fixed feature names under `extensions/`.
  - Examples: `extensions/runtime/`, `extensions/packaging/`, `extensions/integration/`
- Language-specific ad-hoc directory names such as `header/`, `multifile/`, `runtime_emit/`, `hooks/` are disallowed for new additions and should be migrated gradually into `extensions/<topic>/`.
- In a later plan-3 phase, extension features are moved out of `src/backends/<lang>/` and each backend converges toward a `lower/optimizer/emitter`-centric shape.

### 3.3 `src/backends/common/profiles/` and `src/backends/<lang>/profiles/`

- Purpose: declarative language-difference profiles.
- Allowed:
  - Shared defaults: `src/backends/common/profiles/core.json`
  - Per-language profiles: `src/backends/<lang>/profiles/{profile,types,operators,runtime_calls,syntax}.json`
- Not allowed: executable logic.

### 3.4 `src/runtime/`

- Purpose: target runtime implementations.
- Allowed: `src/runtime/<lang>/pytra/`.
- Not allowed: transpiler core logic.

### 3.5 `src/*_module/` (legacy compatibility)

- Purpose: compatibility with old layout.
- Allowed: existing compatibility assets only.
- Not allowed: new runtime implementations.
- Note: phased removal target; new implementations go to `src/runtime/<lang>/pytra/`.

## 4. Documentation Operation Boundaries

### 4.1 `docs/ja/todo/index.md`

- Purpose: open tasks only.
- Allowed: open IDs, priorities, short progress notes.
- Not allowed: completed history body.

### 4.2 `docs/ja/todo/archive/`

- Purpose: completed history by date.
- Allowed: `YYYYMMDD.md`, `index.md`.
- Not allowed: open tasks.

## 5. Placement Checklist

When adding a new file, verify:

1. Purpose matches the folder responsibility.
2. No violation of "not allowed" items.
3. Dependency direction does not reverse boundaries.
4. If boundaries change, update this spec and related specs in the same change.

## 6. Related Specifications

- Implementation: `docs/en/spec/spec-dev.md`
- EAST staged architecture: `docs/en/spec/spec-east.md#east-stages`
- EAST migration responsibility map: `docs/en/spec/spec-east.md#east-file-mapping`
- Runtime: `docs/en/spec/spec-runtime.md`
- Codex operations: `docs/en/spec/spec-codex.md`
