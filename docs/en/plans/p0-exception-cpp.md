# P0-EXCEPTION-CPP: C++ backend exception handling implementation (CommonRenderer integration)

Last updated: 2026-03-28
Status: Completed

## Background

C++ has native exceptions (throw/try-catch), so `exception_style: "native_throw"` maps EAST3's `Raise` / `Try` directly. Using CommonRenderer's shared skeleton, the C++ emitter is implemented with only syntax token overrides.

## Subtasks

1. [ID: P0-EXCEPTION-CPP-S1] Implement a shared skeleton for `emit_raise` / `emit_try` in CommonRenderer — node traversal for `native_throw` languages (Raise → throw expression, Try → try block + handler branching + finally)
2. [ID: P0-EXCEPTION-CPP-S2] Override the mapping of `Raise` → `throw ExceptionType("msg")` in the C++ emitter
3. [ID: P0-EXCEPTION-CPP-S3] Override the mapping of `Try` → `try { } catch (ExceptionType& e) { }` in the C++ emitter — `except ValueError` also catches derived classes (C++ catch works naturally via inheritance)
4. [ID: P0-EXCEPTION-CPP-S4] Map `finally` to RAII / scope guard in the C++ emitter
5. [ID: P0-EXCEPTION-CPP-S5] Add fixtures (raise/try/except/finally, user-defined exceptions, multiple handlers) + confirm C++ compile + run parity

## Design notes

- C++'s `catch (ValueError& e)` naturally catches derived classes via C++ inheritance. No type_id range check is needed.
- `finally` has no native syntax in C++. It is implemented with a scope guard (RAII pattern):
  ```cpp
  {
      auto _finally = pytra_scope_guard([&]() { cleanup(); });
      try { ... } catch (...) { ... }
  }
  ```
- The `emit_raise` / `emit_try` skeleton in CommonRenderer is a separate path from Go's `union_return`. `native_throw` languages (Java, C#, Kotlin, etc.) will use the same skeleton.

## Acceptance Criteria

1. `raise ValueError("msg")` is converted to `throw PytraValueError("msg")` in C++
2. `try/except/finally` is converted to `try/catch` + scope guard in C++
3. `except ValueError` also catches classes derived from ValueError (natural behavior via C++ inheritance)
4. The `emit_raise` / `emit_try` skeleton is implemented in CommonRenderer, and the C++ emitter consists only of overrides
5. Existing fixture + sample C++ parity is maintained

## Decision Log

- 2026-03-28: C++ is implemented with native_throw. Approach decided: build the CommonRenderer shared skeleton first, C++ emitter uses only overrides. finally is handled with RAII scope guard.
- 2026-03-28: `src/pytra/built_in/error.py` is adopted as the pure Python source of truth and flows through the runtime EAST; unified so that C++ also uses Python exception classes directly with throw/catch rather than `std::exception`.
- 2026-03-28: `error.h` runtime header generation follows EAST3's `base`, maintaining the C++ inheritance that lets `except ValueError` naturally catch user-defined derived exceptions.
- 2026-03-28: Added parity fixture `exception_user_defined_multi_handler.py`. Confirmed C++ build+run for `try_raise` / `finally` / `exception_propagation_two_frames` / `exception_user_defined_multi_handler`.
