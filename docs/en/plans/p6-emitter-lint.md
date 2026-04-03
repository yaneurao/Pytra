<a href="../../ja/plans/p6-emitter-lint.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P6-EMITTER-LINT: New emitter responsibility violation checker

Last updated: 2026-03-30
Status: Complete

## Background

An emitter should generate code using only information from EAST3 (spec-emitter-guide §1), but historically there are places where module names and runtime function names are hardcoded. The C++ emitter in toolchain1 had a lot of technical debt, but since toolchain2 is a complete rewrite of the C++ emitter, no such debt exists there.

These responsibility violations cannot be detected by parity checks (hardcoded values still work correctly as long as they are the right names). A checker is needed that greps the emitter source code itself to detect violations.

## Detection targets (6 categories)

### 1. Hardcoded module names

The emitter knows module names as string literals instead of using `runtime_module_id`.

Prohibited pattern examples: `"math"`, `"pathlib"`, `"json"`, `"sys"`, `"os"`, `"glob"`, `"time"`, `"subprocess"`, `"re"`, `"argparse"`

### 2. Hardcoded runtime function names

The emitter directly knows function names instead of using `runtime_call` / `runtime_symbol`.

Prohibited pattern examples: `"perf_counter"`, `"py_len"`, `"py_print"`, `"py_range"`, `"write_rgb_png"`, `"save_gif"`, `"grayscale_palette"`

### 3. Hardcoded target language constants/function names

The emitter is taking over the responsibility of the `calls` table in mapping.json.

Prohibited pattern examples: `"M_PI"`, `"M_E"`, `"std::sqrt"`, `"std::stoll"`, `"math.Sqrt"`, `"Math.PI"`

### 4. Runtime prefix matching

Branching on module ID prefix where `runtime_call_adapter_kind` should be used instead.

Prohibited pattern examples: `"pytra.std."`, `"pytra.core."`, `"pytra.built_in."`

### 5. Hardcoded class names

The emitter branches on class names where the judgment should come from EAST3 type information.

Prohibited pattern examples: `"Path"`, `"ArgumentParser"`, `"Exception"`

### 6. Residual Python syntax

Python syntax that should already be normalized in EAST3 remaining in the emitter.

Prohibited pattern examples: `"__main__"`, `"super()"`

### 7. Hardcoded type_id / isinstance logic

The emitter maintains type-judgment logic on its own instead of delegating to `pytra_isinstance`.

Prohibited pattern examples: `"py_runtime_object_isinstance"`, `"PYTRA_TID_"`, `"py_tid_"`, `"g_type_table"`

## Design

### Grep-based static inspection

Target: `.py` files under `src/toolchain2/emit/*/`. Grep for prohibited pattern strings.

- Focus on categories with high detection accuracy (1–4, parts of 5, 6, 7)
- Among categories 4–7, type-name string matching and branching on attribute names produce many false positives, so they are candidates for future migration to AST-based lint

### Allowlist

~~C++ emitter allowlist~~ — **Not needed**: since toolchain2's C++ emitter is a rewrite, there are no existing violations, and no allowlist will be created. The checker records all violations in a violation matrix (does not affect exit code).

### Output format

Outputs a language × category matrix to stdout:

```
| Category | cpp | go | rs | ts |
|---|---|---|---|---|
| module name | 🟥3 | 🟩0 | 🟩0 | 🟩0 |
| runtime symbol | 🟥5 | 🟥1 | 🟩0 | 🟩0 |
| target constant | 🟥2 | 🟩0 | 🟩0 | 🟩0 |
| prefix match | 🟥1 | 🟩0 | 🟩0 | 🟩0 |
| class name | 🟥2 | 🟩0 | 🟩0 | 🟩0 |
| Python syntax | 🟩0 | 🟩0 | 🟩0 | 🟩0 |
```

This output can be incorporated as part of the progress page.

### Relationship to existing checkers

| Existing checker | Coverage | Relationship to this checker |
|---|---|---|
| `check_emitter_runtimecall_guardrails.py` | Direct runtime call name usage (non-C++ only) | Overlaps with category 2, but this checker targets all languages |
| `check_emitter_forbidden_runtime_symbols.py` | Implementation symbols such as `__pytra_*` | Overlaps with part of category 2 |

In the future, these can be consolidated into this checker and the existing two scripts can be retired.

## Decision Log

- 2026-03-30: Decided on a grep-based approach to detect 6 categories of responsibility violations. Type-name string matching (e.g., `resolved_type == "list"`) and attribute-name branching (e.g., `attr == "append"`) produce too many false positives and are excluded from grep-based detection. They are candidates for future migration to AST-based lint.
- 2026-03-30: Decided against integrating into `run_local_ci.py`. Also decided against integrating into `runtime_parity_check.py` (would make parity checks too slow). Changed to a standalone, manually-run script approach. Timing of execution to be determined separately.
