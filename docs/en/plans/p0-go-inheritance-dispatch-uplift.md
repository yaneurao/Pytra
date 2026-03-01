# P0: Improve Go inheritance-method dynamic dispatch

Last updated: 2026-03-01

Related TODO:
- `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-GO` in `docs/ja/todo/index.md`

Background:
- The Go backend builds inheritance-like structures via embedding, but does not guarantee Python-compatible dispatch via base references.

Goal:
- Organize lowering so inheritance-method calls preserve Python-equivalent resolution order.

Scope:
- `src/hooks/go/emitter/go_native_emitter.py`
- `src/runtime/go/pytra/py_runtime.go` if needed

Out of scope:
- Multiple inheritance beyond Go language semantics

Acceptance criteria:
- `super()`-equivalent call paths are enabled and not treated as no-op.
- Code generation rules are established that satisfy expected fixture output.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets go`

Breakdown:
- [x] Compare inheritance representation approaches in Go (embedding/interface) and finalize the adopted approach.
- [x] Implement rules for `super()` lowering and derived-method resolution.
- [x] Lock non-regression via fixture regressions.

Decision log:
- 2026-03-01: Created a dedicated plan for Go due to larger design differences.
- 2026-03-01: Adopted receiving inheritance type annotations via class interfaces (`AnimalLike`, etc.) rather than `*Class`, enabling dynamic dispatch through base references.
- 2026-03-01: Implemented rules lowering `super().method(...)` to embedded-base calls (`self.<Base>.method(...)`) and `super().__init__(...)` to `self.<Base>.Init(...)`.
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v` passed (12 tests, 0 fail).
- 2026-03-01: `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets go --ignore-unstable-stdout` passed (1/1).
