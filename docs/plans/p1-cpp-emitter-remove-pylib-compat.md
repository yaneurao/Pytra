# P1: Remove `pylib` Compatibility Name Normalization from `CppEmitter`

Last updated: 2026-02-25

## Goal

Remove `_normalize_runtime_module_name` from `src/hooks/cpp/emitter/cpp_emitter.py`, drop forced conversion for `pylib.*` compatibility,
and complete `cpp_emitter.py` name resolution using only the `pytra.*` namespace family.

## Background

- Name normalization in `cpp_emitter.py` exists as a compatibility measure for mixed operation of legacy `pylib` and current `pytra` namespaces.
- Since we no longer intend to maintain legacy compatibility, leaving these duplicate branches increases maintenance and analysis complexity.
- `src/pytra/compiler/east_parts/code_emitter.py` has a similarly named logic area, so overall consistency must be cleaned up.

## Out of scope

- Adding new support for `pylib.*`
- Large-scale redesign of `py2cpp.py` itself (managed as a separate migration task)
- Python runtime API spec changes

## Acceptance criteria

- Remove dependencies on `_normalize_runtime_module_name` from both `src/hooks/cpp/emitter/cpp_emitter.py` and `src/hooks/cpp/emitter/call.py`.
- Remove conversion routes that assume `pylib.*` input (and clearly document that compatibility is no longer provided).
- Confirm via tests (at least `tools/check_py2cpp_transpile.py` or `test/unit/test_py2cpp_*.py`) that no new `pylib`-assumption cases are required.

## Execution order (recommended)

### `P1-CPP-EMIT-NORM-01-S1`
- Inventory all `_normalize_runtime_module_name` call sites in `src/hooks/cpp/emitter/cpp_emitter.py` and lock impact scope for direct removal.
- Decide replacement strategy (`module_namespace_map` / `dict_any_get_str` / `module_name` references).

### `P1-CPP-EMIT-NORM-01-S2`
- Update `src/hooks/cpp/emitter/cpp_emitter.py` and `src/hooks/cpp/emitter/call.py` without `pylib` normalization.
- Delete unnecessary helper implementation or align migration feasibility on `src/pytra/compiler/east_parts/code_emitter.py`.

### `P1-CPP-EMIT-NORM-01-S3`
- Update tests and verification.
- If legacy-compat fixtures remain, mark them out of scope and replace with alternative regression checks.

## Acceptance log

- [x] 2026-02-25: `P1-CPP-EMIT-NORM-01-S1` completed. Removed all `_normalize_runtime_module_name` call sites in `cpp_emitter.py` and `call.py`, excluding `pylib.*` compatibility normalization from paths.
- [x] 2026-02-25: `P1-CPP-EMIT-NORM-01-S2` completed. Default `_normalize_runtime_module_name` in `src/pytra/compiler/east_parts/code_emitter.py` is identity behavior, and no `pylib.*`-dependent conversion branch exists, so no further change required.
- [x] 2026-02-25: `P1-CPP-EMIT-NORM-01-S3` completed. Removed C++ tests that were validating `pylib` compatibility and deleted legacy compatibility test `test_import_pylib_png_runtime` from `test/unit/test_py2cpp_features.py` and fixture `test/fixtures/imports/import_pylib_png.py`. Continued using existing statement in `docs-ja/spec/spec-dev.md` (`pylib.runtime` removal) as explicit requirement.

- [ ] In progress: audit follow-up task for `pylib.*` compatibility normalization removal
