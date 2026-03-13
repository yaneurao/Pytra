# P0: representative C++ support for `collections.deque` appendleft / pop

Last updated: 2026-03-13

Related TODO:
- `ID: P0-COLLECTIONS-DEQUE-CPP-ENDOPS-01` in `docs/ja/todo/index.md`

Background:
- The representative C++ lane for `collections.deque` was aligned in the previous task through `deque()` / `bool(q)` / `len(q)` / `append` / `popleft`.
- However, the paired end-op queue operations `appendleft` and `pop` still leak Python surface directly into emitted C++.
- In the current baseline, `appendleft` is emitted as `q.appendleft(1);` and `pop` as `q.pop()`, which is not valid C++ for `::std::deque<T>`.
- `clear()` already emits as `q.clear();`, which is valid C++, so this task is intentionally limited to the remaining invalid end-op surface.

Goal:
- Align the representative `collections.deque` end-op subset with `::std::deque<T>` in the C++ lane.
- Extend the current support contract so the minimal practical queue/deque subset is covered end to end.

In scope:
- `from collections import deque`
- representative method subset: `appendleft`, `pop`
- `pop()` return surface for both typed and untyped assignment targets
- syncing focused regressions, smoke, docs, and TODO

Out of scope:
- the full `deque` API (`extendleft`, `rotate`, `maxlen`, iterator invalidation semantics, etc.)
- simultaneous rollout to all backends
- redesigning the entire `collections` module
- adding a new C++ runtime object hierarchy such as `PyDequeObj`

Acceptance criteria:
- A baseline regression locks the current invalid C++ surface (`appendleft`, `pop`).
- In the representative C++ lane, `appendleft` lowers to `push_front`.
- In the representative C++ lane, `pop` lowers to a `back + pop_back` lambda.
- Both typed and untyped `pop()` receivers keep a valid C++ surface.
- Build/run smoke passes for a representative fixture.
- The ja/en docs and TODO mirrors reflect the support scope and exclusions.

Validation commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k deque`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `git diff --check`

Decision log:
- 2026-03-13: `appendleft` / `pop` are the remaining invalid surface in the representative `deque` lane, so they are split into a new P0 task.
- 2026-03-13: `clear()` is excluded from this task because it is already emitted as valid C++ for `std::deque`.
- 2026-03-13: as `S1-01`, a focused regression now locks the leaked `q.appendleft(1);` and `q.pop()` surface. This remains the baseline until the lowering is implemented.

## Breakdown

- [ ] [ID: P0-COLLECTIONS-DEQUE-CPP-ENDOPS-01] Lock the representative C++ lane for `collections.deque` `appendleft` / `pop`.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ENDOPS-01-S1-01] Lock the current invalid C++ surface (`appendleft`, `pop`) in focused regressions / TODO / plan.
- [ ] [ID: P0-COLLECTIONS-DEQUE-CPP-ENDOPS-01-S2-01] Lower `appendleft` to `push_front`.
- [ ] [ID: P0-COLLECTIONS-DEQUE-CPP-ENDOPS-01-S2-02] Lower `pop` to a `back + pop_back` lambda and align typed / untyped return surfaces.
- [ ] [ID: P0-COLLECTIONS-DEQUE-CPP-ENDOPS-01-S3-01] Sync build/run smoke and support wording, then close the task.
