<a href="../../../ja/plans/archive/20260307-p0-cpp-core-ext-suffix-retire.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Retire `.ext` Suffixes from the C++ `core` Surface

Last updated: 2026-03-07

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-CPP-CORE-EXT-SUFFIX-RETIRE-01`

Summary:
- Remove `.ext` from:
  - `src/runtime/cpp/core/*.ext.h` compatibility headers
  - `src/runtime/cpp/native/core/*.ext.h`
  - `src/runtime/cpp/native/core/*.ext.cpp`
- Keep ownership visible by directory instead of filename suffix.

Why this was needed:
- After the ownership split, `core/*.ext.h` was no longer the handwritten source of truth; it was just a forwarder layer.
- The `.ext` suffix on the public `core` surface had become misleading.

Target naming:

```text
src/runtime/cpp/core/py_runtime.h
src/runtime/cpp/native/core/py_runtime.h
src/runtime/cpp/native/core/gc.cpp
```

Rules fixed by this plan:
- `core/` is a stable include surface with plain names.
- `native/core/` also uses plain names; ownership is already clear from the directory.
- future `generated/core/` will also use plain names.

Phases:
- inventory current include/compile paths
- switch the `core/` surface to plain names
- update tooling to resolve plain names
- rename `native/core` files
- remove legacy `.ext` fallback and close the plan

Acceptance:
- backend and tooling resolve `runtime/cpp/core/*.h`
- `native/core` compile sources use plain `.h/.cpp`
- no core-lane `.ext` fallback remains in symbol-index or build-graph tooling

Decision log:
- 2026-03-07: ownership belongs in directories, not in `.ext` suffixes, once `core/` is only a compatibility/include surface.
