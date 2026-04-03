<a href="../../ja/spec/spec-tools-update-rules.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# `tools/` — Update Rules

[Back to index](./spec-tools.md)

- When adding a new script to `tools/`, update `docs/ja/spec/spec-tools.md` (the index) at the same time.
- State the purpose of the script in a single line: "what it exists to automate."
- For breaking changes (argument spec changes, deprecations, merges), also sync the relevant command examples in `docs/ja/tutorial/how-to-use.md`.
- The internal version gate (`transpiler_versions.json`) is deprecated. External release versions are managed manually via `docs/VERSION`.
- Sample regeneration is verified by the results of a parity check.
