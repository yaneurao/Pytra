<a href="../../../ja/plans/archive/20260308-p0-pytra-cli-cpp-maxopt-linked-build.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Use the Linked-Program Build Route for Max-Optimized C++ in `pytra-cli`

Last updated: 2026-03-08

Related TODO:
- Completed. See `ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01` in `docs/en/todo/archive/20260308.md`.

Background:
- The linked-program optimizer and ProgramWriter were already available, but `pytra-cli --target cpp --build` still followed the older route in which C++ often went through the legacy compat path.
- As a result, `--codegen-opt 3` did not automatically mean “run the maximum linked-program optimization path and then build an executable.”
- The desired user contract is simple: for C++, the max codegen setting should drive the full linked-program route, and sample parity must stay green.

Objective:
- Make `pytra-cli --target cpp --build --codegen-opt 3` use the linked-program optimizer route by default.
- Align transpile-only and build routes so both use the same max-optimization semantics.
- Hide `eastlink` / `ir2lang` plumbing from the user and keep the one-command C++ build flow intact.

In scope:
- `src/pytra-cli.py`
- `src/py2x.py`
- `src/ir2lang.py`
- C++ multi-file output path and manifest handoff
- representative CLI regressions and sample parity coverage

Out of scope:
- changing the default route for lower codegen levels
- redefining native compiler optimization flags such as `-O3`
- redesigning ProgramWriter itself

Acceptance criteria:
- `--target cpp --build --codegen-opt 3` uses the linked-program optimization route
- transpile-only `--codegen-opt 3` uses the same route rather than the legacy compat path
- manifest/build handoff is verified by representative CLI tests
- C++ sample parity stays green under the max route

Planned verification:
- `python3 -m unittest discover -s tools/unittest/tooling -p 'test_pytra_cli.py'`
- `python3 -m unittest discover -s tools/unittest/tooling -p 'test_runtime_parity_check_cli.py'`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root sample --all-samples --cpp-codegen-opt 3 --east3-opt-level 2`

## Phases

### Phase 1: Contract

- inventory the current relation between `--codegen-opt` and `py2x/eastlink/ir2lang/py2cpp`
- define the target semantics of `codegen-opt=3` for C++

### Phase 2: Route switching

- route `pytra-cli --build --target cpp --codegen-opt 3` through linked-program optimization
- align transpile-only max-opt to the same route

### Phase 3: Regression and parity

- add representative CLI regression coverage
- run C++ sample parity with the max route

### Phase 4: Documentation and closure

- document the max-opt C++ route
- archive the completed plan

## Task Breakdown

- [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S1-01] Inventory current optimization-level behavior and fix the intended semantics of `codegen-opt=3`.
- [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S1-02] Document the CLI contract and sample-parity gate for the max-opt C++ route.
- [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S2-01] Implement a linked-program optimizer route for `pytra-cli --target cpp --build --codegen-opt 3`.
- [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S2-02] Align transpile-only max-opt C++ with the same linked route.
- [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S3-01] Add representative regression coverage for route selection, manifest handling, build, and run.
- [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S3-02] Run sample parity and confirm the max route is still green.
- [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S4-01] Update docs and how-to-use.
- [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S4-02] Record the final result and archive the plan.

## Decision Log

- 2026-03-08: The canonical user-facing behavior was fixed as: `--codegen-opt 3` means “maximum frontend/backend optimization,” while native compiler flags such as `-O3` remain separate.
- 2026-03-08 [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S2-01]: `pytra-cli` was updated so the build route uses `py2x --link-only` followed by `py2x --from-link-output` for max-opt C++, storing the intermediate bundle under `output_dir/.pytra_linked/`.
- 2026-03-08 [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S2-02]: The transpile-only max-opt route was aligned with the same linked-program path and explicitly requires `--output-dir`, since the result is multi-file output.
- 2026-03-08 [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S3-02]: Sample parity was re-run with the max route and remained green at `cases=18 pass=18 fail=0`.
