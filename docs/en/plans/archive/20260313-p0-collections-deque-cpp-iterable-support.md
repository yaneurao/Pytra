<a href="../../../ja/plans/archive/20260313-p0-collections-deque-cpp-iterable-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: representative C++ support for `collections.deque` iterable construction / extendleft

Last updated: 2026-03-13

Related TODO:
- `ID: P0-COLLECTIONS-DEQUE-CPP-ITERABLE-01` in `docs/ja/todo/index.md`

Background:
- The representative C++ lane for `collections.deque` now covers the zero-arg constructor, `append` / `appendleft`, `popleft` / `pop`, and `len` / truthiness.
- The iterable-based surface is now aligned: `deque([1, 2])` lowers to a range constructor and `extendleft([3, 4])` lowers to a `push_front` loop bundle, so only the representative smoke and closeout remain.
- `extend([...])` already lowers to `insert(end, begin, end)`, so this task is intentionally limited to the remaining invalid constructor / left-extend bundle.

Goal:
- Align the iterable-based `collections.deque` surface with `::std::deque<T>` in the representative C++ lane.
- Lock the remaining practical `deque` subset with focused regressions plus smoke.

In scope:
- single-arg `deque(iterable)` construction
- representative lowering for `extendleft(iterable)`
- syncing focused regressions, smoke, docs, and TODO

Out of scope:
- the full `deque` API (`rotate`, `maxlen`, arbitrary insert/remove, iterator invalidation semantics, etc.)
- simultaneous rollout to all backends
- redesigning the entire `collections` module
- adding a new deque object hierarchy to the C++ runtime

Acceptance criteria:
- A focused regression locks the iterable-based `deque` surface after it is aligned to `::std::deque<T>` plus a `push_front` loop bundle.
- In the representative C++ lane, `deque(iterable)` lowers to a valid `::std::deque<T>` constructor surface.
- In the representative C++ lane, `extendleft(iterable)` lowers to a valid C++ loop / `push_front` bundle.
- Build/run smoke passes for a representative fixture.
- The ja/en docs and TODO mirrors reflect the support scope and exclusions.

Validation commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k deque_iterable`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `git diff --check`

Decision log:
- 2026-03-13: among iterable-based `deque` surfaces, `extend` already lowers to valid C++, so this task is limited to `deque(iterable)` and `extendleft(iterable)`.
- 2026-03-13: as `S1-01`, a focused regression now locks the current invalid `q = deque(list<int64>{...});` and `q.extendleft(...)` surface.
- 2026-03-13: as `S2-01`, `deque(iterable)` now lowers to a typed `::std::deque<T>(begin, end)` range constructor. The focused regression is narrowed to the remaining `extendleft` leak.
- 2026-03-13: as `S2-02`, `extendleft(iterable)` now lowers to a snapshot + `push_front` loop bundle. The iterable surface on typed `deque` owners is now aligned to `std::deque` in the representative C++ lane.
- 2026-03-13: as `S3-01`, a representative build/run smoke now locks the `deque([1, 2]) + extendleft([3, 4])` output `4 / 3 / 1 / 2`. The task now satisfies every acceptance criterion.

## Breakdown

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ITERABLE-01] Lock the representative C++ lane for `collections.deque` iterable construction / `extendleft`.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ITERABLE-01-S1-01] Lock the current invalid C++ surface (`deque(iterable)`, `extendleft(iterable)`) in focused regressions / TODO / plan.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ITERABLE-01-S2-01] Lower `deque(iterable)` to a valid `::std::deque<T>` constructor surface.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ITERABLE-01-S2-02] Lower `extendleft(iterable)` to a `push_front` loop bundle.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ITERABLE-01-S3-01] Sync build/run smoke and support wording, then close the task.
