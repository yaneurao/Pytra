<a href="../../ja/plans/p4-int32-default.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P20-INT32: Change the default int size from int64 to int32

Last updated: 2026-03-30
Status: On hold (demoted from P4 to P20. Deprioritized due to wide impact. Temporarily moved out of TODO. Return to infra.md when resuming.)

## Background

Currently, Pytra maps Python's `int` to `int64` during EAST2 type normalization. However, the `int` type in major target languages (C++, Go, Java, C#, Kotlin) is 32-bit, which is sufficient for typical use. 64-bit is less efficient in terms of memory and cache, introducing unnecessary overhead.

Change `int` → `int32`, and require users to explicitly write `int64` when 64-bit is needed.

## Design decisions

### Rationale for `int` → `int32`

- The `int` type in C++/Go/Java/C#/Kotlin is 32-bit (language standard)
- The maximum value of `int32` is approximately 2.1 billion (2,147,483,647), which is sufficient for typical loop counters, array indices, and arithmetic
- Java/C# have operated with int32 for many years, demonstrating no practical problems
- 64-bit integers are at a disadvantage in memory bandwidth and cache line usage (especially when stored in large numbers as container elements)

### Return type of `len()`: `int32`

- Most target languages return signed int32 from `len`/`size`/`count` (Java, C#, Kotlin)
- C++'s `size_t` (uint64) is widely recognized as a design mistake (which led to the addition of `std::ssize()` in C++20); we do not follow it
- Using unsigned leads to real problems: underflow with `len(x) - 1`, cast noise in mixed signed/unsigned arithmetic, etc.
- Arrays with more than 2.1 billion elements are not normally expected

### When 64-bit is needed

The user explicitly writes `int64`. This is the same operational model as other languages (Java's `long`, C#'s `long`, Go's `int64`).

## Impact

### Specification

- `spec-east.md` §6.2: Change `int` normalization target from `int64` → `int32`
- `spec-east2.md` §2.2: Same
- `spec-east1.md`: No impact (EAST1 does not perform type normalization)

### Implementation

- `src/toolchain/compile/east2.py` (or resolve-related): Change type normalization rules
- Integer literal type in `Constant`: `int64` → `int32`
- Return type of `len()`: `int64` → `int32`
- Propagation to `range()` argument and loop variable types
- Cast insertion rules: consider whether promotion rules between `int32` ↔ `int64` need to be added

### Testing / Verification

- Regenerate all golden files (fixture + sample + selfhost)
- Fix type mappings in all emitters (mapping.json, etc.)
- Overflow check for all 18 samples: carefully examine whether intermediate calculations exceed 32-bit, and explicitly fix any such locations to use `int64`
- Parity tests pass for all languages

## Risks

- Some samples (e.g., Mandelbrot set) may have intermediate calculations that exceed int32 → to be examined in S3
- A promotion rule design is needed for when `int32 * int32` results exceed int32
- Check impact on existing user code (e.g., under `materials/`)

## Prerequisites

Start after Go selfhost (P2-SELFHOST) is complete.

## Subtasks

1. [ID: P20-INT32-S1] Change `int` → `int32` normalization rule in spec-east.md / spec-east2.md
2. [ID: P20-INT32-S2] Fix type normalization in resolve
3. [ID: P20-INT32-S3] Overflow check for all 18 samples + explicitly change any affected locations to `int64`
4. [ID: P20-INT32-S4] Regenerate goldens + verify parity for all emitters

## Acceptance Criteria

1. `int` is normalized to `int32` (spec + implementation match)
2. Return type of `len()` is `int32`
3. All language parity passes for all fixtures + all 18 samples (emit + compile + run + stdout match)
4. No overflow occurs in samples (affected locations explicitly changed to `int64`)
5. selfhost goldens have been regenerated

## Warning for out-of-range integer literal assignment

This is a problem that should be addressed independently of P20. It occurs under the current spec as well.

Current behavior: when an integer literal does not fit within the declared type's range, such as `x: int32 = 10000000000`, resolve silently inserts a `static_cast`, causing truncation in C++.

Approach:
- At the resolve stage, compare integer literals against the declared type's range, and emit a **warning** (not an error) if the literal does not fit
- All integer types are covered: `int8`/`uint8`/`int16`/`uint16`/`int32`/`uint32`/`int64`/`uint64`
- Example: `x: int8 = 256` → warning: literal 256 overflows int8 (max 127)
- Example: `x: int32 = 10000000000` → warning: literal 10000000000 overflows int32 (max 2147483647)
- A test for this case is needed in a fixture (add to `test/fixture/source/py/typing/`)

## Warning for signed negative value assigned to unsigned type

This is a problem that should be addressed independently of P20. It occurs under the current spec as well.

Current behavior: when a signed negative value is assigned to an unsigned type, such as `x: int8 = -1; y: uint16 = x`, the result differs between languages (C++: wraparound to 65535, Python: remains -1). Resolve passes this silently.

Approach:
- At the resolve stage, emit a **warning** (not an error) when a signed-type variable is assigned to an unsigned type and the original value may be negative
- Literal assignment (`y: uint16 = -1`) can be detected statically. Variable assignment (`y: uint16 = x` where `x: int8`) can be detected from the type combination
- Since results differ between languages in parity checks, do not include a direct signed-negative-to-unsigned assignment pattern in fixtures

## Decision Log

- 2026-03-26: Discussed return type of `len()`. Confirmed the approach of using `int32` (signed) rather than following C++'s `size_t` (uint64). Reason: unsigned has the underflow trap, and the majority of target languages (Java/C#/Kotlin/Go/Swift) use signed.
- 2026-03-30: Confirmed that `x: int32 = 10000000000` silently truncates. Decided to emit a warning for out-of-range integer literal assignment at the resolve stage (a warning, not an error). Can be addressed independently of P20.
