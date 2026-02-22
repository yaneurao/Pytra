<a href="../../docs-jp/plans/p3-spec-drafts.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# TASK GROUP: TG-P3-SPEC-DRAFTS

Last updated: 2026-02-22

Related TODO:
- `docs-jp/todo.md` `ID: P3-SD-01`
- `docs-jp/todo.md` `ID: P3-SD-02`

Background:
- `spec-make.md` and `spec-template.md` were temporarily placed at repository root, but should be managed under `docs-jp/spec/` for consistency with the specification set.
- At present, both documents contain draft content that has not yet been fully reconciled with implementation status or adoption decisions.

Objective:
- Manage `docs-jp/spec/spec-make.md` and `docs-jp/spec/spec-template.md` as low-priority backlog items and migrate adopted content into canonical specs in stages.

In scope:
- Compare each draft against current implementation and classify sections as adopt/hold/drop candidates.
- Move adopted parts into canonical specs (`spec-runtime`, `spec-user`, `spec-east`, `spec-tools`, `how-to-use`, etc.).
- Determine whether `docs/` mirror synchronization is needed and split follow-up TODOs if needed.

Out of scope:
- Starting implementation of template features or a new CLI.
- Large-scale one-shot rewrites of existing specs.

Acceptance criteria:
- For each draft, the integration target of each section is explicitly defined.
- No implementation-inconsistent text is left untriaged.
- Tasks are split into maintainable low-priority units (ID-level tracking).

Decision log:
- 2026-02-22: Confirmed policy to move `spec-make.md` / `spec-template.md` to `docs-jp/spec/` and add low-priority TODOs (`P3-SD-01`, `P3-SD-02`).
