# P0 C++ iter boundary runtime contract

Last updated: 2026-04-03

## Purpose

Establish a fixed contract for how the C++ backend handles `ObjIterInit` / `ObjIterNext`, as a prerequisite for proceeding with `P0-CPP-VARIANT-S10`.

The current situation has the following misalignments:

- `src/toolchain2/compile/lower.py` generates `iter.init` / `iter.next` as `ObjIterInit` / `ObjIterNext`
- `src/toolchain2/emit/cpp/emitter.py` does not handle `ObjIterInit` / `ObjIterNext` directly
- `src/runtime/cpp/` has no `py_iter_or_raise` / `py_next_or_stop` free helpers
- Furthermore, the generic helpers in the linked runtime — currently `py_any` / `py_all` in [predicates.east](../../runtime/east/built_in/predicates.east) — assume `ForCore(iter_plan.init_op=ObjIterInit, next_op=ObjIterNext)`

In this state, the work of removing the iter boundary from `lower.py` and the contract cleanup for the C++ runtime / emitter are tightly coupled.

## Approach

1. `P0-CPP-VARIANT-S10B`
   - Decide on the iter boundary contract to adopt in the C++ runtime / emitter
   - Candidates:
     - Emit `ObjIterInit` / `ObjIterNext` directly
     - Re-introduce free helpers
     - Return the method-call contract to the runtime core
   - Additional prerequisites:
     - Also decide simultaneously how to replace the linked runtime's generic iter helpers
     - Currently `py_any` / `py_all` in `src/runtime/east/built_in/predicates.east` re-inject the iter boundary seam into the C++ backend

2. `P0-CPP-VARIANT-S10`
   - Incrementally remove `resolved_type="object"` boxing and the iter boundary from `lower.py` in accordance with the contract established above

## State as of 2026-04-03

- `iter_ops.py` has been removed from the canonical source; the old blocker no longer exists in the current repo
- A full fixture scan through C++ lowering shows 0 instances of `resolved_type="object"` on non-explicit dynamic paths
- Residual seams are:
  - Explicit object contracts: `trait_basic`, `trait_with_inheritance`, `typed_container_access`
  - Bare `Callable -> object` boundary
  - Runtime generic iter helper: `py_any` / `py_all` in `src/runtime/east/built_in/predicates.east`

## Completion Criteria

- The iter boundary residual seam is separated as a distinct contract from explicit object / bare `Callable`
- The dependency on `predicates.east` as the home of the runtime generic iter helper is recorded and can be tracked independently from the `S10` main work
