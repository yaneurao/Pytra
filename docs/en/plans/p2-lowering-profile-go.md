# P2-LOWERING-PROFILE-GO: Apply lowering profile to the Go backend

Last updated: 2026-03-28
Status: Not started

## Background

The lowering profile (spec-language-profile.md §7) and per-language EAST3 lowering (tuple_unpack_style, container_covariance, with_style, property_style) have been implemented for the C++ side but are not yet applied to Go.

Many of the issues blocking the Go emitter in selfhost (tuple unpack, container covariance, `with` statement, `@property`) would be resolved by applying the lowering profile to Go.

## Subtasks

1. [ID: P2-LOWERING-GO-S1] Apply Go's `tuple_unpack_style: "multi_return"` to EAST3 lowering — expand tuple unpack into `MultiAssign` so that the Go emitter can map it to `x, y := f()`. Normalize function return types to `multi_return[A, B]`.
2. [ID: P2-LOWERING-GO-S2] Apply Go's `container_covariance: false` to EAST3 lowering — expand type conversions such as `list[str]` → `list[JsonVal]` into `CovariantCopy` nodes so that the Go emitter generates per-element copy loops.
3. [ID: P2-LOWERING-GO-S3] Apply Go's `with_style: "defer"` to EAST3 lowering — expand `With` nodes into a form suited to Go's `defer` pattern.
4. [ID: P2-LOWERING-GO-S4] Apply Go's `property_style: "method_call"` to EAST3 lowering — normalize `attribute_access_kind: "property_getter"` to a parenthesized method call.
5. [ID: P2-LOWERING-GO-S5] Confirm that existing fixture + sample parity for Go is maintained.

## Acceptance Criteria

1. The Go emitter handles tuple unpack via multiple return values according to `tuple_unpack_style`.
2. Container covariance type conversions work correctly in Go.
3. `with` statements are mapped to Go's `defer`.
4. `@property` access becomes a parenthesized method call in Go.
5. Existing fixture + sample Go parity is maintained.

## Decision Log

- 2026-03-28: P2-LOWERING-PROFILE was closed with only the C++ side Completed. Filed applying the lowering profile to Go as a separate task.
