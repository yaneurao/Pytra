<a href="../../en/todo/go.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Go backend

> Domain-specific TODO. See [index.md](./index.md) for the full index.

Last updated: 2026-03-31 (P3-GO-LINT-FIX complete)

## Operating Rules

- **The old toolchain1 (`src/toolchain/emit/go/`) must not be modified.** All new development and fixes go in `src/toolchain2/emit/go/` ([spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1).
- Each task requires an `ID` and a context file (`docs/ja/plans/*.md`).
- Work in priority order (lower P numbers first).
- Progress notes and commit messages must always include the same `ID`.
- **When a task is complete, change `[ ]` to `[x]` and append a completion note, then commit.**
- Completed tasks are periodically moved to `docs/ja/todo/archive/`.
- **Completion criteria for parity tests: "emit + compile + run + stdout match".**
- **You must read the [emitter implementation guide](../spec/spec-emitter-guide.md).** It covers the parity check tool, prohibited patterns, and how to use mapping.json.

## Incomplete Tasks

### P0-GO-TYPE-ID-CLEANUP: Remove pytra_isinstance / py_runtime_object_type_id from the Go runtime

Spec: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md) §6

Go has native `any` + type switch, so `pytra_isinstance` / `py_runtime_object_type_id` are unnecessary. The emitter should generate type switches directly.

1. [ ] [ID: P0-GO-TYPEID-CLN-S1] Remove `pytra_isinstance` and `py_runtime_object_type_id` from `src/runtime/go/built_in/py_runtime.go`
2. [ ] [ID: P0-GO-TYPEID-CLN-S2] Replace isinstance in the Go emitter with `switch v := x.(type)`
3. [ ] [ID: P0-GO-TYPEID-CLN-S3] Confirm no regressions in fixture + sample + stdlib parity

### P0-GO-BOOLOP-BOOL-SHORTCIRCUIT: Output and/or for bool types as && / ||

When both operands are comparison expressions and the expected type is `bool`, as in `if t > 0.0 and t < t_min:`, Go should output `if t > 0.0 && t < t_min {`. Currently the expression is expanded into an immediately-invoked closure as a value-selection expression, making the code significantly harder to read.

spec-east.md §7: "When the expected type is `bool`, output as a boolean operation (`&&`/`||`). When the expected type is something other than `bool`, output as a value-selection expression."

1. [x] [ID: P0-GO-BOOLOP-S1] Fix BoolOp emit in the Go emitter to output `&&` / `||` when `resolved_type` is `bool`
2. [x] [ID: P0-GO-BOOLOP-S2] Confirm Go parity PASS for `boolop_value_select` fixture + all sample 02 cases — typing 23/23, stdlib 16/16, sample 02 PASS

### P0-GO-TUPLE-MULTIRETURN: Fix incomplete tuple multi-return expansion

Review feedback: After converting `py_splitext` to multi-value return, the emitter's `_emit_assign` (`emitter.py:3780`) expands `tuple[...] = Call(...)` to `name_0, name_1 := ...`, but the original `name` itself is not bound, so `return name` / `f(name)` become undefined references. Additionally, `_emit_subscript` (`emitter.py:2915`) only rescues Names listed in `ctx.tup_multi_vars`, so direct subscripts like `os.path.splitext(p)[0]` produce invalid code.

1. [x] [ID: P0-GO-TUPLE-MR-S1] Either also bind the original variable name in tuple multi-return expansion, or emit direct subscripts (`Call(...)[0]`) as element selection from multi-return — added an implementation that expands `Call(...)[i]` via IIFE
2. [x] [ID: P0-GO-TUPLE-MR-S2] Confirm `os_glob_extended` / `pathlib_extended` fixtures compile + run parity PASS in Go — stdlib 4 cases, typing 23/23 PASS

### P0-RESOLVE-INT-PROMOTION: Fix integer promotion casts to attach to operands for all BinOp operators

For all BinOp operators (`+`, `-`, `*`, `/`, `//`, `%`, `&`, `|`, `^`, `<<`, `>>`), when integer types of different sizes are mixed, resolve should cast both operands to the result type **before** the operation. Currently it only casts the smaller side to the other's size, without a promotion cast to the result type. Go/Rust have no implicit promotion, so this causes compile errors.

Example: `m8: int8 = 100; m16: int16 = 100; r5: int32 = m8 * m16`
- Bad: `int16(m8) * m16` → result is int16 (possible overflow), no cast to int32
- Good: `int32(m8) * int32(m16)` → result is int32, no overflow

1. [x] [ID: P0-RESOLVE-INTPROMO-S1] Fix BinOp integer promotion in resolve to "promote to result type" for all operators — attach a cast to the result type on both operands
2. [x] [ID: P0-RESOLVE-INTPROMO-S2] Confirm `integer_promotion` fixture compile + run parity PASS in Go
3. [x] [ID: P0-RESOLVE-INTPROMO-S3] Confirm no impact on other fixtures (regenerate golden) — typing 23/23, stdlib 16/16, sample 18/18 all PASS

### P2-COMMON-RENDERER-PARENS: Implement operator-precedence-based parenthesis control in CommonRenderer

Spec: [spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1.4

1. [x] [ID: P2-CR-PARENS-S1] Add a mechanism for CommonRenderer to receive an operator precedence table — each language's emitter passes its own precedence table. Implement Go's precedence table first as the prototype
2. [x] [ID: P2-CR-PARENS-S2] Implement logic for BinOp / UnaryOp / Compare output: "add parentheses if parent precedence >= child precedence" — do not output unnecessary parentheses
3. [x] [ID: P2-CR-PARENS-S3] Remove outermost redundant parentheses (the outer parentheses in `x = (expr);`)
4. [x] [ID: P2-CR-PARENS-S4] Confirm no impact on Go fixture + sample parity — typing 23/23, stdlib 16/16, sample 18/18 all PASS

### P3-GO-LINT-FIX: Fix hardcode violations in the Go emitter

Spec: [spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1, §7

Violations detected by `check_emitter_hardcode_lint.py`:
- module_name 6 cases: `ctx.imports_needed.add("math")` / `"os"` — hardcoded native imports
- runtime_symbol 2 cases: `dispatch == "py_print"` / `"py_len"` — re-matching by string values already looked up via mapping.json
- class_name 19 cases: `"Exception"` / `"Path"` / `"ArgumentParser"` etc. — some resolved by P0-GO-TYPE-MAPPING, remaining to be removed

1. [x] [ID: P3-GO-LINT-S1] Fix module_name violations — derive native imports from runtime manifest or mapping.json — added go_pkg_imports to mapping.json, changed to use ctx.go_pkg_math / ctx.go_pkg_os
2. [x] [ID: P3-GO-LINT-S2] Fix runtime_symbol violations — remove string matching for `py_print` / `py_len` — added go_builtin_dispatch to mapping.json, changed to use ctx.dispatch_print / ctx.dispatch_len
3. [x] [ID: P3-GO-LINT-S3] Fix class_name violations — resolve from `types` table or EAST3 type info — added go_class_names to mapping.json, moved `_BUILTIN_EXCEPTION_BOUNDS` to ctx.builtin_exc_bounds, moved ArgumentParser / Path to ctx fields
4. [x] [ID: P3-GO-LINT-S4] Confirm 0 Go violations in `check_emitter_hardcode_lint.py` — all 7 categories 🟩 PASS

### P6-GO-SELFHOST: Convert toolchain2 to Go via the Go emitter and pass go build

Context: [docs/ja/plans/p6-go-selfhost.md](../plans/p6-go-selfhost.md)

1. [x] [ID: P6-GO-SELFHOST-S0] Add return type annotations to functions in the selfhost target code (`src/toolchain2/` all .py) that are missing them — get resolve to a state with no `inference_failure` — all functions annotated with return types, inference_failure count is zero in east3-opt
2. [x] [ID: P6-GO-SELFHOST-S1] Emit all toolchain2 .py files to Go and confirm go build passes
3. [x] [ID: P6-GO-SELFHOST-S2] Resolve go build failures by fixing the emitter/runtime (no EAST workarounds)
4. [x] [ID: P6-GO-SELFHOST-S3] Place Go selfhost golden files and maintain them as regression tests — test_selfhost_golden.py -k go: 5 passed, 2 skipped

### P7-GO-SELFHOST-RUNTIME: Run the Go selfhost binary and achieve parity PASS

Context: [docs/ja/plans/p7-go-selfhost-runtime.md](../plans/p7-go-selfhost-runtime.md)

go build passed in P6, but there are still gaps before the selfhost binary can actually convert fixture/sample/stdlib and achieve parity PASS.

1. [x] [ID: P7-GO-SELFHOST-RT-S1] Fix linker type_id assignment to resolve hierarchy for external base classes (CommonRenderer(ABC) etc.) — fall back to object
2. [x] [ID: P7-GO-SELFHOST-RT-S2] Include the Go translation of the Go emitter itself in the selfhost golden — revisit circular dependency exclusions to enable `emit/go/` in golden
3. [x] [ID: P7-GO-SELFHOST-RT-S3] Add a CLI wrapper (`main.go`) — minimal entry point that reads EAST3 JSON and emits Go code
4. [x] [ID: P7-GO-SELFHOST-RT-S4] Run `python3 tools/run/run_selfhost_parity.py --selfhost-lang go` and confirm fixture parity PASS
   - Completed 2026-05-03 in the Docker-isolated `pytra-devcontainer-check` environment. The rebuilt Go selfhost emitter passed fixture 161/161.
5. [ ] [ID: P7-GO-SELFHOST-RT-S5] Bring Go selfhost sample artifact parity to 18/18
   - Progress 2026-05-03: sample compile/run blockers were reduced, but strict artifact-size parity is still 2/18 PASS. Remaining work is PNG/GIF byte-size parity against the Python reference outputs.
