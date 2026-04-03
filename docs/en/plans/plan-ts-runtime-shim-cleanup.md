# Plan: Retire Python built-in shims in the TS/JS runtime (P0-TS-SHIM-CLEANUP)

## Background

A large number of Python built-in name shims are exported from `src/runtime/ts/built_in/py_runtime.ts`:

```typescript
export const int = Number;         // shim for Python int()
export type int = number;
export function match(...) { ... } // shim for Python re.match
```

Generated code imports these via `import { int, match, ... } from "./pytra_built_in_py_runtime"` and calls them using the same names as Python.

## Problems

1. **`int` is not a JavaScript reserved word but it is confusing**: There is no value in aliasing `Number`
2. **`match` is `re.match` functionality**: It should come from `pytra_std_re`, not `pytra_built_in_py_runtime`
3. **The emitter emits Python built-in names as-is**: These should be translated to language-specific names using EAST3's `runtime_call` / `semantic_tag` / `mapping.json`
4. **Import statements become bloated**: Large numbers of names on a single line

## Desired State

| Python | Current TS output | Desired TS output |
|---|---|---|
| `int(x)` | `int(x)` (via shim) | `Math.trunc(Number(x))` or `Number(x)` |
| `str(x)` | `pyStr(x)` (already direct) | Keep as-is |
| `len(x)` | `pyLen(x)` (already direct) | Keep as-is |
| `re.match(p, s)` | `match(p, s)` (via shim) | `pyReMatch(p, s)` or resolved via mapping.json |
| `perf_counter()` | `perf_counter()` (via shim) | Resolved via mapping.json |

The pattern of calling runtime functions directly with a `py` prefix (like `pyStr`, `pyLen`) is correct. The problem is using Python names directly (like `int`, `match`).

## Fix Approach

1. Have the emitter look at EAST3's `runtime_call` / `semantic_tag` and resolve to TS-specific function names via the `calls` table in `mapping.json`
2. Remove the shim exports (`int`, `match`, etc.) from the runtime
3. Add any missing entries to the `calls` table in `mapping.json`

## Target Shims (to be investigated)

Investigate the list of Python built-in names exported from `py_runtime.ts` and classify them as: things to be resolved via `mapping.json` vs. things to keep in the runtime.

## Impact

- Generated code import statements change
- Runtime exports decrease
- TS/JS parity check for fixture + sample + stdlib is required
