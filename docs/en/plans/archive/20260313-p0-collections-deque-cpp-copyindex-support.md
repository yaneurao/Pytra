<a href="../../../ja/plans/archive/20260313-p0-collections-deque-cpp-copyindex-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: representative C++ support for `collections.deque.copy()` / `index()`

Last updated: 2026-03-13

Related TODO:
- `ID: P0-COLLECTIONS-DEQUE-CPP-COPYINDEX-01` in `docs/ja/todo/index.md`

Background:
- The representative C++ lane for `collections.deque` now covers the constructor, `append` / `appendleft`, `popleft` / `pop`, `extendleft(iterable)`, `reverse()`, `rotate()`, `count()`, `remove()`, and `len` / truthiness on the `::std::deque<T>` surface.
- However, `copy()` and `index(value)` still leak directly as `q.copy()` / `q.index(...)`, which are not valid C++ for `std::deque`.
- `clear()`, `extend()`, `reverse()`, `rotate()`, `count()`, and `remove()` already lower to valid C++ surfaces, so this task is intentionally limited to the remaining `copy` / `index` expression-lookup subset.

Goal:
- Align `collections.deque.copy()` / `index()` to valid C++ surfaces in the representative C++ lane.
- Lock the deque representative subset with focused regressions plus smoke.

In scope:
- `from collections import deque`
- representative method subset: `copy()`, `index(value)`
- syncing focused regressions, smoke, docs, and TODO

Out of scope:
- the full `deque` API (`maxlen`, arbitrary insert/remove, iterator invalidation semantics, etc.)
- the full `index()` overload family with slice/start/stop
- simultaneous rollout to all backends
- redesigning the entire `collections` module
- adding a new deque object hierarchy to the C++ runtime

Acceptance criteria:
- A focused regression locks the current invalid C++ surface (`q.copy()`, `q.index(...)`).
- In the representative C++ lane, `copy()` lowers to a valid deque copy-construction surface.
- In the representative C++ lane, `index(value)` lowers to a valid search / distance surface.
- Representative build/run smoke passes for `copy/index` fixtures.
- The ja/en docs and TODO mirrors reflect the support scope and exclusions.

Validation commands:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k deque_copyindex`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`
- `git diff --check`

Decision log:
- 2026-03-13: `clear()`, `extend()`, `reverse()`, `rotate()`, `count()`, and `remove()` already lower to valid C++, so the new task is limited to the `copy` / `index` subset only.

## Breakdown

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-COPYINDEX-01] Lock the representative C++ lane for `collections.deque.copy()` / `index()`.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-COPYINDEX-01-S1-01] Lock the current invalid C++ surface (`copy`, `index`) in focused regressions / TODO / plan.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-COPYINDEX-01-S2-01] Lower `copy()` to a valid deque copy-construction surface.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-COPYINDEX-01-S2-02] Lower `index(value)` to a valid search / distance surface.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-COPYINDEX-01-S3-01] Sync build/run smoke and support wording, then close the task.

- 2026-03-13: `copy()` now lowers to explicit `::std::deque<T>(src)` copy-construction inside a single-evaluation lambda, and `index(value)` now lowers to `std::find + iterator difference + ValueError("deque.index missing value")`.
- 2026-03-13: The representative build/run smoke is locked on the typed lane `r: deque[int] = q.copy()` with output `3 / 2 / 0`. Plain local inference (`r = q.copy()`) is split out into a follow-up task.
