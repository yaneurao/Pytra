<a href="../../../ja/plans/archive/20260313-p0-collections-deque-cpp-expr-method-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: representative C++ support for `collections.deque` expressions and methods

Last updated: 2026-03-13

Related TODO:
- `ID: P0-COLLECTIONS-DEQUE-CPP-EXPR-METHOD-01` in `docs/ja/todo/index.md`

Background:
- The representative C++ contract for `deque[T]` type annotations and dataclass-field lanes is already fixed, so the original Pytra-NES blocker around `timestamps: deque[float] = field(init=False, repr=False)` itself is no longer blocked.
- However, the plain expression / method lane still leaks Python surface directly into emitted C++.
- In the current baseline, `deque()` is emitted as `q = deque();`, `append` as `q.append(1);`, `popleft` as `q.popleft();`, truthiness as `py_to<bool>(q)`, and `len` as `py_len(q)`, which is not valid C++ for `::std::deque<T>`.
- The next practical Pytra-NES blocker is queue operations, so the right move is to lock a representative subset first instead of aiming for full `deque` compatibility.

Goal:
- Align the expression / method surface of `collections.deque` with valid `::std::deque<T>` lowering in the representative C++ lane.
- Lock a first-pass subset of queue operations as the current support contract.

In scope:
- `from collections import deque`
- zero-arg `deque()` expressions
- representative method subset: `append`, `popleft`
- representative utility subset: `len(deque)`, truthiness
- syncing focused regressions, docs, and TODO

Out of scope:
- the full `deque` API (`appendleft`, `extend`, `rotate`, `maxlen`, iterator invalidation semantics, etc.)
- simultaneous rollout to all backends
- redesigning the entire `collections` module
- adding a new C++ runtime object hierarchy such as `PyDequeObj`

Acceptance criteria:
- A baseline regression locks the current invalid C++ surface (`deque()`, `.append`, `.popleft`, `py_to<bool>(deque)`, `py_len(deque)`).
- In the representative C++ lane, `deque()` lowers to `::std::deque<T>{}`.
- In the representative C++ lane, `append` lowers to `push_back` and `popleft` lowers to a `front + pop_front` equivalent.
- In the representative C++ lane, `len(deque)` and truthiness lower to valid C++ (`.size()`, `!empty()`).
- Build/run smoke passes for a representative fixture.
- The ja/en docs and TODO mirrors reflect the support scope and exclusions.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k deque`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-13: since `dataclasses.field(...)` and the `deque[T]` annotation lane are already closed, this new task is limited to the representative queue-operation subset.
- 2026-03-13: the first-pass subset is restricted to `deque()`, `append`, `popleft`, `len`, and truthiness, matching the immediate Pytra-NES need. `appendleft` and beyond are deferred.
- 2026-03-13: the baseline is locked via C++ source regressions instead of direct compile-failure assertions, to avoid compiler-error-text brittleness.
- 2026-03-13: as `S1-01`, a focused regression now locks `q = deque();`, `q.append(1);`, `q.popleft();`, `py_to<bool>(q)`, and `py_len(q)` as the current invalid C++ surface.
- 2026-03-13: as `S2-01`, `deque()` now lowers to `::std::deque<T>{}`, `bool(q)` to `!q.empty()`, and `len(q)` to `q.size()`. The remaining invalid Python surface is limited to `append` / `popleft`.
- 2026-03-13: `popleft()` was already lowering through the existing attr-call lane into a `front + pop_front` lambda, so after the `S2-01` regression refresh the only remaining invalid Python surface is `append`.
- 2026-03-13: as `S2-02`, typed `deque[T].append(...)` now lowers to `push_back(...)`. The representative lowering is now aligned for `deque()` / `bool(q)` / `len(q)` / `append` / `popleft`, and only build/run smoke plus support wording remain.
- 2026-03-13: as `S3-01`, a representative build/run smoke now locks the `False / 0 / 1` output. All acceptance criteria for this task are now satisfied.

## Breakdown

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-EXPR-METHOD-01] Lock the representative C++ expression / method lane for `collections.deque`.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-EXPR-METHOD-01-S1-01] Lock the current invalid C++ surface in focused regressions / TODO / plan.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-EXPR-METHOD-01-S2-01] Align `deque()` expressions and `len/truthiness` with representative C++ lowering.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-EXPR-METHOD-01-S2-02] Align the `append` method subset with representative C++ lowering and keep the `popleft` representative regression green.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-EXPR-METHOD-01-S3-01] Sync build/run smoke and support wording, then close the task.
