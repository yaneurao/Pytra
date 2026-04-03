# P0-EXCEPTION-GO: Go backend exception handling implementation

Last updated: 2026-03-28
Status: Not started

## Background

Go has no native exceptions, so Python's `raise` / `try/except/finally` must be automatically converted to a return-value union (`T | PytraError`). In the Go selfhost, the toolchain code uses try/except, which may become a blocker.

Following spec-exception.md §5, this implements linker marker assignment + EAST3 lowering of ErrorReturn/ErrorCheck/ErrorCatch + Go emitter mapping.

## Subtasks

1. [ID: P0-EXCEPTION-GO-S1] Implement `PytraError` / `PytraValueError` / `PytraRuntimeError` class hierarchy in the Go runtime — struct embedding + `pytraErrorIsInstance(err, tidMin, tidMax)` function
2. [ID: P0-EXCEPTION-GO-S2] Implement transitive assignment of `can_raise_v1` markers in the linker — traverse the call graph to identify functions that contain raise, and propagate markers transitively to callers without try/except
3. [ID: P0-EXCEPTION-GO-S3] In EAST3 language-specific lowering, generate `ErrorReturn`, `ErrorCheck` (propagate/catch), and `ErrorCatch` nodes for `Raise` when `exception_style: "union_return"`
4. [ID: P0-EXCEPTION-GO-S4] Map `ErrorReturn` / `ErrorCheck` / `ErrorCatch` in the Go emitter — `(T, *PytraError)` return values, `if _err != nil` propagation, type_id range check for isinstance, `defer` for finally
5. [ID: P0-EXCEPTION-GO-S5] Add fixtures (raise/try/except/finally, user-defined exceptions, multiple handlers, nesting) + confirm Go parity

## Acceptance Criteria

1. `raise ValueError("msg")` is converted to `return _zero, &PytraValueError{...}` in Go
2. `try/except ValueError` becomes a type_id range check isinstance judgment in Go
3. `except ValueError` also catches classes derived from ValueError (such as ParseError)
4. `finally` is mapped to Go's `defer` and executes in both normal and error paths
5. Existing fixture + sample Go parity is maintained

## Decision Log

- 2026-03-28: Decided to implement exception handling for Go/Rust/Zig using the union_return approach. Exception types are treated as regular classes (with type_id), and isinstance is determined by type_id range check. Detailed specification written in spec-exception.md.
