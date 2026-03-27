<a href="../../../ja/plans/archive/20260312-p0-collections-deque-cpp-representative-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Representative C++ support for `collections.deque[T]`

Last updated: 2026-03-12

Related TODO:
- `ID: P0-COLLECTIONS-DEQUE-CPP-REPRESENTATIVE-01` in `docs/ja/todo/index.md`

Background:
- Pytra-NES uses dataclass fields such as `timestamps: deque[float] = field(init=False, repr=False)` in real code.
- The `field(...)` leak itself was already fixed, but the baseline C++ emitter still produced raw `deque[float64]`.
- The current user need is not full Python `collections.deque` compatibility; it is a representative C++ lane that unblocks Pytra-NES.

Goal:
- Make `collections.deque[T]` usable in the representative C++ lane and unblock the Pytra-NES dataclass-field / mutable-queue use case.
- Keep this separate from the `field(...)` task and lock the `deque[T]` type / ctor / member lane as the current support contract.

In scope:
- `from collections import deque`
- C++ type lowering for `deque[T]` annotations
- representative dataclass-field and zero-arg constructor lanes
- syncing focused regressions / docs / TODO

Out of scope:
- simultaneous rollout to all backends
- full Python `deque` compatibility (`maxlen`, rotate, full rich API)
- redesign of `collections` as a whole
- reflection-like dataclass support

Acceptance criteria:
- A representative C++ regression locks the raw `deque[T]` type-leak baseline.
- `deque[T]` lowers to `::std::deque<T>` in the representative C++ lane and passes a focused compile smoke.
- The ja/en plan and TODO mirrors record the Pytra-NES blocker and scope.
- The follow-up bundles are split cleanly into `type lowering` and `zero-arg ctor/member lane`.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k deque`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core_parser_behavior_classes.py' -k deque`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: The static-metadata work for `dataclasses.field(...)` is already complete, so this task is restricted to `deque[T]` type lowering and representative runtime lanes rather than field semantics.
- 2026-03-12: v1 only targets the representative C++ lane; non-C++ rollout is deferred.
- 2026-03-12: The baseline is locked by `test_deque_annotation_current_baseline_still_leaks_raw_cpp_type`, which records the current representative failure where the C++ emitter still outputs raw `deque[float64]`.
- 2026-03-12: `S2-01` keeps the runtime surface minimal by lowering directly to `::std::deque<T>` and adding only the required `<deque>` includes in `py_types.h` and the header builder.
- 2026-03-12: `S2-02` stays scoped to the dataclass field lane that blocks Pytra-NES, locking `init=False` zero-arg construction and `default_factory=deque` compile smoke without changing the general plain-class constructor policy.
- 2026-03-12: `S3-01` documents the C++ support wording as `partial`: the representative contract covers type lowering and the dataclass field lane only, while full `deque` API compatibility remains out of scope.

## Breakdown

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REPRESENTATIVE-01] Lock the representative C++ lane for `collections.deque[T]` and remove the Pytra-NES blocker.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REPRESENTATIVE-01-S1-01] Lock the current baseline failure and representative scope in focused regressions / TODO / plan.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REPRESENTATIVE-01-S2-01] Lock representative C++ type lowering for `deque[T]`.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REPRESENTATIVE-01-S2-02] Align the zero-arg constructor / dataclass-field member lane with representative C++ emission.
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REPRESENTATIVE-01-S3-01] Sync docs / regressions / support wording to the current contract and close the task.
