<a href="../../../ja/plans/archive/20260308-p2-linked-runtime-helper-template-v1.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2: `@template` v1 for Linked Runtime Helpers

Last updated: 2026-03-08

Related TODO:
- Completed. See `ID: P2-LINKED-RUNTIME-TEMPLATE-01` in `docs/en/todo/archive/20260308.md`.

Related:
- [p2-runtime-sot-linked-program-integration.md](../p2-runtime-sot-linked-program-integration.md)
- [p2-runtime-helper-generics-under-linked-program.md](../p2-runtime-helper-generics-under-linked-program.md)
- [spec-template.md](../../spec/spec-template.md)

Background:
- The long-term generic/runtime-helper direction already existed, but syntax had not been fixed between `TypeVar`-style notation and `@template("T")`.
- For the first limited rollout, a dedicated Pytra surface is clearer than trying to reuse Python’s generic surface awkwardly.
- The first scope must remain narrow: linked runtime helpers only, top-level functions only, and no explicit instantiation yet.

Objective:
- Fix `@template("T", ...)` as the canonical v1 generic surface.
- Limit the scope to linked-program runtime helpers.
- Delay explicit instantiation and treat specialization/monomorphization as a later linked-program concern.
- Fix syntax, metadata, validation, and extension direction before implementing the feature itself.

Acceptance criteria:
- `@template("T")` is documented as the canonical v1 syntax
- scope is fixed to runtime-helper top-level functions only
- canonical metadata is fixed around `meta.template_v1`
- `@instantiate(...)` is reserved as a future extension rather than part of v1
- `TypeVar` remains annotation-only and is not used for the v1 surface

## Task Breakdown

- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S1-01] Close the `TypeVar` vs `@template` comparison and choose `@template("T")`.
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S1-02] Fix the v1 scope to runtime helpers, top-level functions, and no explicit instantiation.
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S2-01] Design the canonical parser / EAST / linked metadata shape such as `meta.template_v1`.
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S2-02] Design validation rules for position, names, duplicates, and runtime-helper-only enforcement.
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S3-01] Record an extension path compatible with future `@instantiate(...)`.
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S3-02] Clarify the connection to later specialization collector / monomorphization work.
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S4-01] Sync docs / TODO / related plans.
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S4-02] Prepare the plan for archival closure.

## Decision Log

- 2026-03-08: `@template("T")` was chosen because it makes the function-scoped type-parameter declaration explicit, while `TypeVar` leaves the declaration site ambiguous for the intended helper-only rollout.
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S1-02]: v1 was explicitly limited to linked runtime helpers, top-level functions, and no explicit instantiation.
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S2-01]: canonical metadata was fixed as `FunctionDef.meta.template_v1` with `schema_version`, `params`, `scope="runtime_helper"`, and `instantiation_mode="linked_implicit"`.
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S2-02]: validation was split between parser/EAST build for syntax and a linked-program validator for runtime-helper provenance.
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S3-01]: future explicit instantiation will extend the same decorator family through `@instantiate("name", type_args...)` rather than splitting into a different syntax family.
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S3-02]: specialization collectors will use `meta.template_v1` rather than raw decorators, and `instantiation_mode="linked_implicit"` means concrete type tuples are collected deterministically from linked-program call sites.
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S4-02]: The plan was judged complete as a docs-fixation step; implementation follow-up belongs to the later linked-runtime and helper-generics plans.
