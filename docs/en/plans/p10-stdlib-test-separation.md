<a href="../../en/plans/p10-stdlib-test-separation.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P10-STDLIB-TEST-SEPARATION: Separate stdlib tests from fixture and generate a per-module matrix

Last updated: 2026-03-30
Status: Not started

## Background

Currently, stdlib tests live as fixtures under `test/fixture/source/py/stdlib/`. Fixtures are intended for unit-testing individual language features; they are different in nature from comprehensive API coverage tests for stdlib modules.

Additionally, a per-module matrix is needed so that users can determine at a glance whether a given module is available for a given target language.

## Design

### Directory structure

```
test/stdlib/source/py/
  math/
    test_sqrt.py
    test_trig.py
    test_constants.py
  json/
    test_loads.py
    test_dumps.py
    test_unicode.py
  pathlib/
    test_read_write.py
    test_joinpath.py
  re/
    test_match.py
    test_search.py
    test_sub.py
  argparse/
    test_basic.py
  sys/
    test_argv.py
  os/
    test_makedirs.py
    test_glob.py
  sqlite3/
    test_connect.py
    test_query.py
```

Test files are placed in a per-module folder.

### parity check support

- Add `--case-root stdlib`
- Accumulate results in `.parity-results/<lang>_stdlib.json`
- Module name is taken automatically from the folder name

### Per-module matrix

`gen_backend_progress.py` reads the stdlib results and generates a module × language matrix.

```
| Module  | C++ | Go | Rust | TS | JS | ... |
|---|---|---|---|---|---|---|
| math    | 🟩 | 🟩 | 🟩  | 🟩 | 🟩 | |
| json    | 🟩 | 🟩 | 🟥  | 🟩 | 🟩 | |
| pathlib | 🟩 | 🟩 | 🟥  | 🟥 | 🟥 | |
| re      | 🟩 | 🟥 | 🟥  | 🟥 | 🟥 | |
| sqlite3 | ⬜ | ⬜ | ⬜  | ⬜ | ⬜ | |
```

PASS condition: all tests in a module folder pass parity. If even one FAIL, the entire module is FAIL.

Output path: `docs/ja/progress/backend-progress-stdlib.md` (generated in Japanese and English simultaneously)

Add a link in progress/index.md.

### Migration from fixture

- Move existing tests from `test/fixture/source/py/stdlib/` to `test/stdlib/source/py/<module>/`
- They disappear from the fixture matrix and appear in the stdlib matrix
- Migration is done incrementally — first build the mechanism for one module (math), then migrate the rest

### User value

Users can tell at a glance whether "json works in Go" or "pathlib works in Rust". Integrate with spec-pylib-modules.md so module documentation links to the matrix.

## Prerequisites

None. This should be done before backends start selfhost testing; otherwise tests would have to be redone after migration.

## Decision Log

- 2026-03-30: Decided to separate stdlib tests from fixture and generate a per-module matrix. The first migration will happen when a heavy stdlib is added.
