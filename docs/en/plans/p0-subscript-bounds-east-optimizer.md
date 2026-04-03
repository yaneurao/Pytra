# P0-SUBSCRIPT-BOUNDS: Migrate negative-index-mode / bounds-check-mode to the EAST optimizer

Last updated: 2026-04-02

## Background

The old toolchain's emitter had `--negative-index-mode` (`always` / `const_only` / `off`) and `--bounds-check-mode` (`always` / `debug` / `off`). The old defaults were `const_only` + `off`.

In toolchain2 these options were never migrated, and the C++ runtime's `py_list_at_ref` performs negative-index normalization + bounds checking on every `Subscript` access. This is the direct cause of the hot-loop indexing slowdown observed in 1600×1200 PNG output (millions of iterations).

### Design problem

In the old toolchain these options were **emitter options**. That is not the right design:
- The emitter should not know that these options exist
- Optimization decisions are the responsibility of the EAST optimizer
- The emitter only maps EAST3 metadata to output

## Approach

### Rename `--east3-opt-level` to `--opt-level` and integrate as an optimization preset

The old `--east3-opt-level` exposes an internal implementation name directly on the CLI. From the user's perspective it is simply an "optimization level", so it should be renamed to `--opt-level`.

`--opt-level` determines the defaults for `negative_index_mode` / `bounds_check_mode`, which can then be overridden individually:

| `--opt-level` | Meaning | `negative_index_mode` default | `bounds_check_mode` default |
|---|---|---|---|
| `0` | No optimization, full Python compatibility | `always` | `always` |
| `1` | Light optimization (default) | `const_only` | `off` |
| `2` | Aggressive optimization | `off` | `off` |

The individual options (`--negative-index-mode` / `--bounds-check-mode`) override the defaults set by `--opt-level`:
```
--opt-level 2 --negative-index-mode always   # aggressive optimization but always normalize negative indices
```

### Relationship between Python subscript semantics and negative_index / bounds_check

Python's `a[i]` works in the following steps:

```python
if i < 0:
    i += len(a)        # ← negative_index (normalization)
if i < 0 or i >= len(a):
    raise IndexError   # ← bounds_check (range check)
```

**negative_index and bounds_check are not independent — they are coupled.** `a[-100]` will still be negative after normalization, so it raises IndexError. If you apply bounds checking without normalization, negative numbers immediately raise IndexError (different behavior from Python).

| | bounds_check on | bounds_check off |
|---|---|---|
| **negative_index on** | Full Python compatibility | Normalizes, but out-of-range is undefined |
| **negative_index off** | Negative numbers immediately error (no normalization) | Everything undefined (fastest) |

**Handling of literal negative indices (`a[-1]`):**
- With `negative_index: off`, `a[-1]` is not normalized either. In C++, `vector[-1]` is undefined behavior. This is the user's choice.
- Treating literal negatives specially would make the meaning of `off` inconsistent.
- `off` truly means off. Code that uses `a[-1]` will break with `--opt-level 2`. With `--opt-level 1` (default), `const_only` means literal negatives are normalized.

### Responsibilities of EAST lowering / optimizer / emitter

Subscript processing is handled in two stages: **EAST2 → EAST3 lowering** and the **optimizer**:

**EAST2 → EAST3 lowering (static expansion of negative literals):**
- `negative_index_mode=always` / `const_only`: expands literal negatives like `a[-1]` to `a[len(a) - 1]`
- `negative_index_mode=off`: leaves literal negatives as-is (passes them through to the emitter)
- Variable indices are not touched during lowering (cannot determine statically whether they are negative)

**Optimizer (metadata attachment):**
- Attaches `meta.subscript_access_v1` to `Subscript` nodes:
  - `negative_index: "normalize" | "skip"` — whether runtime negative-index normalization (`if (i < 0) i += len`) is needed
  - `bounds_check: "full" | "off"` — whether range checking is needed
- Decision logic:
  - Subscript with index from a `ForRange` loop variable → `negative_index: "skip"`, `bounds_check: "off"` (always safe)
  - Lowered literals (confirmed non-negative) → `negative_index: "skip"`
  - Negative literals → `negative_index: "normalize"`, `bounds_check: "full"` (fail-closed: may still be out of range after normalization)
  - Variable indices → follow `negative_index_mode` setting
  - `bounds_check` → follow `bounds_check_mode` setting

**Emitter:**
- Only looks at metadata to select the runtime API:
  - `bounds_check: "full"` + `negative_index: "normalize"` → `py_list_at_ref` (existing, full check)
  - `bounds_check: "off"` + `negative_index: "skip"` → direct `operator[]` / native subscript
  - `bounds_check: "full"` + `negative_index: "skip"` → bounds check only, no normalization
  - `bounds_check: "off"` + `negative_index: "normalize"` → normalization only, no bounds check
- The emitter does not know about `--opt-level` / `--negative-index-mode` / `--bounds-check-mode` options themselves

## Target

- `src/toolchain2/optimize/` — add option and metadata attachment logic to the optimizer
- `docs/ja/spec/spec-east.md` — `meta.subscript_access_v1` schema definition
- `docs/ja/spec/spec-east3-optimizer.md` — append to optimizer pass specification
- `src/toolchain2/emit/cpp/emitter.py` — API selection based on metadata (emitter does not know about options)
- All emitters — same as above

## Out of scope

- Adding options to the emitter (prohibited)
- Improvements to `src/pytra/utils/png.py` proper (separate task, though synergistic)

## State of existing documentation

- `docs/en/spec/spec-options.md` documents `--negative-index-mode` / `--bounds-check-mode` / `-O0`~`-O3` as old emitter options
- `docs/ja/spec/archive/20260328-spec-options.md` is the Japanese version (archived)
- Both describe these as "emitter options"; there is no description as EAST optimizer options
- `docs/ja/tutorial/transpiler-cli.md` also lists `--bounds-check-mode` as an emitter CLI option
- `docs/ja/tutorial/advanced-usage.md` mentions `-O3`
- None of these have been migrated to toolchain2
- spec-east.md / spec-east3-optimizer.md also have no relevant entries

## Acceptance Criteria

- [ ] `--east3-opt-level` is renamed to `--opt-level`
- [ ] `--opt-level` determines the defaults for `negative_index_mode` / `bounds_check_mode`
- [ ] Individual overrides via `--negative-index-mode` / `--bounds-check-mode` work
- [ ] `Subscript` nodes have `meta.subscript_access_v1` attached
- [ ] The emitter references only metadata and does not know about the options themselves
- [ ] C++ sample 01 (mandelbrot) runtime is improved to be comparable to Rust/Go
- [ ] No regression in fixture + sample parity
- [ ] spec-options.md is updated and these are redefined as EAST optimizer options (emitter option descriptions removed)
- [ ] spec-east3-optimizer.md has the `subscript_access_v1` pass appended
- [ ] `docs/ja/tutorial/transpiler-cli.md` options section is updated (described as EAST optimizer options, not emitter options)
- [ ] `docs/ja/tutorial/advanced-usage.md` `-O3` description is updated

## Subtasks

1. [x] [ID: P0-SUB-BOUNDS-S1] Define `meta.subscript_access_v1` schema in spec-east.md
2. [ ] [ID: P0-SUB-BOUNDS-S1.5] Rename `--east3-opt-level` to `--opt-level` (pytra-cli2.py, runtime_parity_check_fast.py, optimizer, spec, tutorial — all locations)
3. [ ] [ID: P0-SUB-BOUNDS-S2] Implement `--opt-level` and `--negative-index-mode` / `--bounds-check-mode` coupling in the optimizer
   - `--opt-level` determines the defaults for `negative_index_mode` / `bounds_check_mode`
   - Individual overrides via `--negative-index-mode` / `--bounds-check-mode` work
   - Add `negative_index_mode` / `bounds_check_mode` parameters to `optimize_east3_document()`
   - Add `--opt-level` / `--negative-index-mode` / `--bounds-check-mode` to `runtime_parity_check_fast.py` and thread them to the optimizer
4. [ ] [ID: P0-SUB-BOUNDS-S3] Implement metadata-based direct index / py_list_at_ref branching in the C++ emitter
5. [ ] [ID: P0-SUB-BOUNDS-S4] Confirm that C++ sample 01 (mandelbrot) runtime is improved
6. [ ] [ID: P0-SUB-BOUNDS-S5] Confirm no regression in fixture + sample + stdlib parity
7. [ ] [ID: P0-SUB-BOUNDS-S6] Add negative index regression fixtures — fixtures containing `a[-1]` / `a[-2]` that FAIL if the optimizer incorrectly attaches `negative_index: skip`

## Decision Log

- 2026-04-02: Investigated why C++ sample 01 is slow compared to Python (12.8s vs 34.9s, Rust 1.9s). Root cause is that `py_list_at_ref` in the PNG runtime performs bounds checking + negative normalization on every call. The old toolchain had `bounds_check_mode=off` as default but it was never migrated to toolchain2. Filed ticket to redesign this as the responsibility of the EAST optimizer rather than an emitter option.
- 2026-04-02: `--east3-opt-level` exposes an internal implementation name on the CLI, so it will be renamed to `--opt-level`. `--opt-level` will determine the defaults for `negative_index_mode` / `bounds_check_mode`, with individual options able to override them.
