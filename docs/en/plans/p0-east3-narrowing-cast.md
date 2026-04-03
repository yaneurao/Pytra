<a href="../../ja/plans/p0-east3-narrowing-cast.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P0-EAST3-NARROWING-CAST: Insert Cast/Unbox nodes after isinstance narrowing

Last updated: 2026-03-30
Status: Not started

## Background

EAST3 updates `resolved_type` after isinstance narrowing but does not insert explicit Cast/Unbox nodes. For example:

```python
val: JsonVal = json.loads(data)
if isinstance(val, str):
    print(val.upper())  # val is narrowed to str
```

In EAST3 the `resolved_type` of `val` is updated to `str`, but the expression node remains the original `Name("val")`. For languages like Rust that require a downcast from `PyAny` to a concrete type, the emitter is forced to implement its own logic — "this Name's `resolved_type` differs from its declared type → insert a conversion call" — which violates emitter guide §1.1.

## Current state

- spec-east.md §7.1: specifies that narrowing is achieved by updating the type environment at the resolve stage and that no new EAST nodes are introduced
- Rust emitter: implements a workaround in `_emit_name` with an `EAST3 DEFICIENCY WORKAROUND` comment
- C++/Go/TS: the problem does not manifest because implicit casts work

## Proposal

Wrap Name references whose `resolved_type` has changed due to isinstance narrowing in a **Cast node**.

```json
// Current: only resolved_type of Name is updated
{"kind": "Name", "id": "val", "resolved_type": "str"}

// Proposed: wrap in a Cast node
{"kind": "Cast", "value": {"kind": "Name", "id": "val", "resolved_type": "JsonVal"}, "to": "str", "reason": "isinstance_narrowing"}
```

- The original Name retains the type at declaration time (`JsonVal`)
- The Cast node explicitly states the conversion to the narrowed type (`str`)
- The emitter simply renders the Cast node (compliant with §1.1)

## Files to change

`src/toolchain2/compile/east2_to_east3_lowering.py` or the narrowing logic in `src/toolchain2/resolve/`.

When `resolved_type` is updated during narrowing, insert a Cast node only when the type differs from the original. Do not insert a Cast node when the type is the same (redundant cast).

## Impact

- Cast nodes will increase, so emitters for all languages need to be able to render Cast nodes (most are already capable)
- C++/Go/TS were relying on implicit casts, so adding explicit Cast nodes will not change the output (Cast output may be skipped by implicit_promotions in some cases)
- Rust will remove the workaround and replace it with Cast node rendering
- spec-east.md §7.1's "no new EAST nodes are introduced" will need to be updated to "wrap in a Cast node"

## Decision Log

- 2026-03-30: The narrowing workaround in `_emit_name` of the Rust emitter was identified as a §1.1 violation. Decided to insert Cast nodes on the EAST3 side. The Rust team is responsible for the EAST3 fix.
