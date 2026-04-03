<a href="../../ja/plans/p0-callable-type-tracking.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P0: Callable type tracking

Last updated: 2026-03-22

Related TODO:
- `ID: P0-CALLABLE-TYPE-TRACKING` in `docs/ja/todo/index.md`

## Background

When a function argument has a `Callable` type, the `resolved_type` in EAST3 becomes `unknown`, and the emitter cannot distinguish between a function reference and a regular variable. In PowerShell such arguments must be passed as scriptblocks, and other languages also differ in how they handle function pointers / lambdas.

If the EAST1 parser recognizes `Callable` type annotations and sets `resolved_type` to `callable[..., RetType]`, emitters can generate the appropriate code.

## Subtasks

- [ ] [ID: P0-CALLABLE-TYPE-TRACKING-01] Reflect `Callable` type annotations in `resolved_type` in the EAST1 parser
- [ ] [ID: P0-CALLABLE-TYPE-TRACKING-02] Add unit tests

## Decision Log

- 2026-03-22: The PS team reported insufficient type tracking for Callable arguments. Filed as a cross-backend improvement.
- 2026-04-02: Because the remaining item in C++ `P0-CPP-VARIANT-S7` was reduced to only bare `Callable` in `type_ignore_from_import`, this plan is referenced as a blocker for the variant/object migration.
- 2026-04-02: The resolver's call-site refine was fixed to account for the `main -> __pytra_main` rename and treat the zero-arg `callable[[],None]` signature as a concrete type. This causes `Callable` in `type_ignore_from_import` to lower to `::std::function<void()>` in C++, unblocking `P0-CPP-VARIANT-S7`.
