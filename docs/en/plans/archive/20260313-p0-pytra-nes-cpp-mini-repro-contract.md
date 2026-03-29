<a href="../../../ja/plans/archive/20260313-p0-pytra-nes-cpp-mini-repro-contract.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Pytra-NES representative C++ mini repro contract

Last updated: 2026-03-13

Related TODO:
- `ID: P0-PYTRA-NES-CPP-MINI-REPRO-01` in `docs/en/todo/index.md`

Background:
- The Pytra-NES team reported two early blockers: a parenthesized sibling relative import like `from .controller import (...)` and a class field declaration such as `timestamps: deque[float] = field(init=False, repr=False)`.
- Each surface already has its own representative C++ smoke / regression, but there is no single representative contract that fixes them together inside the same multi-file package.
- In practice, the real package touches relative-import resolution, dataclass field metadata, and `collections.deque` lowering at the same time, so separate regressions are not enough to prevent re-entry.

Goal:
- Define one representative minimal Pytra-NES-style package and lock it through transpile / build / run on the C++ multi-file lane.
- Use a sibling package layout such as `controller.py` / `pad_state.py` / `ppu.py`, and require parenthesized relative imports, `dataclass`, a `deque[float]` field, and `deque.append/popleft/len` to work together.
- Keep the smoke strong enough to prove that `field(...)` does not leak into generated C++ and `deque[float]` lowers to `::std::deque<float64>`.

In scope:
- `tools/unittest/emit/cpp/test_py2cpp_features.py`
- Representative C++ emitter / runtime drift guards when needed
- TODO / plan / support docs

Out of scope:
- Rolling the same repro out to non-C++ backends immediately
- Converting the full NES emulator into a checked-in fixture
- Full `dataclass` compatibility or full `deque` API coverage

Acceptance criteria:
- A 3-module package `controller.py` / `pad_state.py` / `ppu.py` passes transpile / build / run on the C++ multi-file lane.
- Generated `pad_state.h` contains `::std::deque<float64> timestamps;`.
- Generated `ppu.cpp` keeps the sibling include, `append -> push_back`, `popleft -> front()+pop_front()`, and `len(...) -> .size()` lowering guards.
- Generated output does not leak `field(`.
- Representative runtime output is fixed in regression form.

Verification commands:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/tools/unittest/backends python3 tools/unittest/emit/cpp/test_py2cpp_features.py -k pytra_nes`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`

Breakdown:
- [x] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01] Lock a representative Pytra-NES multi-file package (parenthesized sibling relative import + `dataclass` + `deque[float]` field + `deque` methods) through build/run on the representative C++ lane.
- [x] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01-S1-01] Added the representative package smoke and locked the C++ multi-file build/run baseline that combines `from .controller import (...)` with `timestamps: deque[float] = field(init=False, repr=False)`.
- [x] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01-S2-01] Turn the generated include / class layout / method-lowering surface exposed by the smoke into source guards so the representative Pytra-NES lane fails fast on drift.
- [x] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01-S3-01] Sync TODO / plan / support docs to the representative Pytra-NES mini repro contract and close it.

Decision log:
- 2026-03-13: Fixed the representative contract to a 3-module `controller.py` / `pad_state.py` / `ppu.py` package that mirrors the real Pytra-NES pattern. The task intentionally locks the combination of surfaces rather than treating them as unrelated single-feature regressions.
- 2026-03-13: `S2-01` folded generated-source guards into the compile/run smoke and locked `controller.h` / `pad_state.h` includes, the `::std::deque<float64>` field layout, `append -> push_back(float64(...))`, `popleft -> front()+pop_front()`, and `len(...) -> (deque).size()`. Old `py_list_append_mut(...)`, `obj_to_list_ref_or_raise(...)`, and raw `.popleft()` calls stay forbidden.
- 2026-03-13: `S3-01` synchronized the C++ support wording for `collections.deque[T]` with the Pytra-NES multi-file package smoke and then closed the task into the archive.
