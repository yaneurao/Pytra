<a href="../../../ja/plans/archive/20260312-p0-typed-varargs-signature-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: support typed `*args` signatures on the representative C++ lane

Last updated: 2026-03-11

Related TODO:
- `ID: P0-TYPED-VARARGS-SIGNATURE-01` in `docs/en/todo/index.md`

Background:
- The current self-hosted parser explicitly rejects `*args` / `**kwargs` in function signatures.
- A representative blocker from Pytra-NES is `def merge_controller_states(target: ControllerState, *states: ControllerState) -> None:`, which currently fails with `Use explicit parameters instead of *args.`
- The current EAST `FunctionDef` carrier only keeps `arg_types` / `arg_order` / `arg_defaults`, so it has no place to retain variadic positional parameter metadata.
- Parser-only acceptance would still be broken without call-site packing for extra positional arguments.

Goal:
- As representative v1, support typed user-defined `*args` signatures from the self-hosted parser through the C++ target.
- Accept `def f(x: T, *rest: U) -> R` and pack extra positional arguments into a trailing collection parameter at known user-function call sites.
- Keep non-C++ backends fail-closed for v1 instead of pretending to support the lane.

In scope:
- typed `*args: T` support in the self-hosted signature parser
- `vararg_name` / `vararg_type` / `vararg_type_expr` on the `FunctionDef` / signature carrier
- parser / builder / frontend mirror updates for the new signature fields
- representative user-defined function call packing
- C++ function definition / call emission
- representative regression fixtures and source contracts
- ja/en TODO / plan / docs sync

Out of scope:
- untyped `*args`
- `**kwargs`
- positional-only `/`
- keyword-only `*` marker extensions
- starred actual arguments such as `f(*xs)`
- full implementations for Rust / C# / other backends

Acceptance criteria:
- The self-hosted parser accepts `def f(x: T, *rest: U) -> R:` and preserves variadic positional metadata on `FunctionDef`.
- On the representative fixture, extra positional argument calls are packed into the trailing collection parameter, and C++ transpile plus runtime regression pass.
- Non-C++ backends remain fail-closed on the representative `*args` lane instead of silently emitting the wrong thing.
- Unsupported lanes (untyped `*args`, `**kwargs`) still fail explicitly.

Checks:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/common -p 'test_self_hosted_signature.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east1_build.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k varargs`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_east3_cpp_bridge.py' -k varargs`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/check_transpiler_version_gate.py`
- `python3 tools/run/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Decision log:
- 2026-03-11: v1 is limited to typed `*args: T` on user-defined functions, with call-site packing implemented only on the representative C++ lane.
- 2026-03-11: The IR carrier gets dedicated `vararg_*` fields; the variadic parameter will not be smuggled into `arg_order`.
- 2026-03-11: Non-C++ backends stay fail-closed instead of advertising support they do not have.

## Breakdown

- [x] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S1-01] Fix the current reject contract and representative fixture in docs/tests and lock the typed `*args` v1 scope.
- [x] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S2-01] Add `vararg_*` fields to the self-hosted signature parser / AST builder / stmt/module parser and carry them onto `FunctionDef`.
- [x] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S2-02] Propagate the new `vararg_*` fields through the frontend mirror / auxiliary schema and lock selfhost regression.
- [x] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S3-01] Add variadic positional packing to the C++ emitter function definition / known call lane and pass the representative fixture.
- [x] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S3-02] Update non-C++ backend contract guards and docs to close v1.

- 2026-03-11: Added the representative blocker fixture `ng_typed_varargs_representative.py` and locked the current typed `*args` rejection in unit tests.
- 2026-03-11: Store typed `*args: T` on `FunctionDef.vararg_name/vararg_type/vararg_type_expr`, while exposing the local binding inside the body as `list[T]`.
- 2026-03-11: Flipped the representative fixture to `ok_typed_varargs_representative.py` and moved the reject contract back to untyped `ng_varargs.py`.
- 2026-03-11: Keep `vararg_*` as dedicated fields in the frontend mirror and host signature extractor as well, instead of mixing the variadic parameter into `arg_order` or `arg_types`.
- 2026-03-11: On the C++ v1 lane, `*rest: T` is emitted as a trailing `list[T]` parameter, and extra positional arguments at known user-function calls are packed through a synthetic `List` node so the normal call-arg bridge can still coerce to `rc_list_from_value(...)` when needed.
- 2026-03-11: The representative lane also prescans mutable parameter positions for top-level known functions so caller-side mutability, such as `ControllerState&`, is propagated interprocedurally.
- 2026-03-11: Non-C++ backends now share `reject_backend_typed_vararg_signatures()` at transpile entrypoints so typed `*args` fail closed as `unsupported_syntax` instead of silently emitting broken code.
