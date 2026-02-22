<a href="../../docs-jp/plans/p2-microgpt-compatibility.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# TASK GROUP: TG-P2-MICROGPT-COMPAT

Last updated: 2026-02-22

Related TODO:
- `docs-jp/todo.md` `ID: P2-MGPT-01`
- `docs-jp/todo.md` `ID: P2-MGPT-02`
- `docs-jp/todo.md` `ID: P2-MGPT-03`
- `docs-jp/todo.md` `ID: P2-MGPT-04`

Background:
- Transpiling `work/tmp/microgpt-20260222-lite.py` via `python3 src/py2cpp.py ...` currently stops because the self_hosted parser rejects arguments without type annotations.
- With typed minimal probes for `random.choices` / `random.gauss` / `random.shuffle`, generated C++ emits `pytra::std::random::*` calls, but compilation fails because those APIs were missing in `src/runtime/cpp/pytra/std/random.h`.
- `os.path.exists` has already been confirmed to transpile and pass C++ syntax check under the same conditions.

Validation commands (already executed):
- `python3 src/py2cpp.py work/tmp/microgpt-20260222-lite.py -o work/out/microgpt-20260222.cpp`
- `python3 src/py2cpp.py /tmp/pytra_probe_random_choices.py -o work/out/pytra_probe_random_choices.cpp`
- `python3 src/py2cpp.py /tmp/pytra_probe_random_gauss.py -o work/out/pytra_probe_random_gauss.cpp`
- `python3 src/py2cpp.py /tmp/pytra_probe_random_shuffle.py -o work/out/pytra_probe_random_shuffle.cpp`
- `g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only work/out/pytra_probe_random_choices.cpp`
- `g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only work/out/pytra_probe_random_gauss.cpp`
- `g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only work/out/pytra_probe_random_shuffle.cpp`
- `g++ -std=c++20 -I src -I src/runtime/cpp -fsyntax-only work/out/pytra_probe_os_exists.cpp`

Objective:
- Incrementally improve `py2cpp` compatibility for microgpt-like input while explicitly handling gaps against the current specification (type annotations required).

In scope:
- Decision and implementation path for self_hosted parser type-annotation requirements (keep as spec or extend functionality)
- API expansion for `pytra.std.random` / C++ runtime random
- Building a regression path for transpile -> compile on microgpt-like input

Out of scope:
- Optimization of learning algorithms themselves
- Runtime implementation of network access (`urllib`)

Acceptance criteria:
- Operational policy for type-annotation requirements is documented in spec.
- Minimal C++ syntax checks pass for `random.choices` / `random.gauss` / `random.shuffle`.
- Causes of failures on microgpt-like cases can be traced reproducibly (fixture or explicit procedure).
- `work/tmp/microgpt-20260222-lite.py` transpiles with `py2cpp.py` and generated C++ compiles with `g++ -std=c++20 -I src -I src/runtime/cpp`.

Decision log:
- 2026-02-22: Initial draft. Added TODO entries for observed gaps in microgpt conversion tests (type annotations, random API).
- 2026-02-22: Implemented `P2-MGPT-02`. Added `choices/gauss/shuffle` to `src/pytra/std/random.py` and regenerated `src/runtime/cpp/pytra/std/random.*` via `--emit-runtime-cpp`. Added a 2-arg overload on C++ runtime for `choices(population, weights)` delegating to `choices(population, weights, 1)`, and aligned `shuffle` declaration with implementation signature (`list<int64>&`).
