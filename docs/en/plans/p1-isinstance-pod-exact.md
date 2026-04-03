<a href="../../ja/plans/p1-isinstance-pod-exact.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1-ISINSTANCE-POD: POD type isinstance exact match implementation

Last updated: 2026-03-27
Status: Completed

## Background

spec-type_id.md §4.2 specifies that `isinstance` for POD types is an exact type match. However, this is not yet implemented, and the fixture (`test/fixture/source/py/typing/isinstance_pod_exact.py`) has only been placed in advance without generating a golden.

## Target

### Parser / resolve

- `isinstance(x, int16)` and similar — correctly parse and resolve `isinstance` calls with POD type literals as the second argument
- Codify POD type exact match checks as EAST3 instructions

### fixture / golden

- `test/fixture/source/py/typing/isinstance_pod_exact.py` passes through all pipeline stages
- Generate and place golden files (east1/east2/east3/east3-opt/linked)

### emitter

- Each emitter correctly maps the POD isinstance EAST3 instruction to the target language

## Acceptance Criteria

1. `isinstance_pod_exact.py` passes parse → resolve → compile → optimize → link
2. Golden files are generated and incorporated into regression tests
3. C++ emitter + Go emitter: compile + run + stdout match (`py_assert_stdout` passes)
4. The spec-type_id.md §4.2 specification and the implementation agree

## Decision Log

- 2026-03-26: Specified the separation of POD / class type isinstance checks in spec-type_id.md §4.2. Fixture placed in advance.
- 2026-03-27: POD checks such as `isinstance(x, int16)` are organized to be retained in EAST3 as an exact-match lane with `expected_type_id=Name("int16")`. `int` / `float` are normalized to `int64` / `float64` during compile lowering.
- 2026-03-27: The Go emitter renders to exact helpers like `py_is_exact_int16`, and the C++ emitter renders to `py_runtime_value_exact_is<int16>(...)`. Generated golden for fixture `isinstance_pod_exact.py`; confirmed that `pytra-cli.py build ... --target cpp/go --run` returns `True` for both.
