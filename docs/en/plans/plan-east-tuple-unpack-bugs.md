# Plan: Fix EAST tuple unpack bugs (P0-EAST-TUPLE-UNPACK)

## Background

The `tuple_unpack_variants` fixture revealed 3 bug patterns in EAST3 tuple unpacking. These are valid Python syntax that is not correctly represented in EAST3.

## Bug List

| Pattern | EAST3 result | Status |
|---|---|---|
| `x, y, z = 1, 2, 3` | `TupleUnpack` | ✅ Correct |
| `(x, y, z) = (1, 2, 3)` | Collapses to `Expr` (assignment disappears) | ❌ Bug |
| `[x, y, z] = [1, 2, 3]` | Collapses to `Expr` (assignment disappears) | ❌ Bug |
| `x, y, z = [1, 2, 3]` | `TupleUnpack` | ✅ Correct |
| `x, y, z = [i for i in range(3)]` | comprehension expansion causes unpack assignment to vanish | ❌ Bug |
| `a[0], a[1], a[2] = [1, 2, 3]` | `TupleUnpack` | ✅ Correct |
| `a, (b, c) = 1, (2, 3)` | `TupleUnpack` | ✅ Correct |
| `x, y = y, x` | `Swap` | ✅ Correct |

## Root Cause Analysis

### Bug 1: Parenthesized left-hand side `()` / `[]`

For `(x, y, z) = ...` and `[x, y, z] = ...`, when the left-hand side is enclosed in parentheses or square brackets, the parser fails to recognize it as an assignment target and collapses it to `Expr`.

In Python's AST, `(x, y, z)` and `[x, y, z]` are treated as identical assignment targets to `x, y, z`. The EAST parser does not handle this equivalence.

### Bug 2: comprehension + unpack

For `x, y, z = [i for i in range(3)]`:
1. The list comprehension is expanded to `__comp_1` (correct)
2. However, the tuple unpack assignment `x, y, z = __comp_1` is not generated (bug)

The comprehension expansion path loses the original assignment target information.

## Fix Approach

### Bug 1

In the EAST1 parser (`src/toolchain2/parse/py/` or `src/toolchain/misc/east_parts/core.py`), when the left-hand side of an assignment is a Tuple/List wrapped in `()` or `[]`, convert it to `TupleUnpack` in the same way as a bare tuple target.

### Bug 2

In the EAST2 or EAST3 list comprehension expansion path, when the original assignment target is a Tuple, generate index-access assignments from the expanded `__comp_N` to each variable:

```
__comp_1 = [i for i in range(3)]  # comprehension expansion
x = __comp_1[0]                    # tuple unpack expansion
y = __comp_1[1]
z = __comp_1[2]
```

## Fixture

All 8 patterns are placed in `test/fixture/source/py/typing/tuple_unpack_variants.py`. All pass in Python.
