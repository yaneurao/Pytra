<a href="../../ja/spec/spec-east3-optimizer.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# EAST3 Optimizer Specification

This document defines the responsibilities, contracts, and staged rollout of the `EAST3` optimization layer, `EAST3 -> EAST3`.

## 1. Objective

- Optimize `EAST3` immediately before the emitter to improve generated-code quality and runtime performance.
- Separate optimization logic from the emitter to improve maintainability.
- Separate reusable cross-language optimizations from language-specific optimizations used only when needed.

## 2. Non-goals

- Replacing syntax or type-resolution logic at `EAST2` and earlier.
- Taking over backend-specific final formatting or syntax-sugar responsibilities.
- Lowering directly into backend syntax, for example generating C++ `for (init; cond; inc)` forms.
- Any optimization that changes semantics and breaks strict compatibility.

## 3. Pipeline position

The standard pipeline order is:

1. `EAST2 -> EAST3` lowering, `east2_to_east3_lowering.py`
2. shared `EAST3 Optimizer`
3. `EAST3 Optimizer <lang>`, optional and language-specific
4. each emitter

Notes:

- The optimizer accepts only `EAST3` as input.
- Do not distribute optimization logic into the pre-`EAST3` stage, the `EAST2` stage.

## 4. Input and output contract

### 4.1 Input

- An `EAST3` document with `kind == "Module"`
- It must satisfy `east_stage == 3`

### 4.2 Output

- The return value is also an `EAST3` document, `EAST3 -> EAST3`.
- It must preserve the following invariants.
  - `east_stage` stays `3`
  - `schema_version` stays within the compatible range
  - `source_span`, `repr`, `resolved_type`, `borrow_kind`, and `casts` are not broken
  - the `main_guard_body` separation contract is preserved

## 5. Safety contract, semantic preservation

- Semantic preservation takes highest priority.
- The optimizer must not change:
  - evaluation order
  - exception timing
  - whether side effects occur, or how many times
  - the conditions that make short-circuit evaluation succeed
- Reordering across expressions that may have side effects is forbidden.
- Uncertain transformations must be skipped rather than forced, fail-closed.

## 6. Structure, pass manager

`EAST3 Optimizer` is composed as a sequence of passes.

- `PassContext`
  - `opt_level`
  - `target_lang`, may be empty
  - `debug_flags`
  - `non_escape_policy`
    - `unknown_call_escape`, treat unresolved calls as escape
    - `unknown_attr_call_escape`, treat dynamic attribute calls as escape
    - `global_write_escape`, treat global and nonlocal writes as escape
    - `return_escape_by_default`, treat return boundaries as escape by default
    - `yield_escape_by_default`, treat yield boundaries as escape by default
- `PassResult`
  - `changed: bool`
  - `change_count: int`
  - `warnings: list[str]`
  - `elapsed_ms: float`

Execution contract:

- Passes must be deterministic.
- The same input and the same options must always produce the same output.
- Pass order is fixed, and ordering dependencies must be explicit.

## 7. Optimization levels

- `O0`, disabled:
  - do not run the optimizer
- `O1`, default:
  - only local passes with strong semantic-preservation guarantees
- `O2`:
  - `O1` plus conservative loop-related optimizations

## 8. v1 pass set, implementation-aligned as of 2026-03-07

| Pass | opt-level | Status | Representative transformation | Main guard |
| --- | --- | --- | --- | --- |
| `NoOpCastCleanupPass` | `O1` | Implemented | Remove cast entries where `from == to` | Only when type equality is proven statically |
| `LiteralCastFoldPass` | `O1` | Implemented | Fold literal `static_cast` calls into `Constant` | Literals only and only lossless, same-type conversion |
| `RangeForCanonicalizationPass` | `O1` | Implemented | `RuntimeIterForPlan(py_range)` -> `StaticRangeForPlan` | Currently limited to constant integer args, 1 to 3 args, and `step != 0` |
| `ExpressionNormalizationPass` | `O1` | Implemented | Preserve `BinOp/Compare` and `ForCore(StaticRange)` condition expressions structurally as `normalized_expr(_version)` | Paths not satisfying `normalized_expr_version=east3_expr_v1` must fall back or fail closed in the backend |
| `LifetimeAnalysisPass` | `O1` | Implemented | Annotate intra-function `CFG + def-use + liveness + last_use` | If dynamic name resolution, `locals/globals/vars/eval/exec`, is detected, set `fail_closed` |
| `UnusedLoopVarElisionPass` | `O1` | Implemented | Replace unused `NameTarget` with `_` | Not applied if the variable is referenced in the loop body, `orelse`, later code, or via dynamic name resolution |
| `LoopInvariantHoistLitePass` | `O2` | Implemented | Hoist invariant assignments at the start of a non-empty `StaticRangeForPlan` into the preheader | Requires proof of non-empty loop, no side effects, and no reassignment |
| `StrengthReductionFloatLoopPass` | `O2` | Implemented | Convert float `x / C` to `x * (1/C)` | Only when `C` is a finite, non-zero constant whose absolute value is a power of two |
| `RedundantWrapperCtorPass` | - | Candidate, not implemented | Remove redundant cases such as `bytes(bytes_expr)` | Temporary value only and no alias risk |
| `DeadTempCleanupPass` | - | Candidate, not implemented | Remove unused temporaries | No references and no side effects |

Notes:

- The current implementation intentionally keeps the application range narrow and prioritizes fail-closed behavior.
- `O0` disables all passes, `O1` runs the `O1` passes in the table, and `O2` runs `O1 + O2`.
- `NonEscapeInterproceduralPass` and `ContainerValueLocalHintPass`, formerly `CppListValueLocalHintPass` and generalized and renamed on 2026-03-23, are no longer part of the default local `EAST3` pass list as of 2026-03-07. They are treated instead as whole-program and global-annotation passes on the `LinkedProgramOptimizer` side.
- `LifetimeAnalysisPass` remains a local-only pass and does not move into the linked-program stage.

### 8.1 Responsibility boundary for optimizing `for ... in range(...)`

- The shared optimizer may convert `for ... in range(...)` into a backend-independent normalized representation.
- A form such as `for _ in range(5)` must not be optimized merely because the variable name is `_`. It is optimized only when actual-use analysis proves that the variable is unused.
- Do not apply the transformation unless the following are proven statically safe:
  - the loop variable is referenced nowhere in the body, `else`, or after the loop
  - it cannot be observed by closure capture
  - it cannot be observed through dynamic name resolution, such as `locals`, `globals`, `vars`, or `eval`
- Language-structural forms such as C++ `for (i = 0; i < n; ++i)` belong to `EAST3 -> <lang>` lowering or to the emitter, not to the shared optimizer.

### 8.2 Responsibility boundary for expression normalization, EAST3 versus emitter

- Expression normalization whose meaning is shared across backends, for example identity-cast removal, simplification of `StaticRange` trip-count and condition expressions, and normalization of compare chains, belongs in `EAST3 -> EAST3`.
- The normalized result should be kept as a structured representation, node or metadata, so the emitter can reference it without recomputing it.
- The emitter's responsibility is limited to mapping into target-language surface notation.
  - operator spelling
  - standard-library or API names
  - minimal precedence parentheses
  - notation differences required by the target language, for example `Math.floor`-style forms
- For expression categories that already carry normalized information, the emitter must not rebuild an equivalent expression string.
- If normalized information is missing or malformed, fail closed and suppress the optimized output path rather than allowing invalid `reserve` or condition-expression generation.
- Policy: semantic decisions belong to EAST3, notation decisions belong to the emitter.

### 8.3 Structured contract for `normalized_expr`, v1

When EAST3 passes a normalized expression downstream, the recommended contract is:

- `normalized_expr_version: "east3_expr_v1"`
- `normalized_expr: <EAST3 expression node>`
  - allowed subset in v1: `Constant`, `Name`, `BinOp`, `Compare`, `IfExp`
  - it preserves `resolved_type`, `borrow_kind`, and `casts`

Operational rules:

- Existing category-specific metadata such as `trip_count`, for example `reserve_hints[*].count_expr`, must also satisfy `east3_expr_v1`.
- If `normalized_expr_version` is unknown, or `normalized_expr` is missing or malformed, the emitter disables that normalized route, fail-closed.
- In fail-closed mode, the emitter must not generate code whose meaning changes. If necessary, it should return to the previous path or leave the optimization unapplied.

### 8.4 `lifetime_analysis` annotation contract, `east3_lifetime_v1`

`LifetimeAnalysisPass` annotates `FunctionDef`, and methods inside `ClassDef`, with the following:

- `meta.lifetime_analysis.schema_version = "east3_lifetime_v1"`
- `meta.lifetime_analysis.status`
  - `ok`
  - `fail_closed`, when dynamic name resolution is detected
- `meta.lifetime_analysis.reason`
  - when `status=fail_closed`, use `dynamic_name_access`
- `meta.lifetime_analysis.cfg`
  - array of nodes, `id`, `kind`, `defs`, `uses`, `succ`
- `meta.lifetime_analysis.def_use`
  - `defs: dict[name, node_id[]]`
  - `uses: dict[name, node_id[]]`
- `meta.lifetime_analysis.variables`
  - `def_nodes`, `use_nodes`, `live_in_nodes`, `live_out_nodes`, `last_use_nodes`, `lifetime_class`

Each statement node, each CFG node, is additionally annotated with:

- `meta.lifetime_node_id`
- `meta.lifetime_defs`
- `meta.lifetime_uses`
- `meta.lifetime_live_in`
- `meta.lifetime_live_out`
- `meta.lifetime_last_use_vars`

Rules for `lifetime_class`, v1:

- Default: `local_non_escape_candidate`
- Use `escape_or_unknown` in any of the following cases:
  - `status=fail_closed`
  - the variable is used in `Return` or `Yield`
  - `escape_summary.arg_escape[i] == true` for that argument

Fail-closed rules:

- If a function contains calls to `locals`, `globals`, `vars`, `eval`, or `exec`, set `status=fail_closed`.
- In a `fail_closed` function, do not create lifetime-optimization candidates. Downstream backends must treat them as `escape_or_unknown`.

## 9. Language-specific optimization layers

- After the shared layer, an optional `east3_optimizer_<lang>.py` may be added.
- A language-specific layer must obey the following.
  - the same semantic-preservation contract as the shared layer
  - limited to code-generation needs that are genuinely language-specific
  - language-structural lowering, for example classic C++ `for` syntax, belongs here or in the emitter
  - do not duplicate an optimization in the language-specific layer if it can be expressed in the shared layer

Recommended file placement:

- `src/toolchain/misc/east_parts/east3_optimizer.py`
- `src/toolchain/misc/east_parts/east3_optimizer_cpp.py`
- `src/toolchain/misc/east_parts/east3_opt_passes/*.py`

## 10. CLI and debug contract

Recommended options:

- `--east3-opt-level {0,1,2}`, default `1`
- `--east3-opt-pass +PASS,-PASS`, per-pass on/off
- `--dump-east3-before-opt <path>`
- `--dump-east3-after-opt <path>`
- `--dump-east3-opt-trace <path>`

Recommended trace contents:

- pass execution order
- `changed`, `change_count`, and `elapsed_ms` for each pass
- final summary, total change count and total time

### 10.1 Operating procedure for trace inspection and isolation

1. First, take EAST3 dumps and a trace with the default `O1`.

```bash
python3 src/pytra-cli.py sample/py/01_mandelbrot.py --target cpp -o out.cpp \
  --dump-east3-before-opt work/logs/east3_before.json \
  --dump-east3-after-opt work/logs/east3_after.json \
  --dump-east3-opt-trace work/logs/east3_trace.txt
```

2. If a problem appears, disable passes one by one with `--east3-opt-pass` and isolate the responsible pass, for example `-RangeForCanonicalizationPass`.

```bash
python3 src/pytra-cli.py sample/py/01_mandelbrot.py --target cpp -o out.cpp \
  --east3-opt-level 2 \
  --east3-opt-pass -RangeForCanonicalizationPass,-UnusedLoopVarElisionPass
```

3. Compare compatibility among `O0`, `O1`, and `O2` using the same procedure through `runtime_parity_check.py --east3-opt-level`.

```bash
python tools/check/runtime_parity_check.py --case-root sample --all-samples \
  --targets cpp,rs,cs,js,ts --ignore-unstable-stdout \
  --east3-opt-level 0 --summary-json work/logs/east3_opt_parity_o0.json
python tools/check/runtime_parity_check.py --case-root sample --all-samples \
  --targets cpp,rs,cs,js,ts --ignore-unstable-stdout \
  --east3-opt-level 1 --summary-json work/logs/east3_opt_parity_o1.json
python tools/check/runtime_parity_check.py --case-root sample --all-samples \
  --targets cpp,rs,cs,js,ts --ignore-unstable-stdout \
  --east3-opt-level 2 --summary-json work/logs/east3_opt_parity_o2.json
```

## 11. Test contract

Minimum requirements:

- single-pass unit tests, comparing input and output EAST3
- syntax and type invariant tests, such as `east_stage`, `schema_version`, and `resolved_type`
- regression tests on major `sample/` cases
- output consistency in existing parity tests, stdout and artifacts

Points that must be checked carefully:

- behavior remains stable when switching between `O0` and `O1/O2`
- transformations are correctly suppressed in cases where they must not be applied

## 12. Introduction phases

### Phase 1

- skeleton implementation of the pass manager
- `O0/O1` and trace output
- introduction of `NoOpCastCleanup` and `LiteralCastFold`

### Phase 2

- loop-related optimizations, `LoopInvariantHoistLite` and `StrengthReductionFloatLoop`
- add entrypoints for language-specific optimizers

### Phase 3

- profile-driven policy for pass enablement
- baseline measurement and automatic regression detection for long-term operation

## 13. Compatibility policy

- Keep the existing emitter API.
- Use `O1` as the default, but always provide `O0` so problems can be isolated.
- When adding a new optimizer, preserving output equality on existing fixtures and samples is mandatory.
