<a href="../../../ja/plans/archive/20260306-p0-runtime-symbol-index-data-driven.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Make the Runtime Symbol Index Data-Driven

Last updated: 2026-03-06

Related TODO:
- `docs/ja/todo/index.md` `ID: P0-RUNTIME-SYMBOL-INDEX-01`

Summary:
- Consolidate runtime-symbol ownership and companion rules into a SoT-generated JSON index.
- Keep only target-independent runtime metadata in IR.
- Make backends derive target-specific headers/sources from the index instead of guessing module ownership.

Why this was needed:
- EAST3 and backend code still had places where runtime ownership was inferred from bare runtime-call strings such as `py_enumerate`, `py_any`, `py_strip`, or `dict.get`.
- Import-to-runtime resolution rules were scattered across `signature_registry.py`, IR construction, and backend emitters.
- That design was brittle and easy to regress.

Rules fixed by this plan:
1. Do not hardcode runtime-symbol-to-module/file mapping in Python code.
2. Do not introduce handwritten JSON as a new source of truth; JSON must be generated from SoT.
3. IR only stores target-independent runtime data.
4. IR must not contain target file paths such as `runtime/cpp/std/math.gen.h`.
5. Backends derive target artifacts from `runtime_module_id + runtime_symbol`.

Target direction:

```json
{
  "runtime_module_id": "pytra.built_in.iter_ops",
  "runtime_symbol": "py_enumerate",
  "runtime_dispatch": "function"
}
```

and a generated index such as:

```json
{
  "schema_version": 1,
  "modules": {
    "pytra.built_in.iter_ops": {
      "exports": {
        "py_enumerate_object": {
          "kind": "function",
          "companions": ["gen", "ext"]
        }
      }
    }
  }
}
```

Phases:
- inventory current hardcoded runtime-symbol knowledge
- define the generated schema
- implement the generator from SoT/runtime layout
- switch IR/runtime binding metadata to canonical module/symbol forms
- migrate representative backends to use the index
- add tooling/guard coverage and close the plan

Acceptance:
- runtime-symbol ownership is generated from SoT
- IR stores canonical module/symbol identity instead of target paths
- representative backends resolve runtime calls from the generated index
- guardrails catch reintroduction of handwritten runtime-symbol guesses

Decision log:
- 2026-03-06: the correct ownership boundary is “IR keeps target-independent module/symbol identity; backends derive target artifacts from a generated index.”
- 2026-03-06: handwritten JSON was rejected; the index had to be generated from `src/pytra/*` and runtime layout information.
