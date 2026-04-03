<a href="../../../ja/spec/archive/20260328-spec-zig-native-backend.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Zig Native Backend Contract Specification

This document defines the contract for the Zig native emitter (EAST3 → direct Zig generation).

## 1. Purpose

- Fix the responsibility boundary for implementing the Zig backend as a direct native generator with no sidecar dependency.
- Document the supported scope and failure conditions on unsupported input, even at the initial implementation stage.

## 2. Input EAST3 Node Responsibilities

The Zig native emitter accepts only EAST3 documents satisfying the following.

- Root is a `dict` with `kind == "Module"`.
- `east_stage == 3` (`--east-stage 2` is not accepted).
- `body` is a sequence of EAST3 statement nodes.

## 3. Fail-Closed Contract

On receiving unsupported input, fail immediately without escaping to a compatibility path.

- Raise `RuntimeError` the moment an unsupported `kind` / shape is detected.
- The error message must include at least `lang=zig` and the failure kind (node/shape).
- The CLI must exit non-zero and must not treat incomplete `.zig` output as a success.

## 4. Runtime Boundary

The runtime boundary for Zig-generated code is limited in principle to the following.

- The Zig runtime API under `src/runtime/zig/built_in/`
- The Zig standard library (`std`)

## 5. Unsupported Features (Permanent Constraints Due to Zig Language Characteristics)

The following Python features are out of scope for conversion due to Zig's language design.

### 5.1 try/except/finally (Exception Handling)

Zig has no exception mechanism. Python's `try/except/finally` is not converted to Zig.

- Statements inside the `try` block are emitted as-is (straight-line execution without guards).
- `except` handlers are not emitted (treated as unreachable).
- Statements inside the `finally` block are emitted as-is after the `try` body.
- `raise` is converted to `@panic()` (immediate process termination).
- Logic that depends on exceptions in the input Python (flows that branch on `except`) will not behave as expected in the Zig backend. This is a constraint by design.

### 5.2 Class Inheritance (Composition Pattern)

Zig has no class inheritance, so conversion uses the composition (delegation) pattern.

- A single class (no inheritance) is converted to a `struct`.
- `class Dog(Animal)` gives the `Dog` struct a `_base: Animal` field.
- Base class methods that are not overridden automatically generate delegation functions via `self._base.method()`.
- `super().__init__()` cannot be converted as the Pytra parser currently does not support it.
- Polymorphism (assigning `Dog` to an `Animal`-typed variable) can be handled by taking a pointer with `&dog._base`. However, virtual dispatch (dynamic dispatch of overriding methods) is not supported.

### 5.3 isinstance / issubclass

Zig has no runtime type inspection. `isinstance` / `issubclass` are stub implementations (always returning `false`).

### 5.4 Reference Semantics

Zig is value-type by default and cannot directly express Python's reference semantics (object sharing / aliasing).

- Assignments to function arguments may not be reflected in the original.
- This constraint is permanent, arising from Zig's language design; conversion to pointer passing is a target for future improvement.

## 6. Verification Perspectives (Initial)

- `transpile_to_zig_native()` can generate `.zig` from EAST3.
- `check_py2x_transpile.py --target zig` succeeds for all fixture conversions.
- Basic tests pass in `tools/unittest/emit/zig/test_py2zig_smoke.py`.
- The majority of core/control fixtures compile and run with `zig build-exe` and produce the same stdout as Python.
