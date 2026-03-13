# P1: align the `rc<list<T>>` lane for `field(default_factory=lambda: [0] * N)` in C++

Last updated: 2026-03-13

Related TODO:
- `docs/ja/todo/index.md` `ID: P1-NES3-LIST-DEFAULT-FACTORY-RC-LIST-CPP-01`

Background:
- The Pytra-NES3 repro [`materials/refs/from-Pytra-NES3/list_default_factory.py`](../../../materials/refs/from-Pytra-NES3/list_default_factory.py) uses `field(default_factory=lambda: [0] * 8)` on an `rc<list<int64>>` field.
- An archived task already covered the representative `field(default_factory=Child)` lane on `rc<Child>`, but as of 2026-03-13 the C++ lane still emits the list factory as a plain `list<int64>` value, which does not match `rc<list<int64>>`.
- The generated default argument also uses a capture-default lambda in an invalid position, so the emitted C++ is structurally wrong as well.

Objective:
- Support zero-capture list factories for `rc<list<T>>` fields as a representative subset.
- Lock the contract difference between the value lane and the `rc<list<T>>` lane with compile smoke and regressions.

In scope:
- Dataclass field metadata for `default_factory=lambda: [0] * N`
- Constructor-default / member-init lowering for `rc<list<T>>`
- Compile smoke for `materials/refs/from-Pytra-NES3/list_default_factory.py`
- Regression, docs, and TODO sync

Out of scope:
- Arbitrary callable `default_factory` support in general
- Closure factories with captures
- Non-C++ backends

Acceptance criteria:
- The generated C++ for `list_default_factory.py` compiles.
- The generated code stops passing a raw `list<T>` value directly into the `rc<list<T>>` lane and lowers through a representative contract-compatible path.
- Existing `default_factory=Child` and `default_factory=deque` lanes keep working.

Validation commands (planned):
- `python3 tools/check_todo_priority.py`
- `bash ./pytra materials/refs/from-Pytra-NES3/list_default_factory.py --target cpp --output-dir /tmp/pytra_nes3_list_default_factory`
- `g++ -std=c++20 -O0 -c /tmp/pytra_nes3_list_default_factory/src/list_default_factory.cpp -I /tmp/pytra_nes3_list_default_factory/include -I /workspace/Pytra/src -I /workspace/Pytra/src/runtime/cpp`
- `git diff --check`

## Breakdown

- [ ] [ID: P1-NES3-LIST-DEFAULT-FACTORY-RC-LIST-CPP-01-S1-01] Lock the current compile failure and representative-subset boundary in focused regressions, the plan, and TODO.
- [ ] [ID: P1-NES3-LIST-DEFAULT-FACTORY-RC-LIST-CPP-01-S2-01] Align `default_factory=lambda: [0] * N` for the `rc<list<T>>` lane with the correct constructor/member-init lowering.
- [ ] [ID: P1-NES3-LIST-DEFAULT-FACTORY-RC-LIST-CPP-01-S3-01] Sync compile smoke and docs wording to the current subset contract.

Decision log:
- 2026-03-13: Split out as the next step after the archived representative `default_factory` support, limited to list factories on `rc<list<T>>`.
