# P0: representative C++ support for `collections.deque.count()` / `remove()`

Last updated: 2026-03-13

Related TODO:
- `ID: P0-COLLECTIONS-DEQUE-CPP-SEARCHMUT-01` in `docs/ja/todo/index.md`

Background:
- The representative C++ lane for `collections.deque` now covers the constructor, `append` / `appendleft`, `popleft` / `pop`, `extendleft(iterable)`, `reverse()`, `rotate()`, and `len` / truthiness on the `::std::deque<T>` surface.
- `S1-01` locked the `q.count(...)` / `q.remove(...)` surface leak, `S2-01` aligned `count(value)`, and `S2-02` aligned `remove(value)` to STL algorithm surfaces. Only the representative smoke and closeout remain.
- `clear()`, `extend()`, `reverse()`, and `rotate()` already lower to valid C++ surfaces, so this task is intentionally limited to the remaining `count` / `remove` search-mutate subset.

Goal:
- Align `collections.deque.count()` / `remove()` to valid STL algorithm surfaces in the representative C++ lane.
- Lock the deque representative mutation subset with focused regressions plus smoke.

In scope:
- `from collections import deque`
- representative method subset: `count(value)`, `remove(value)`
- syncing focused regressions, smoke, docs, and TODO

Out of scope:
- the full `deque` API (`maxlen`, arbitrary insert/remove, iterator invalidation semantics, etc.)
- full Python-compat behavior for `remove()` exception messages
- simultaneous rollout to all backends
- redesigning the entire `collections` module
- adding a new deque object hierarchy to the C++ runtime

Acceptance criteria:
- A focused regression locks the state where `count(value)` / `remove(value)` are aligned to STL algorithm surfaces.
- In the representative C++ lane, `count()` lowers to a valid `std::count`-based surface.
- In the representative C++ lane, `remove()` lowers to a first-hit erase surface.
- Representative build/run smoke passes for `count` / `remove` fixtures.
- The ja/en docs and TODO mirrors reflect the support scope and exclusions.

Validation commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k deque_searchmut`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `git diff --check`

Decision log:
- 2026-03-13: `clear()`, `extend()`, `reverse()`, and `rotate()` already lower to valid C++, so the new task is limited to the `count` / `remove` subset only.
- 2026-03-13: as `S1-01`, a focused regression now locks the current invalid `q.count(...)` / `q.remove(...)` surface in the TODO / plan.
- 2026-03-13: as `S2-01`, typed deque-owner `count(value)` now lowers to a `std::count(begin, end, value)` surface. The focused regression is narrowed to the remaining `remove()` leak.
- 2026-03-13: as `S2-02`, typed deque-owner `remove(value)` now lowers to a `std::find + erase` surface, and the not-found path throws `ValueError("deque.remove missing value")`. Only the build/run smoke remains.
- 2026-03-13: as `S3-01`, a representative build/run smoke now locks the `count/remove` bundle output `2 / 2 / 1`. The task now satisfies every acceptance criterion.

## Breakdown

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-SEARCHMUT-01] Lock the representative C++ lane for `collections.deque.count()` / `remove()`.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-SEARCHMUT-01-S1-01] Lock the current invalid C++ surface (`count`, `remove`) in focused regressions / TODO / plan.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-SEARCHMUT-01-S2-01] Lower `count(value)` to a valid `std::count`-based surface.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-SEARCHMUT-01-S2-02] Lower `remove(value)` to a first-hit erase surface.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-SEARCHMUT-01-S3-01] Sync build/run smoke and support wording, then close the task.
