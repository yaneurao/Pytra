<a href="../../ja/plans/p1-parser-stdlib-json.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1-PARSER-STDLIB-JSON: Parser support for pytra.std.json + golden regeneration

Last updated: 2026-03-27
Status: Not started

## Background

`src/pytra/std/json.py` is the canonical stdlib source, but the current source fails to parse. As a result, the golden (EAST1/EAST2/EAST3/EAST3-opt/linked) cannot be regenerated, and a stale stored EAST3 continues to be used. In Go selfhost (P2-SELFHOST-S4), type corruption caused by the stale EAST3 (remaining `str` coercion, insufficient optional narrowing, broken types from cast) is a Go build blocker.

The same problem can occur in other `pytra.std.*` files, so fixing the parser is relevant to the health of the entire pipeline, not just selfhost.

## Causes of parse failure

Syntax in `src/pytra/std/json.py` that the parser cannot handle:

1. **Recursive type alias (PEP 695 form)**:
   ```python
   type JsonVal = None | bool | int | float | str | list[JsonVal] | dict[str, JsonVal]
   ```
   - Parser support for the `type X = ...` syntax (PEP 695)
   - Forward reference resolution for `JsonVal` appearing recursively in the right-hand side union

2. **Forward reference to a class defined later**:
   ```python
   def get(self, key: str) -> JsonValue | None:  # JsonValue is defined later
   ```

These are already noted in P2-SELFHOST-S1 remarks as "unsupported parser syntax" (ParseContext recursion, Union forward ref).

## Scope of impact

- `pytra.std.json` golden becomes regeneratable
- Go selfhost json lane blocker is resolved
- Other `pytra.std.*` files using the same syntax will also pass

## Subtasks

1. [ID: P1-PARSER-JSON-S1] Enable the parser to handle `type X = ...` (PEP 695 type alias) syntax
2. [ID: P1-PARSER-JSON-S2] Enable resolution of recursive forward references in unions (`JsonVal` itself inside `list[JsonVal]`)
3. [ID: P1-PARSER-JSON-S3] Confirm that `pytra.std.json.py` passes parse → resolve → compile → optimize → link
4. [ID: P1-PARSER-JSON-S4] Regenerate golden + confirm existing parity is maintained

## Acceptance Criteria

1. `pytra-cli2 -parse src/pytra/std/json.py` succeeds
2. All stages (parse → resolve → compile → optimize → link) pass
3. golden is regenerated from the current source
4. Existing fixture / sample parity is maintained

## Decision Log

- 2026-03-27: Identified the root cause of the Go selfhost json lane blocker as "pytra.std.json.py cannot be parsed → stale golden → emitter generates from outdated information". Decided to fix the parser and regenerate golden rather than absorbing the stale EAST3 in the emitter.
