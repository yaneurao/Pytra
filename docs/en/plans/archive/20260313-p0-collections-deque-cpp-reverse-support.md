<a href="../../../ja/plans/archive/20260313-p0-collections-deque-cpp-reverse-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: representative C++ support for `collections.deque.reverse()`

Last updated: 2026-03-13

Related TODO:
- `ID: P0-COLLECTIONS-DEQUE-CPP-REVERSE-01` in `docs/ja/todo/index.md`

Background:
- The representative C++ lane for `collections.deque` now covers the constructor, `append` / `appendleft`, `popleft` / `pop`, `extendleft(iterable)`, and `len` / truthiness on the `::std::deque<T>` surface.
- `S1-01` locked the `q.reverse();` surface leak, and `S2-01` aligned `reverse()` to `::std::reverse(begin, end)`. Only the representative smoke and closeout remain.
- `clear()` and `extend()` already lower to valid C++ surfaces, so this task is intentionally limited to the remaining invalid `reverse()` surface.

Goal:
- Align `collections.deque.reverse()` to `::std::reverse(begin, end)` in the representative C++ lane.
- Lock the deque representative mutation subset with focused regressions plus smoke.

In scope:
- `from collections import deque`
- representative method subset: `reverse()`
- syncing focused regressions, smoke, docs, and TODO

Out of scope:
- the full `deque` API (`rotate`, `maxlen`, arbitrary insert/remove, iterator invalidation semantics, etc.)
- simultaneous rollout to all backends
- redesigning the entire `collections` module
- adding a new deque object hierarchy to the C++ runtime

Acceptance criteria:
- A focused regression locks the aligned `reverse()` surface after it lowers to `::std::reverse(begin, end)`.
- In the representative C++ lane, `reverse()` lowers to `::std::reverse(q.begin(), q.end())`.
- Build/run smoke passes for a representative fixture.
- The ja/en docs and TODO mirrors reflect the support scope and exclusions.

Validation commands:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k deque_reverse`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`
- `git diff --check`

Decision log:
- 2026-03-13: `clear()` / `extend()` already lower to valid C++, so the new task is limited to `reverse()` only.
- 2026-03-13: as `S1-01`, a focused regression now locks the current invalid `q.reverse();` surface in the TODO / plan.
- 2026-03-13: as `S2-01`, typed deque-owner `reverse()` now lowers to `::std::reverse(begin, end)`. Only the build/run smoke remains.
- 2026-03-13: as `S3-01`, a representative build/run smoke now locks the `deque([1, 2, 3]).reverse()` output `3 / 2 / 1`. The task now satisfies every acceptance criterion.

## Breakdown

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REVERSE-01] Lock the representative C++ lane for `collections.deque.reverse()`.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REVERSE-01-S1-01] Lock the current invalid C++ surface (`q.reverse();`) in focused regressions / TODO / plan.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REVERSE-01-S2-01] Lower `reverse()` to `::std::reverse(begin, end)`.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REVERSE-01-S3-01] Sync build/run smoke and support wording, then close the task.
