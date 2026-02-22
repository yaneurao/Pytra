<a href="../../docs-jp/spec/spec-language-profile.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# LanguageProfile Specification (CodeEmitter)

This document defines the language-profile JSON specification used by `CodeEmitter`.

## 1. Purpose

- Separate language-specific differences (types, operators, runtime calls, syntax templates) from Python code.
- Thin transpiler entry implementations such as `py2cpp.py` and increase shared components.
- Handle only exceptional conversions in `hooks`, and process normal cases via JSON configuration.

## 2. Placement

- `src/profiles/`
  - `common/core.json`: shared defaults for all languages
  - `cpp/profile.json`: integrated profile for C++ (entry)
  - `cpp/types.json`: type map
  - `cpp/operators.json`: operator map
  - `cpp/runtime_calls.json`: built-in / `module.attr` call map
  - `cpp/syntax.json`: statement templates

## 3. Load Order

1. `common/core.json`
2. `include` order in `<lang>/profile.json`
3. body of `<lang>/profile.json`
4. CLI overrides (if needed)

Last-write-wins merge is the default rule.

## 4. Schema (v1)

Minimal `profile.json` example:

```json
{
  "schema_version": 1,
  "language": "cpp",
  "include": [
    "types.json",
    "operators.json",
    "runtime_calls.json",
    "syntax.json"
  ],
  "hooks": {
    "module": "hooks.cpp.hooks.cpp_hooks",
    "factory": "build_cpp_hooks"
  }
}
```

### 4.1 `types`

EAST type name -> output language type name.

```json
{
  "types": {
    "int64": "int64",
    "float64": "float64",
    "str": "str",
    "bytes": "bytes",
    "bytearray": "bytearray"
  },
  "generic_types": {
    "list": "list<{T}>",
    "dict": "dict<{K}, {V}>",
    "set": "set<{T}>",
    "tuple": "std::tuple<{...}>",
    "optional": "std::optional<{T}>"
  }
}
```

### 4.2 `operators`

EAST operator -> output token.

```json
{
  "operators": {
    "bin": { "Add": "+", "Sub": "-", "Div": "/" },
    "cmp": { "Eq": "==", "NotEq": "!=", "Lt": "<" },
    "aug": { "Add": "+=", "Sub": "-=" }
  }
}
```

### 4.3 `runtime_calls`

- `builtin_call`: `len`, `print`, etc.
- `module_attr_call`: calls in `module.attr` form
- `method_call`: `list.append`, etc.

```json
{
  "runtime_calls": {
    "builtin_call": {
      "len": "py_len",
      "print": "py_print"
    },
    "module_attr_call": {
      "pytra.std.sys": {
        "write_stdout": "pytra::std::sys::write_stdout"
      }
    },
    "method_call": {
      "list.append": "list.append",
      "dict.get": "dict.get"
    }
  }
}
```

### 4.4 `syntax`

Statement templates and syntax switches.

```json
{
  "syntax": {
    "if": "if ({cond}) {",
    "else": "} else {",
    "while": "while ({cond}) {",
    "function_decl": "{ret} {name}({args}) {",
    "class_decl": "struct {name} : public PyObj {"
  }
}
```

### 4.5 `syntax.identifiers`

Reserved-word avoidance, prefixes, and identifier rules.

```json
{
  "syntax": {
    "identifiers": {
      "reserved_words": ["class", "template"],
      "rename_prefix": "__py_"
    }
  }
}
```

### 4.6 `hooks`

Move only branches hard to express in profiles into hooks.

```json
{
  "hooks": {
    "module": "hooks.cpp.hooks.cpp_hooks",
    "factory": "build_cpp_hooks"
  }
}
```

Place `module` under language-specific side (e.g., `src/hooks/cpp/hooks/`), not under `src/common/`.

## 5. Hooks Specification

`profile.hooks` handles only branches that are hard to express in JSON.

Selfhost constraints:
- hooks API mainly uses `dict[str, Any]` / `list[str]` / `str` / `bool`, and does not depend on `callable` type annotations.
- `CodeEmitter` handles hooks by “fetching from dict and calling,” avoiding selfhost conversion stalls derived from type annotations.

- `on_emit_stmt(emitter, stmt)`:
  - If it returns `True`, skip default statement emission.
- `on_render_call(emitter, call_node, func_node, rendered_args, rendered_kwargs)`
- `on_render_binop(emitter, binop_node, left, right)`

Return values:
- `None`: continue default logic
- `str`: adopt that string as output

### 5.1 Implementation Location (C++)

```text
src/hooks/cpp/hooks/cpp_hooks.py
```

## 6. Validation Rules

- `schema_version` is required (current: `1`).
- `language` is required.
- `include` allows relative paths only.
- Unknown keys are warnings (not errors).
- Missing required keys cause startup errors.

## 7. Migration Policy

1. Migrate C++ first.
2. Remove hardcoded maps in `py2cpp.py` in stages.
3. Rename `BaseEmitter` to `CodeEmitter` while keeping compatibility with `BaseEmitter = CodeEmitter`.

