<a href="../../ja/tutorial/troubleshooting.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# How to Read Errors and Common Stumbling Points

This page collects a quick guide to reading Pytra transpilation errors and finding the usual trouble spots.  
For the source-of-truth language rules, see the [User Specification](../spec/spec-user.md) and the [Specification Index](../spec/index.md).

## Error Categories

Failure messages from `src/pytra-cli.py --target cpp` are shown in the following categories.

- `[user_syntax_error]`
  - A syntax error in user code
- `[not_implemented]`
  - Syntax that is not implemented yet
- `[unsupported_by_design]`
  - Syntax intentionally unsupported by the language design
- `[internal_error]`
  - An internal transpiler error

## Common Stumbling Points

- Importing Python standard-library modules directly
  - Prefer `pytra.std.*`.
  - See: [spec-pylib-modules.md](../spec/spec-pylib-modules.md)
- Missing type annotations, so types such as empty `list` / `dict` cannot be resolved
  - See: [spec-user.md](../spec/spec-user.md)
- Using syntax that is not supported
  - See: [spec-user.md](../spec/spec-user.md)
- Trying to use `getattr(...)` / `setattr(...)`
  - Dynamic attribute lookup/update by string name is intentionally unsupported.
  - Prefer concrete `x.field` access, `dict` / JSON objects, or dedicated `@extern` seams.
- Want to check detailed C++ support status
  - See: [py2cpp Support Matrix](../language/cpp/spec-support.md)
- Want to confirm import / runtime-module coverage
  - See: [spec-pylib-modules.md](../spec/spec-pylib-modules.md)
- Want to confirm what a CLI option means
  - See: [spec-options.md](../spec/spec-options.md)

## More Operational Checks

- Want to check parity, selfhost, or local CI
  - [Usage Guide](../how-to-use.md)
- Want to call `pytra-cli.py` / `east2x.py` directly
  - [Usage Guide](../how-to-use.md)
- Want to use `@extern` / `extern(...)`
  - [extern.md](./extern.md)
