<a href="../../ja/spec/spec-east3-optimizer.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# EAST3 Optimizer Specification

This document defines the responsibilities, contracts, and staged rollout of the `EAST3` optimization layer (`EAST3 -> EAST3`).

## 1. Objective

- Optimize `EAST3` immediately before the emitter to improve generated-code quality and runtime performance.
- Separate optimization logic from the emitter to improve maintainability.
- Separate reusable cross-language optimizations from language-specific optimizations that are only needed in some targets.

## 2. Non-Goals

- Replacing syntax or type-resolution logic from `EAST2` and earlier.
- Replacing backend-specific final formatting or syntax sugar responsibilities.
- Lowering directly into backend syntax, for example generating C++ `for (init; cond; inc)` forms here.
- Applying optimizations that change semantics and break strict compatibility.

## 3. Position in the Pipeline

The canonical pipeline order is:

1. `EAST2 -> EAST3` lowering (`east2_to_east3_lowering.py`)
2. `EAST3 Optimizer` (shared)
3. `EAST3 Optimizer <lang>` (optional, per language)
4. each emitter

Notes:

- The optimizer accepts only `EAST3` as input.
- Do not distribute optimization logic into pre-`EAST3` (`EAST2`) stages.

## 4. Input / Output Contract

### 4.1 Input

- An `EAST3` document with `kind == "Module"`.
- It must satisfy `east_stage == 3`.

### 4.2 Output

- The return value is also an `EAST3` document (`EAST3 -> EAST3`).
- It must preserve the following invariants:
  - `east_stage` stays `3`
  - `schema_version` stays within the compatible range
  - `source_span`, `repr`, `resolved_type`, `borrow_kind`, and `casts` are not corrupted
  - the `main_guard_body` separation contract is preserved

## 5. Safety Contract (Semantic Preservation)

- Semantic preservation has top priority.
- The optimizer must not change:
  - evaluation order
  - exception timing
  - the presence or number of side effects
  - short-circuit conditions
- Reordering across expressions that may have side effects is forbidden.
- Uncertain transformations must be skipped rather than forced (fail-closed).

## 6. Structure (Pass Manager)

`EAST3 Optimizer` is structured as a sequence of passes.

- `PassContext`
  - `opt_level`
  - `target_lang` (may be empty)
  - `debug_flags`
  - `non_escape_policy`
    - `unknown_call_escape` (treat unresolved calls as escape)
    - `unknown_attr_call_escape` (treat dynamic attribute calls as escape)
    - `global_write_escape` (treat global/nonlocal writes as escape)
    - `return_escape_by_default` (treat return boundaries as escape by default)
    - `yield_escape_by_default` (treat yield boundaries as escape by default)
- `PassResult`
  - `changed: bool`
  - `change_count: int`
  - `warnings: list[str]`
  - `elapsed_ms: float`

Execution contract:

- Each pass must be deterministic.
- The same input with the same options must always produce the same output.
- Pass order is fixed, and any ordering dependency must be explicit.

## 7. Optimization Levels

- `O0` (disabled):
  - do not run the optimizer
- `O1` (default):
  - only local passes with strong semantic-preservation guarantees
- `O2`:
  - `O1` plus conservative loop-related optimizations

## 8. v1 Pass Set (Implementation-Aligned: 2026-03-07)

| Pass | opt-level | status | representative transformation | main guard |
| --- | --- | --- | --- | --- |
| `NoOpCastCleanupPass` | `O1` | implemented | remove cast entries where `from == to` | only when type equality is proven statically |
| `LiteralCastFoldPass` | `O1` | implemented | fold literal `static_cast` calls into `Constant` | literals only, and only lossless same-type conversion |
| `RangeForCanonicalizationPass` | `O1` | implemented | `RuntimeIterForPlan(py_range)` -> `StaticRangeForPlan` | currently only constant integer arity 1..3 and `step != 0` |
| `ExpressionNormalizationPass` | `O1` | implemented | structurally preserve `BinOp/Compare` and `ForCore(StaticRange)` condition expressions as `normalized_expr(_version)` | paths not satisfying `normalized_expr_version=east3_expr_v1` must fall back or fail closed in the backend |
| `LifetimeAnalysisPass` | `O1` | implemented | annotate intra-function `CFG + def-use + liveness + last_use` | if dynamic name resolution (`locals/globals/vars/eval/exec`) is detected, mark `fail_closed` |
| `UnusedLoopVarElisionPass` | `O1` | implemented | replace unused `NameTarget` with `_` | skip if referenced in loop body, `orelse`, later code, or dynamic-name access |
| `LoopInvariantHoistLitePass` | `O2` | implemented | hoist invariant assignments from the first iteration of a non-empty `StaticRangeForPlan` into the preheader | requires proof of non-empty loop, no side effects, and no reassignment |
| `StrengthReductionFloatLoopPass` | `O2` | implemented | convert float `x / C` into `x * (1/C)` | only when `C` is a finite non-zero constant whose absolute value is a power of two |
| `RedundantWrapperCtorPass` | - | candidate, not implemented | remove redundant cases such as `bytes(bytes_expr)` | temporary value only and no alias risk |
| `DeadTempCleanupPass` | - | candidate, not implemented | remove unused temporaries | no references and no side effects |

Notes:

- The current implementation intentionally keeps the application range narrow and prioritizes fail-closed behavior.
- `O0` runs no passes, `O1` runs the `O1` passes above, and `O2` runs `O1 + O2`.
- As of 2026-03-07, `NonEscapeInterproceduralPass` and `CppListValueLocalHintPass` have been removed from the default local `EAST3` pass list and are treated on the `LinkedProgramOptimizer` side as whole-program/global annotation passes.
- `LifetimeAnalysisPass` remains a local-only pass and does not move into the linked-program stage.

### 8.1 Responsibility Boundary for Optimizing `for ... in range(...)`

- The shared optimizer may convert `for ... in range(...)` into a backend-independent normalized representation.
- Forms such as `for _ in range(5)` must not be optimized merely because the variable name is `_`; apply the optimization only when actual usage analysis proves the variable is unused.
- Do not apply the transformation unless the following are statically proven safe:
  - the loop variable is not referenced in the body, the `else`, or after the loop
  - it cannot be observed through closure capture
  - it cannot be observed through dynamic name resolution such as `locals`, `globals`, `vars`, or `eval`
- Language-specific structural forms such as C++ `for (i = 0; i < n; ++i)` belong to `EAST3 -> <lang>` lowering or to the emitter, not to the shared optimizer.

### 8.2 Responsibility Boundary for Expression Normalization (EAST3 vs emitter)

- Expression normalization whose meaning is shared across backends, such as removing identity casts, simplifying `StaticRange` trip-count or condition expressions, and normalizing compare chains, should be performed in `EAST3 -> EAST3`.
- The normalized result should be kept as a structured representation (node or metadata) so the emitter can reference it without recomputing it.
- The emitter is restricted to mapping into target-language surface syntax.
  - operator spelling
  - standard-library / API names
  - minimal precedence parentheses
  - target-language constraints such as `Math.floor`-style forms
- For expression categories that already carry normalized information, emitters must not rebuild equivalent expressions as strings.
- If normalized information is missing or malformed, fail closed and suppress the optimized output path instead of allowing invalid `reserve` or conditional generation.
- Policy: semantic decisions belong to EAST3, spelling decisions belong to the emitter.

### 8.3 Structured Contract for `normalized_expr` (v1)

When EAST3 passes a normalized expression downstream, the recommended contract is:

- `normalized_expr_version: "east3_expr_v1"`
- `normalized_expr: <EAST3 expression node>`
  - allowed subset in v1: `Constant`, `Name`, `BinOp`, `Compare`, `IfExp`
  - it preserves `resolved_type`, `borrow_kind`, and `casts`

Operational rules:

- Existing category-specific metadata such as `trip_count` and `reserve_hints[*].count_expr` must also satisfy `east3_expr_v1`.
- If `normalized_expr_version` is unknown, or `normalized_expr` is missing or malformed, the emitter disables that normalized route (fail-closed).
- Fail-closed handling must not generate semantically different code. Fall back to the old path or disable the optimization entirely.

### 8.4 `lifetime_analysis` Annotation Contract (`east3_lifetime_v1`)

`LifetimeAnalysisPass` annotates `FunctionDef` and methods inside `ClassDef` with:

- `meta.lifetime_analysis.schema_version = "east3_lifetime_v1"`
- `meta.lifetime_analysis.status`
  - `ok`
  - `fail_closed` (dynamic name resolution detected)
- `meta.lifetime_analysis.reason`
  - `dynamic_name_access` when `status=fail_closed`
- `meta.lifetime_analysis.cfg`
  - node array with `id`, `kind`, `defs`, `uses`, `succ`
- `meta.lifetime_analysis.def_use`
  - `defs: dict[name, node_id[]]`
  - `uses: dict[name, node_id[]]`
- `meta.lifetime_analysis.variables`
  - `def_nodes`, `use_nodes`, `live_in_nodes`, `live_out_nodes`, `last_use_nodes`, `lifetime_class`

Each statement node that corresponds to a CFG node also carries:

- `meta.lifetime_node_id`
- `meta.lifetime_defs`
- `meta.lifetime_uses`
- `meta.lifetime_live_in`
- `meta.lifetime_live_out`
- `meta.lifetime_last_use_vars`

Rules for `lifetime_class` (v1):

- Default: `local_non_escape_candidate`
- Escalate to `escape_or_unknown` when any of the following holds:
  - `status=fail_closed`
  - the variable is used by `Return` or `Yield`
  - the argument has `escape_summary.arg_escape[i] == true`

Fail-closed rules:

- Any function that calls `locals`, `globals`, `vars`, `eval`, or `exec` becomes `status=fail_closed`.
- In a `fail_closed` function, do not produce lifetime optimization candidates. Downstream backends must treat them as `escape_or_unknown`.

## 9. Language-Specific Optimization Layer

- After the shared layer, `east3_optimizer_<lang>.py` may be added optionally.
- The language-specific layer must follow:
  - the same semantic-preservation contract as the shared layer
  - restriction to target-specific codegen concerns
  - language-structural lowering such as classical C++ `for` syntax belongs here or in the emitter
  - do not duplicate in a language-specific layer an optimization that can be represented in the shared layer

Recommended file layout:

- `src/toolchain/compiler/east_parts/east3_optimizer.py`
- `src/toolchain/compiler/east_parts/east3_optimizer_cpp.py`
- `src/toolchain/compiler/east_parts/east3_opt_passes/*.py`

## 10. CLI / Debug Contract

Recommended options:

- `--east3-opt-level {0,1,2}` (default `1`)
- `--east3-opt-pass +PASS,-PASS` (per-pass enable/disable)
- `--dump-east3-before-opt <path>`
- `--dump-east3-after-opt <path>`
- `--dump-east3-opt-trace <path>`

Recommended trace contents:

- executed pass order
- `changed/change_count/elapsed_ms` per pass
- final totals (total changes, total time)

### 10.1 Operational Procedure (Trace Inspection / Isolation)

1. First, dump EAST3 and the trace at default `O1`.

```bash
python3 src/py2x.py sample/py/01_mandelbrot.py --target cpp -o out.cpp \
  --dump-east3-before-opt work/logs/east3_before.json \
  --dump-east3-after-opt work/logs/east3_after.json \
  --dump-east3-opt-trace work/logs/east3_trace.txt
```

2. If a problem appears, disable passes individually through `--east3-opt-pass` and isolate the responsible pass, for example `-RangeForCanonicalizationPass`.

```bash
python3 src/py2x.py sample/py/01_mandelbrot.py --target cpp -o out.cpp \
  --east3-opt-level 2 \
  --east3-opt-pass -RangeForCanonicalizationPass,-UnusedLoopVarElisionPass
```

3. Compare `O0/O1/O2` compatibility through `runtime_parity_check.py --east3-opt-level`.

```bash
python tools/runtime_parity_check.py --case-root sample --all-samples \
  --targets cpp,rs,cs,js,ts --ignore-unstable-stdout \
  --east3-opt-level 0 --summary-json work/logs/east3_opt_parity_o0.json
python tools/runtime_parity_check.py --case-root sample --all-samples \
  --targets cpp,rs,cs,js,ts --ignore-unstable-stdout \
  --east3-opt-level 1 --summary-json work/logs/east3_opt_parity_o1.json
python tools/runtime_parity_check.py --case-root sample --all-samples \
  --targets cpp,rs,cs,js,ts --ignore-unstable-stdout \
  --east3-opt-level 2 --summary-json work/logs/east3_opt_parity_o2.json
```

## 11. Test Contract

Minimum requirements:

- pass-level unit tests (diffing input EAST3 against output EAST3)
- syntax and type invariant tests (`east_stage`, `schema_version`, `resolved_type`, and similar)
- regression tests over representative `sample/` cases
- output consistency under existing parity tests (stdout and generated artifacts)

Particular points to verify:

- behavior stays stable when switching between `O0` and `O1/O2`
- cases that should not be optimized are actually suppressed

## 12. Rollout Phases

### Phase 1

- skeleton implementation of the Pass Manager
- `O0/O1` and trace output
- introduction of `NoOpCastCleanup` and `LiteralCastFold`

### Phase 2

- loop-related optimization (`LoopInvariantHoistLite`, `StrengthReductionFloatLoop`)
- add the entry point for language-specific optimizers

### Phase 3

- profile-driven pass enablement policy
- baseline measurement for long-term operation and automatic regression detection

## 13. Compatibility Policy

- Keep the existing emitter API.
- Default to `O1`, but always provide `O0` for problem isolation.
- When adding optimizer behavior, keeping existing fixture/sample outputs compatible is mandatory.
