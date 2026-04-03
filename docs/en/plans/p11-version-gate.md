<a href="../../en/plans/p11-version-gate.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P11-VERSION-GATE: New version checker for toolchain2

Last updated: 2026-03-30
Status: Retired — parity check + progress matrix serve as replacements, so an internal version gate was deemed unnecessary. The old checker and old version file have also been retired.

## Background

The current version gate (`tools/check/check_transpiler_version_gate.py`) assumes the toolchain1 directory structure (`src/toolchain/`). As migration to toolchain2 (`src/toolchain2/`) progresses, the version file (`src/toolchain/misc/transpiler_versions.json`) and dependency path definitions have diverged from reality.

A new version checker aligned to toolchain2 would be created and the old checker retired.

## Design

### 1. New version file

Create `src/toolchain2/transpiler_versions.json`.

```json
{
  "shared": {"version": "1.0.0"},
  "cpp": {"version": "1.0.0"},
  "rs": {"version": "1.0.0"},
  "cs": {"version": "1.0.0"},
  "powershell": {"version": "1.0.0"},
  "js": {"version": "1.0.0"},
  "ts": {"version": "1.0.0"},
  "dart": {"version": "1.0.0"},
  "go": {"version": "1.0.0"},
  "java": {"version": "1.0.0"},
  "swift": {"version": "1.0.0"},
  "kotlin": {"version": "1.0.0"},
  "ruby": {"version": "1.0.0"},
  "lua": {"version": "1.0.0"},
  "scala": {"version": "1.0.0"},
  "php": {"version": "1.0.0"},
  "nim": {"version": "1.0.0"},
  "julia": {"version": "1.0.0"},
  "zig": {"version": "1.0.0"}
}
```

- Components are `shared` (shared pipeline) + 18 per-language entries
- `shared` covers `src/toolchain2/parse/`, `src/toolchain2/resolve/`, `src/toolchain2/compile/`, `src/toolchain2/optimize/`, `src/toolchain2/link/`, `src/toolchain2/emit/common/`
- Per-language entries cover `src/toolchain2/emit/<lang>/`
- Languages that do not yet have a toolchain2 emitter are initialized at `1.0.0` (PATCH bump when the emitter is added)

### 2. Dependency path definitions

Define which files, when changed, should trigger a version bump for which component.

| Component | Watch paths |
|---|---|
| `shared` | `src/toolchain2/parse/`, `src/toolchain2/resolve/`, `src/toolchain2/compile/`, `src/toolchain2/optimize/`, `src/toolchain2/link/`, `src/toolchain2/emit/common/` |
| `cpp` | `src/toolchain2/emit/cpp/`, `src/runtime/cpp/` |
| `go` | `src/toolchain2/emit/go/`, `src/runtime/go/` |
| `rs` | `src/toolchain2/emit/rs/`, `src/runtime/rs/` |
| `ts` | `src/toolchain2/emit/ts/`, `src/runtime/ts/`, `src/runtime/js/` |

### 3. Version update rules

- **PATCH**: Agents may update at their own discretion when emitter / runtime changes occur
- **MINOR / MAJOR**: Only with explicit user instruction

### 4. Checker behavior

Retrieve staged files via `git diff --cached`; if any file matches a watch path, verify that `transpiler_versions.json` has been updated with at least a PATCH bump for the corresponding component. Fail if not updated.

### 5. Retiring the old checker

Retire `tools/check/check_transpiler_version_gate.py` and `src/toolchain/misc/transpiler_versions.json`, moving them to `tools/unregistered/`.

## Prerequisites

Begin after the complete migration to toolchain2. At this point some toolchain1 code is still in use, so the old and new checkers would need to run in parallel.

## Decision Log

- 2026-03-29: Confirmed the need for a new version checker aligned to the toolchain2 directory structure. Filed as a TODO.
