<a href="../../docs-ja/spec/spec-folder.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Folder Responsibility Map Specification (Pytra)

This document is the source of truth for placement decisions: which folder should contain what.
Algorithm details belong to other specs (`spec-dev.md`, `spec-east123.md`, `spec-runtime.md`); this file defines boundaries only.

## 1. Scope

- In scope:
  - Repository top-level folders
  - Major responsibility boundaries under `src/`
  - `docs-ja/todo/` operation boundaries
- Out of scope:
  - Detailed algorithms
  - Full per-language support matrix

## 2. Top-Level Folder Responsibilities

### 2.1 `src/`

- Purpose: transpiler implementation, shared libraries, and target runtimes.
- Allowed: `py2*.py`, `src/pytra/`, `src/runtime/<lang>/pytra/`, `src/hooks/`, `src/profiles/`.
- Not allowed: logs, temporary outputs, process docs.

### 2.2 `test/`

- Purpose: regression tests and fixtures.
- Allowed: unit/integration tests, fixtures.
- Not allowed: production implementation.

### 2.3 `sample/`

- Purpose: public sample inputs/outputs and comparison artifacts.
- Allowed: `sample/py`, `sample/<lang>`, `sample/images`, `sample/golden`.
- Not allowed: unorganized local experiments.

### 2.4 `docs-ja/`

- Purpose: source of truth documentation.
- Allowed: `spec/`, `plans/`, `todo/`, `language/`, `news/`.
- Not allowed: implementation code.

### 2.5 `docs/`

- Purpose: English translation mirror of `docs-ja/`.
- Allowed: translated counterparts of `docs-ja/`.
- Not allowed: upstream-first edits diverging from `docs-ja/`.

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

- Purpose: EAST1/EAST2/EAST3 stage processing and shared emitter foundation.
- Allowed: `east1.py`, `east2.py`, `east3.py`, `east3_lowering.py`, `east_io.py`, `core.py`, `code_emitter.py`.
- Not allowed: target-language-specific final emission branches.
- Dependency rule: allow `pytra.*` shared layers; avoid direct dependency on `hooks/<lang>`.

### 3.2 `src/hooks/`

- Purpose: absorb target-language syntax differences.
- Allowed: backend-specific hook implementations.
- Not allowed: language-agnostic semantic lowering.

### 3.3 `src/profiles/`

- Purpose: declarative language-difference profiles.
- Allowed: `types/operators/runtime_calls/syntax` maps.
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

### 4.1 `docs-ja/todo/index.md`

- Purpose: open tasks only.
- Allowed: open IDs, priorities, short progress notes.
- Not allowed: completed history body.

### 4.2 `docs-ja/todo/archive/`

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

- Implementation: `docs-ja/spec/spec-dev.md`
- EAST staged architecture: `docs-ja/spec/spec-east123.md`
- EAST migration responsibility map: `docs-ja/spec/spec-east123-migration.md`
- Runtime: `docs-ja/spec/spec-runtime.md`
- Codex operations: `docs-ja/spec/spec-codex.md`
