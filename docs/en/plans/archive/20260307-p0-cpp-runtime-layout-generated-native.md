<a href="../../../ja/plans/archive/20260307-p0-cpp-runtime-layout-generated-native.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Realign the C++ Runtime Layout Around `generated/` and `native/`

Last updated: 2026-03-07

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-CPP-RUNTIME-LAYOUT-REALIGN-01`

Summary:
- Reorganize `src/runtime/cpp/` so ownership is visible from directories instead of filename suffixes.
- Keep `pytra/` as the generated public shim layer.
- Move module runtime artifacts to:
  - `generated/` for SoT-generated runtime code
  - `native/` for C++-specific handwritten companions

Target layout:

```text
src/runtime/cpp/
  core/
  generated/
    built_in/
    std/
    utils/
  native/
    built_in/
    std/
    utils/
  pytra/
    built_in/
    std/
    utils/
```

Why this was needed:
- The old `.gen.*` / `.ext.*` naming mixed ownership into filenames.
- The old `src/runtime/cpp/pytra/...` public include layer was correct in role but awkward in placement.
- Making directory ownership explicit simplifies guards, symbol-index generation, and future cleanup.

Rules fixed by this plan:
- `pytra/` remains the stable public include surface and is generated.
- `generated/` contains SoT-derived module runtime files.
- `native/` contains C++-specific runtime companions that cannot be generated from pure Python.
- `core/` remains separate from module runtime ownership.

Phases:
- inventory current layout
- switch runtime emission to `generated/...`
- update symbol index / build graph / layout guards
- move `utils` and `built_in` generated runtime into `generated/...`
- remove legacy fallback and close the old ownership model

Acceptance:
- `emit-runtime-cpp` writes module runtime to `generated/...`
- symbol index and build graph resolve `pytra/` public headers and `generated/native` implementation files
- legacy module directories no longer own runtime artifacts
- layout guard enforces the new structure

Decision log:
- 2026-03-07: the right abstraction is “public/internal ownership cleanup,” not merely renaming `.gen` / `.ext`.
- 2026-03-07: `pytra/` stays as a public shim layer, while `generated/` and `native/` become the canonical implementation ownership roots.
