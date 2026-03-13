# P0: align `py2x` entrypoint imports to the `toolchain.frontends` facade

Last updated: 2026-03-13

Related TODO:
- `ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01` in `docs/en/todo/index.md`

Background:
- The canonical Python frontend implementation has already moved under `toolchain.frontends`, but [`src/py2x.py`](/workspace/Pytra/src/py2x.py) and [`src/py2x-selfhost.py`](/workspace/Pytra/src/py2x-selfhost.py) still import directly from `toolchain.compiler.transpile_cli`.
- [`src/toolchain/compiler/transpile_cli.py`](/workspace/Pytra/src/toolchain/compiler/transpile_cli.py) is a compatibility shim, so leaving external entrypoints attached to it keeps the canonical import surface ambiguous.
- [`src/toolchain/frontends/__init__.py`](/workspace/Pytra/src/toolchain/frontends/__init__.py) already exports `add_common_transpile_args` and `load_east3_document_typed`, but the `build_module_east_map` helper used by `py2x.py` is not exposed on the facade yet.

Goal:
- Add `build_module_east_map` to the `toolchain.frontends` facade and align the frontend imports in `py2x.py` / `py2x-selfhost.py` onto that facade.
- Add a source contract so those entrypoints do not regress back to direct `toolchain.compiler.transpile_cli` imports.

In scope:
- `src/toolchain/frontends/python_frontend.py`
- `src/toolchain/frontends/__init__.py`
- `src/py2x.py`
- `src/py2x-selfhost.py`
- `test/unit/common/test_py2x_entrypoints_contract.py`
- `test/unit/tooling/test_py2x_cli.py` if needed

Out of scope:
- Changing behavior inside `toolchain.frontends.transpile_cli`
- Deleting `toolchain.compiler.transpile_cli`
- Cleaning unrelated compiler/backend-registry imports

Acceptance criteria:
- The `toolchain.frontends` facade exports `build_module_east_map`.
- `py2x.py` / `py2x-selfhost.py` import their frontend helpers from the `toolchain.frontends` facade.
- A source contract detects any regression back to direct `toolchain.compiler.transpile_cli` imports, and the focused tests are green.

Verification commands:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 /workspace/Pytra/test/unit/common/test_py2x_entrypoints_contract.py -k dynamic_carrier`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 /workspace/Pytra/test/unit/tooling/test_py2x_cli.py`
- `python3 /workspace/Pytra/tools/check_todo_priority.py`
- `git -C /workspace/Pytra diff --check`

Breakdown:
- [ ] [ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01] Move the frontend imports in `py2x.py` / `py2x-selfhost.py` from `toolchain.compiler.transpile_cli` over to the `toolchain.frontends` facade so entrypoint consumers stop reaching through the compat shim.
- [ ] [ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01-S1-01] Lock the stale import surface and close condition in the plan / TODO.
- [ ] [ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01-S2-01] Update the `toolchain.frontends` facade exports plus the entrypoint imports and bring the source contract / focused tests back to green.
- [ ] [ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01-S3-01] Sync TODO / plan / archive and lock the close condition.

Decision log:
- 2026-03-13: Filed this as the next follow-up P0 after TODO became empty. Scope stays limited to the external entrypoint consumers, and does not attempt to delete the `toolchain.compiler.transpile_cli` compat shim yet.
