<a href="../../../ja/language/cpp/spec-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# py2cpp Support Matrix (Test-Aligned)

Last updated: 2026-02-21

This document summarizes language-feature support status in `src/py2cpp.py` at a granularity verifiable through both implementation code and runtime tests.

## Status Definitions

- `supported`: supported in current implementation, with green corresponding tests.
- `partial`: supported with conditions/limitations.
- `unsupported`: unsupported in current implementation; explicitly errored.
- `not_yet_verified`: described in spec docs, but not confirmed in this table due to insufficient dedicated regression tests.

## Core Syntax and Expressions

| Feature | Status | Current State | Evidence |
|---|---|---|---|
| `enumerate(xs)` | supported | Supported. | `src/py2cpp.py:3304`, `test/unit/test_py2cpp_features.py:1441`, `test/fixtures/strings/enumerate_basic.py:7` |
| `enumerate(xs, 1)` / `enumerate(xs, start)` | supported | Supported with second argument. `start` is converted to `int64`. | `src/py2cpp.py:3306`, `test/fixtures/strings/enumerate_basic.py:17`, `test/fixtures/strings/enumerate_basic.py:21`, `test/unit/test_py2cpp_features.py:1441` |
| Basic `lambda` (0/1/multi args) | supported | Supported. | `src/py2cpp.py:4296`, `test/unit/test_py2cpp_features.py:1259`, `test/fixtures/core/lambda_basic.py:8` |
| Outer-variable capture in `lambda` | supported | Supported (`[&]` capture). | `src/py2cpp.py:4303`, `test/unit/test_py2cpp_features.py:1337`, `test/fixtures/core/lambda_capture_multiargs.py:7` |
| Passing `lambda` as argument | supported | Supported. | `test/unit/test_py2cpp_features.py:1349`, `test/fixtures/core/lambda_as_arg.py:10` |
| Immediate `lambda` call | supported | Supported. | `test/unit/test_py2cpp_features.py:1355`, `test/fixtures/core/lambda_immediate.py:5` |
| Ternary inside `lambda` | supported | Supported. | `test/unit/test_py2cpp_features.py:1331`, `test/fixtures/core/lambda_ifexp.py:6` |
| `x if cond else y` (IfExp) | supported | Supported. | `src/py2cpp.py:3911`, `test/unit/test_py2cpp_features.py:964` |
| `list` comprehension | partial | Supported, but assumes a single generator. | `src/py2cpp.py:4304`, `src/py2cpp.py:4306`, `test/unit/test_py2cpp_features.py:1253`, `test/unit/test_py2cpp_features.py:1325` |
| `set` comprehension | partial | Supported, but assumes a single generator. | `src/py2cpp.py:4381`, `src/py2cpp.py:4383`, `test/unit/test_py2cpp_features.py:1307`, `test/fixtures/collections/comprehension_dict_set.py:6` |
| `dict` comprehension | partial | Supported, but assumes a single generator. | `src/py2cpp.py:4436`, `src/py2cpp.py:4438`, `test/unit/test_py2cpp_features.py:1307`, `test/fixtures/collections/comprehension_dict_set.py:7` |
| `if` condition in comprehension | supported | Supported. | `test/unit/test_py2cpp_features.py:1253`, `test/unit/test_py2cpp_features.py:1301`, `test/fixtures/collections/comprehension_filter.py:7` |
| `range(start, stop, step)` in comprehension | supported | Supported. | `test/unit/test_py2cpp_features.py:1325`, `test/fixtures/collections/comprehension_range_step.py:6` |
| Nested comprehension (comprehension inside comprehension) | supported | Supported. | `test/unit/test_py2cpp_features.py:1295`, `test/fixtures/collections/comprehension_nested.py:6` |
| `str` slice | supported | Supported. | `test/unit/test_py2cpp_features.py:1435`, `test/fixtures/strings/str_slice.py:1` |
| for-each over string | supported | Supported. | `test/unit/test_py2cpp_features.py:1429`, `test/fixtures/strings/str_for_each.py:1` |
| Basic `bytes` / `bytearray` operations | supported | Supported. | `test/unit/test_py2cpp_features.py:1241`, `test/unit/test_py2cpp_features.py:1247`, `test/fixtures/typing/bytes_basic.py:1`, `test/fixtures/typing/bytearray_basic.py:1` |

## import / Module Resolution

| Feature | Status | Current State | Evidence |
|---|---|---|---|
| `import M` | supported | Supported. | `test/unit/test_py2cpp_features.py:1385`, `test/fixtures/imports/import_math_module.py:3` |
| `import M as A` | supported | Supported. | `test/unit/test_py2cpp_features.py:259`, `test/fixtures/imports/import_pytra_runtime_png.py:3` |
| `from M import S` | supported | Supported. | `test/unit/test_py2cpp_features.py:242`, `test/unit/test_py2cpp_features.py:1283`, `test/fixtures/imports/from_import_symbols.py:3` |
| `from M import S as A` | supported | Supported. | `test/unit/test_py2cpp_features.py:1283`, `test/fixtures/imports/from_import_symbols.py:3` |
| Circular import detection | unsupported | Detects and stops with `input_invalid(kind=import_cycle)`. | `src/py2cpp.py:5734`, `test/unit/test_py2cpp_features.py:567` |
| Relative import (`from .m import x`) | unsupported | `input_invalid(kind=unsupported_import_form)`. | `src/py2cpp.py:4693`, `test/unit/test_py2cpp_features.py:596` |
| `from M import *` | unsupported | `input_invalid(kind=unsupported_import_form)`. | `src/py2cpp.py:4686`, `test/unit/test_py2cpp_features.py:618` |
| Unresolved module import | unsupported | `input_invalid(kind=missing_module)`. | `test/unit/test_py2cpp_features.py:544` |
| Duplicate import binding | unsupported | `input_invalid(kind=duplicate_binding)`. | `test/unit/test_py2cpp_features.py:645`, `test/unit/test_py2cpp_features.py:675` |
| Referencing `M.T` after `from M import S` | unsupported | Treated as `input_invalid(kind=missing_symbol)`. | `test/unit/test_py2cpp_features.py:732` |

## OOP / Types / Runtime

| Feature | Status | Current State | Evidence |
|---|---|---|---|
| `super().__init__()` | supported | Supported. | `test/unit/test_py2cpp_features.py:1379`, `test/fixtures/oop/super_init.py:1` |
| `@dataclass` | supported | Supported. | `test/unit/test_py2cpp_features.py:1519`, `test/fixtures/stdlib/dataclasses_extended.py:1` |
| `Enum` / `IntEnum` / `IntFlag` | supported | Supported. | `test/unit/test_py2cpp_features.py:1453`, `test/unit/test_py2cpp_features.py:1459`, `test/unit/test_py2cpp_features.py:1465` |
| `Any` family (basic) | supported | Supported (regression-checked for `Any`/`None`/mixed list-dict cases). | `test/unit/test_py2cpp_features.py:1265`, `test/unit/test_py2cpp_features.py:1271`, `test/unit/test_py2cpp_features.py:1277`, `test/unit/test_py2cpp_features.py:1289` |
| Attribute/method call on `object` receiver | unsupported | Rejected by emit guard. | `test/unit/test_py2cpp_features.py:1531` |

## Constraints From CLI Options

| Feature | Status | Current State | Evidence |
|---|---|---|---|
| `--str-index-mode=codepoint` | unsupported | Explicit error at present. | `src/pytra/compiler/transpile_cli.py:152`, `test/unit/test_py2cpp_features.py:1183` |
| `--str-slice-mode=codepoint` | unsupported | Explicit error at present. | `src/pytra/compiler/transpile_cli.py:154`, `src/py2cpp.py:6419` |
| `--int-width=bigint` | unsupported | Explicit error in transpilation; only planning-value display is allowed in `--dump-options`. | `src/pytra/compiler/transpile_cli.py:144`, `test/unit/test_py2cpp_features.py:1167`, `src/py2cpp.py:6417` |

## Undetermined (Do Not Overstate In This Table)

The following still lack sufficient dedicated regression coverage, so they are treated as `not_yet_verified`:

- Detailed compatibility scope for function default arguments, `*args`, and `**kwargs`
- Behavior of `yield` / generator expressions
- Fine-grained exception hierarchy compatibility (e.g., type patterns in multiple except clauses)

## Update Rules

- When updating this table, always add runtime-test evidence (`test/unit/...`) for each corresponding row.
- Do not mark anything as `supported` if implementation appears to work but no test evidence exists.
