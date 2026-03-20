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
- Allowed: `py2*.py`, `src/pytra/`, `src/runtime/<lang>/{generated,native}/`, `src/toolchain/emit/`. Legacy `pytra-gen/pytra-core` is rollout debt only.
- For non-C++/non-C# backends, checked-in `src/runtime/<lang>/pytra/**` must not exist; any re-entry is a contract failure.
- The canonical repo layout allows only `src/runtime/<lang>/{generated,native}/` as live runtime roots.
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

### 3.1 `src/toolchain/frontends/` / `src/toolchain/ir/` / `src/toolchain/compiler/` (3-layer + compat)

- Purpose: separate the input frontend and IR stage processing into `toolchain` sub-packages; `compiler` is being reduced to a compatibility facade.
- Allowed:
  - `src/toolchain/frontends/`: input-language frontend (e.g., `transpile_cli.py`, `python_frontend.py`, `east1_build.py`, `signature_registry.py`, `frontend_semantics.py`)
  - `src/toolchain/ir/`: EAST1/2/3 definitions, lowering, optimizer, pipeline (e.g., `core.py`, `east1.py`, `east2.py`, `east3.py`, `east3_optimizer.py`)
  - `src/toolchain/compiler/`: compatibility shim / facade (e.g., legacy import route receivers, backend registry)
- Not allowed:
  - re-adding to `compiler` any logic that has already been moved to `frontends` / `ir`
  - target-language-specific final emission branches
- Dependency direction:
  - canonical direction is `toolchain.frontends -> toolchain.ir -> backends`
  - `backends -> toolchain.frontends` is forbidden
  - `toolchain.compiler -> toolchain.frontends|toolchain.ir` is allowed as a compatibility layer
  - as a temporary exception, `toolchain.ir.core` may reference `toolchain.frontends.signature_registry|frontend_semantics` (scheduled for removal in the cycle-elimination task)

#### 3.1.1 Forbidden Old Import Paths (Migration Contract)

- Adding new imports to the old paths `pytra.frontends` / `pytra.ir` / `pytra.compiler` is forbidden.
- The canonical paths are `toolchain.frontends` / `toolchain.ir` / `toolchain.compiler`.
- Do not add re-export / alias shims to keep old paths alive (no backward-compatibility layer).
- Audit and removal of remaining references is done in phased migration; unmigrated references can be found with:
  - `rg -n "pytra\\.(frontends|ir|compiler)" src tools test`
  - `rg -n "toolchain\\.(frontends|ir|compiler)" src tools test`

### 3.2 `src/pytra/` (transpile-time reference library)

- Purpose: hold the Python namespace library (`pytra.std` / `pytra.utils` / `pytra.built_in`) that the transpiler references.
- Allowed: `src/pytra/std/`, `src/pytra/utils/`, `src/pytra/built_in/`
- Not allowed:
  - concrete implementations of `frontends` / `ir` / `compiler`
  - backend-specific logic

### 3.3 `src/toolchain/emit/`

- Purpose: absorb target-language syntax differences.
- Allowed: backend-specific hook implementations.
- Not allowed: language-agnostic semantic lowering.

#### 3.2.1 Standard backend pipeline directories

- The standard backend layout is `src/toolchain/emit/<lang>/{lower,optimizer,emitter}/`.
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
- In a later plan-3 phase, extension features are moved out of `src/toolchain/emit/<lang>/` and each backend converges toward a `lower/optimizer/emitter`-centric shape.

### 3.3 `src/toolchain/emit/common/profiles/` and `src/toolchain/emit/<lang>/profiles/`

- Purpose: declarative language-difference profiles.
- Allowed:
  - Shared defaults: `src/toolchain/emit/common/profiles/core.json`
  - Per-language profiles: `src/toolchain/emit/<lang>/profiles/{profile,types,operators,runtime_calls,syntax}.json`
- Not allowed: executable logic.

### 3.4 `src/runtime/`

- Purpose: target runtime implementations.
- Allowed: `src/runtime/<lang>/{generated,native}/`. Legacy backends may temporarily keep `pytra-gen/pytra-core`.
- Not allowed: transpiler core logic.

### 3.5 `src/*_module/` (legacy compatibility)

- Purpose: compatibility with old layout.
- Allowed: existing compatibility assets only.
- Not allowed: new runtime implementations.
- Note: phased removal target; new implementations go to the canonical lanes under `src/runtime/<lang>/{generated,native}/`.

## 4. Documentation Operation Boundaries

### 4.1 `docs/ja/todo/index.md`

- Purpose: open tasks only.
- Allowed: open IDs, priorities, short progress notes.
- Not allowed: completed history body.

### 4.2 `docs/ja/todo/archive/`

- Purpose: completed history by date.
- Allowed: `YYYYMMDD.md`, `index.md`.
- Not allowed: open tasks.

### 4.3 `docs/ja/spec/archive/`

- Purpose: store retired legacy specifications with a date stamp.
- Allowed: `YYYYMMDD-<slug>.md`, `index.md`.
- Not allowed: current specifications (those belong directly under `docs/ja/spec/`).

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
