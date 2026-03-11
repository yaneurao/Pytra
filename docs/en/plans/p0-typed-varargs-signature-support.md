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
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_self_hosted_signature.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east1_build.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k varargs`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py' -k varargs`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Decision log:
- 2026-03-11: v1 is limited to typed `*args: T` on user-defined functions, with call-site packing implemented only on the representative C++ lane.
- 2026-03-11: The IR carrier gets dedicated `vararg_*` fields; the variadic parameter will not be smuggled into `arg_order`.
- 2026-03-11: Non-C++ backends stay fail-closed instead of advertising support they do not have.

## Breakdown

- [ ] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S1-01] Fix the current reject contract and representative fixture in docs/tests and lock the typed `*args` v1 scope.
- [ ] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S2-01] Add `vararg_*` fields to the self-hosted signature parser / AST builder / EAST carrier.
- [ ] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S2-02] Propagate the new `vararg_*` fields through the stmt/module parser and frontend mirror, and pass selfhost regression.
- [ ] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S3-01] Add variadic positional packing to the C++ emitter function definition / known call lane and pass the representative fixture.
- [ ] [ID: P0-TYPED-VARARGS-SIGNATURE-01-S3-02] Update non-C++ backend contract guards and docs to close v1.
