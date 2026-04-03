<a href="../../ja/plans/p4-cpp-selfhost.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P4-CPP-SELFHOST: Convert toolchain2 to C++ via the C++ emitter and pass g++ build

Last updated: 2026-03-31
Status: In progress (S0–S4 complete, S5–S7 incomplete)

## Background

Convert Pytra's own transpiler (toolchain2) to C++ and verify that the resulting C++ compiler operates correctly. This:

- Validates C++ emitter quality at the scale of toolchain2's codebase
- Fills in the C++ row of the selfhost matrix
- Enables fast compilation via a C++ binary in the future

## Flow

1. Convert all toolchain2 `.py` files to C++ with `pytra-cli2 -build --target cpp`
2. Compile with `g++` to generate a binary
3. Use the binary to convert fixture/sample, and verify that it produces the same output as Python (P3-SELFHOST-PARITY)

## Subtasks

1. [S0] Complete type annotation coverage for selfhost target code (shared with P6-GO-SELFHOST-S0)
2. [S1] toolchain2 → C++ emit + pass g++ build ✅
3. [S2] Fix emitter/runtime for build failures ✅
4. [S3] Place selfhost C++ goldens + regression tests ✅
5. [S4] C++ emit succeeds for all toolchain2 modules including the previously skipped 5 modules ✅
6. [S5] g++ build / link for selfhost C++ binary
7. [S6] selfhost parity fixture
8. [S7] selfhost parity sample

## Design decisions

- No EAST workarounds. Build failures are resolved by fixing the emitter/runtime.
- Type annotation completion (S0) is shared with Go selfhost. Whichever finishes first provides the results.
- Goldens are placed in `test/selfhost/cpp/` and maintained as regression tests.

## Decision Log

- 2026-03-29: Filed P4-CPP-SELFHOST. Start after P3-COMMON-RENDERER-CPP is complete.
- 2026-03-30: S1 (emit + build pass) and S2 (build failure fixes) complete. Extended tuple subscript detection, added `py_dict_set_mut`, forced object→str/container type coercions, two-phase forward declaration output, etc.
- 2026-03-31: S0 completed via audit. Scanned all `.py` files under `src/toolchain2/` with `ast`; confirmed zero missing return annotations. Added `tools/unittest/selfhost/test_selfhost_return_annotations.py` as a regression guard.
- 2026-03-31: S3 complete. Updated `test/selfhost/cpp/` with `tools/gen/regenerate_selfhost_golden.py --target cpp --timeout 60`, finalizing C++ goldens for the 42 modules that emit successfully. The 5 modules that fail to emit are fixed as known skips, and `tools/unittest/selfhost/test_selfhost_cpp_golden.py` verifies golden coverage / re-emit consistency as a `unittest` regression test.
- 2026-03-31: S4 complete. `collect_east3_opt_entries()` now returns 47 modules, and C++ emit succeeds for all of them, including the previously skipped `toolchain2.compile.passes`, `toolchain2.resolve.py.resolver`, and `toolchain2.optimize.passes.{tuple_target_direct_expansion,typed_enumerate_normalization,typed_repeat_materialization}`. The current selfhost golden diff is a golden mismatch, not an emit failure.
