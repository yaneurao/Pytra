<a href="../../../ja/plans/archive/20260307-p0-cpp-core-ownership-split.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Split C++ `core` Ownership

Last updated: 2026-03-07

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-CPP-CORE-OWNERSHIP-SPLIT-01`

Summary:
- Prepare for future generated low-level runtime by separating `core` ownership into:
  - `generated/core`
  - `native/core`
  - `core/` as a stable include surface / compatibility layer

Why this was needed:
- `core/` had historically meant “handwritten low-level runtime,” but future plans include generated core helpers.
- Mixing generated and handwritten files directly in `core/` would make ownership unclear again.

Contract fixed by this plan:
- `core/` is not an implementation ownership bucket; it is the stable include surface.
- `generated/core` is reserved for generated core artifacts and must carry generator markers.
- `native/core` contains handwritten low-level implementation sources.
- `pytra/core` is not introduced; module-facing public shims stay under `pytra/`, while low-level runtime keeps `core/`.

Phases:
- inventory current `core/`
- fix the spec and README contract
- extend symbol-index and build-graph path resolution
- harden layout / marker guards
- move compile sources into `native/core`
- close the old ownership model and archive the plan

Acceptance:
- compile sources such as `gc` and `io` live under `native/core`
- `core/` becomes header-only stable surface
- guards prevent random `.cpp` files from re-entering `core/`
- future `generated/core` is explicitly reserved and documented

Decision log:
- 2026-03-07: if generated core becomes necessary, it must be introduced as `generated/core + native/core`, not by mixing generated files into `core/`.
- 2026-03-07: `core/` stays as the stable include surface; it is not moved under `pytra/`.
