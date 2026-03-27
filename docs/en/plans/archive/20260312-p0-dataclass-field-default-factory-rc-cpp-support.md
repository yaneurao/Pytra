<a href="../../../ja/plans/archive/20260312-p0-dataclass-field-default-factory-rc-cpp-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Representative C++ support for `field(default_factory=...)` on rc fields

Last updated: 2026-03-12

Related TODO:
- `ID: P0-DATACLASS-FIELD-DEFAULT-FACTORY-RC-CPP-01` in `docs/ja/todo/index.md`

Background:
- The Pytra-NES minimal sample [`materials/refs/from-Pytra-NES/field_default_factory_rc_obj.py`](../../../materials/refs/from-Pytra-NES/field_default_factory_rc_obj.py) uses `field(default_factory=Child)` on an `rc<Child>` field.
- In the current representative C++ lane, this emits an invalid default argument such as `Parent(rc<Child> child = Child())`, which fails to build because `Child` cannot be converted to `rc<Child>`.
- The earlier task that absorbs `field(...)` as static metadata is already in progress, so the core issue here is the rc-lane lowering of `default_factory`.

Objective:
- Lower `field(default_factory=...)` correctly for rc fields in the representative C++ lane and remove the Pytra-NES blocker.
- Lock as current contract that dataclass metadata lowers `default_factory` differently in value lanes and rc lanes.

In scope:
- dataclass field metadata for `default_factory`
- representative C++ rc-field lane
- focused regressions, docs, and TODO sync

Out of scope:
- full Python dataclasses compatibility
- arbitrary callable `default_factory`
- simultaneous rollout to non-C++ backends
- `field(metadata=...)` and reflection-like features

Acceptance criteria:
- The current failure of the minimal sample `field_default_factory_rc_obj.py` is locked with a focused regression.
- In the representative C++ lane, `default_factory=Child` on an rc field lowers to the correct lane, equivalent to `::rc_new<Child>()`, and compile smoke passes.
- The lowering difference between value lanes and rc lanes is recorded in regressions and docs.
- The current representative subset of `default_factory` support is explicitly documented in the plan and TODO.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k dataclass_field`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core_parser_behavior_classes.py' -k field`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: This task is limited to the representative `default_factory` rc lane that blocks Pytra-NES, not `field(...)` support as a whole.
- 2026-03-12: v1 targets the representative subset of zero-arg class factories and keeps arbitrary callables fail-closed.

## Breakdown

- [x] [ID: P0-DATACLASS-FIELD-DEFAULT-FACTORY-RC-CPP-01] Align the `field(default_factory=...)` rc-field lane with the representative C++ contract and remove the Pytra-NES blocker.
- [x] [ID: P0-DATACLASS-FIELD-DEFAULT-FACTORY-RC-CPP-01-S1-01] Lock the minimal-sample baseline and current C++ failure with focused regressions, TODO, and plan.
- [x] [ID: P0-DATACLASS-FIELD-DEFAULT-FACTORY-RC-CPP-01-S2-01] Align `default_factory` with the correct ctor/member-init lowering in the representative C++ rc-field lane.
- [x] [ID: P0-DATACLASS-FIELD-DEFAULT-FACTORY-RC-CPP-01-S3-01] Sync docs, support wording, and representative-subset regressions with the current contract and close the task.

- 2026-03-12: In the representative C++ lane, `field(default_factory=Child)` on an `rc<...>` field now lowers ctor defaults/member init to `::rc_new<Child>()` as the current contract.
- 2026-03-12: The representative static dataclass subset is now locked in parser/C++ regressions and support docs through `default`, `default_factory=deque`, and `default_factory=Child` on `rc<Child>`, while arbitrary callable `default_factory` stays out of scope.
