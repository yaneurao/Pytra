<a href="../../../ja/plans/archive/20260307-p0-cpp-list-ref-first-completion.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Complete Ref-First List Semantics in the C++ Backend

Last updated: 2026-03-07

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-CPP-LIST-REFFIRST-01`

Summary:
- Finish the move to ref-first list semantics for typed mutable lists in the C++ backend.
- Keep `rc<list<T>>` as the canonical mutable representation across runtime and emitter boundaries.

Why this was needed:
- The old lowering still mixed value-first and ref-first behavior depending on local context.
- Typed list locals, fields, call-returned lists, and ABI adapter boundaries were not yet aligned.

Target contract:
- internal mutable typed lists are `rc<list<T>>`
- runtime helpers and emitters use ref-first semantics consistently
- value conversion happens only at explicit boundaries where needed

Main work covered by the plan:
- inventory value-first leftovers
- normalize runtime helper paths for `rc<list<T>>`
- trim obsolete mutable overloads for plain value lists
- switch typed signatures and locals to ref-first
- fix iter/subscript/method dispatch on call-returned lists
- align class fields and ABI adapters
- close remaining nested/container adapter gaps

Acceptance:
- representative codegen and runtime tests use ref-first behavior consistently
- plain `list<T>` mutable overloads no longer leak back in accidentally
- fixture/sample parity remains green

Decision log:
- 2026-03-07: `rc<list<T>>` is the canonical mutable typed-list lane; value lists are only transitional/read-only/boundary forms.
