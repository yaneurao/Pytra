# P0 CommonRenderer box/unbox normalization

Last updated: 2026-04-02

## Background

In the C++ backend, the emit logic for `optional[T]` / general unions / callable arguments each carries its own backend-local box/unbox and cast normalization. As a result, the following C++-specific breakdowns occurred in runtime parity:

- Dereferencing `optional[int64]` twice, producing `*(*indent)`
- Creating an unnecessary `object` lambda bridge for `std::function<T(U)>` arguments
- Stacking additional boxing / unboxing on top of an expression that already matches the target type

These issues are not caused by the C++ output syntax itself; they stem from a lack of shared normalization that prevents the same semantic transformation from being applied more than once. Rather than patching each backend individually, the fix should be moved into CommonRenderer to prevent recurrence.

## Approach

- Move idempotent box/unbox/cast decisions that can be evaluated without backend knowledge into CommonRenderer
- Backends are responsible only for the final surface representation
  - C++: `*opt`, `std::get<T>`, `std::holds_alternative<T>`, etc.
- When a decision cannot be made, fall back (fail-closed) to the current backend implementation

## Target

- Suppressing `Box(Box(x))`
- Suppressing `Unbox(Unbox(x))`
- Suppressing double unbox for `optional[T] -> T`
- Suppressing unnecessary cast / boxing for expressions that already match the target type
- Suppressing bridges driven by a stale `call_arg_type=object` at callable boundaries

## Out of scope

- C++-specific ownership / ref / `Object<T>` generation rules
- Concrete syntax selection for `std::optional` / `std::variant`
- Eliminating box/unbox node generation from EAST itself

## Completion Criteria

- CommonRenderer has a shared entry point for box/unbox/cast normalization
- The C++ emitter uses that shared entry point
- C++ parity for `json_extended`, `json_indent_optional`, `json_unicode_escape`, and `callable_higher_order` all PASS
- The number of stop-gap box/unbox branches remaining in backend-specific code has decreased
