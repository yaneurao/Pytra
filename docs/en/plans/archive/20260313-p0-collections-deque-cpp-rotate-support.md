# P0: representative C++ support for `collections.deque.rotate()`

Last updated: 2026-03-13

Related TODO:
- `ID: P0-COLLECTIONS-DEQUE-CPP-ROTATE-01` in `docs/ja/todo/index.md`

Background:
- The representative C++ lane for `collections.deque` now covers the constructor, `append` / `appendleft`, `popleft` / `pop`, `extendleft(iterable)`, `reverse()`, and `len` / truthiness on the `::std::deque<T>` surface.
- `S1-01` locked the `q.rotate(...)` surface leak, and `S2-01` aligned `rotate()` / `rotate(n)` to valid `::std::rotate(...)` bundles. Only the representative smoke and closeout remain.
- `clear()`, `extend()`, and `reverse()` already lower to valid C++ surfaces, so this task is intentionally limited to the remaining invalid `rotate` subset.

Goal:
- Align `collections.deque.rotate()` / `rotate(n)` to valid `::std::rotate(...)` bundles in the representative C++ lane.
- Lock the deque representative mutation subset with focused regressions plus smoke.

In scope:
- `from collections import deque`
- representative method subset: `rotate()`, `rotate(positive int)`, `rotate(negative int)`
- syncing focused regressions, smoke, docs, and TODO

Out of scope:
- the full `deque` API (`maxlen`, arbitrary insert/remove, iterator invalidation semantics, etc.)
- full support for non-integer or runtime-unknown rotation steps
- simultaneous rollout to all backends
- redesigning the entire `collections` module
- adding a new deque object hierarchy to the C++ runtime

Acceptance criteria:
- A focused regression locks the aligned `rotate()` / `rotate(n)` surface after it lowers to valid `::std::rotate(...)` bundles.
- In the representative C++ lane, `rotate()` / `rotate(n)` lower to valid `::std::rotate(...)` bundles.
- Representative build/run smoke passes for default / positive / negative rotate fixtures.
- The ja/en docs and TODO mirrors reflect the support scope and exclusions.

Validation commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k deque_rotate`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `git diff --check`

Decision log:
- 2026-03-13: `clear()`, `extend()`, and `reverse()` already lower to valid C++, so the new task is limited to the `rotate` subset only.
- 2026-03-13: as `S1-01`, a focused regression now locks the current invalid `q.rotate()`, `q.rotate(1)`, and `q.rotate(-1)` surface in the TODO / plan.
- 2026-03-13: as `S2-01`, typed deque-owner `rotate()` / `rotate(n)` now lower to normalized-step `::std::rotate(...)` bundles. Only the build/run smoke remains.
- 2026-03-13: as `S3-01`, a representative build/run smoke now locks the default / positive / negative rotate output `3 / 3 / 2`. The task now satisfies every acceptance criterion.

## Breakdown

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ROTATE-01] Lock the representative C++ lane for `collections.deque.rotate()`.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ROTATE-01-S1-01] Lock the current invalid C++ surface (`rotate()`, `rotate(1)`, `rotate(-1)`) in focused regressions / TODO / plan.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ROTATE-01-S2-01] Lower `rotate()` / `rotate(n)` to valid `::std::rotate(...)` bundles.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ROTATE-01-S3-01] Sync build/run smoke and support wording, then close the task.
