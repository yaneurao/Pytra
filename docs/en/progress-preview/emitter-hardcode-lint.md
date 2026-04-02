<a href="../../ja/progress-preview/emitter-hardcode-lint.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Emitter hardcode violation matrix

> Machine-generated file. Run `python3 tools/check/check_emitter_hardcode_lint.py` to update.
> Generated at: 2026-04-02T13:46:19
> [Links](./index.md)

Matrix of grep-detected violations where the emitter hardcodes module names, runtime symbols, or class names instead of using EAST3 data.
Fewer violations means the emitter is more faithfully following the EAST3 source of truth.

| Icon | Meaning |
|---|---|
| 🟩 | No violations |
| 🟥 | Violations found (see details below) |
| ⬜ | Not implemented (no emitter in toolchain2) |

> **js** shares the **ts** emitter and has no separate implementation; the js column mirrors ts results.

| Category | cpp | rs | cs | ps1 | js | ts | dart | go | java | scala | kotlin | swift | ruby | lua | php | nim | julia | zig |
|--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| module name | 🟩 | 🟥 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | ⬜ | 🟩 | 🟩 | 🟩 | 🟩 | ⬜ | ⬜ |
| runtime symbol | 🟩 | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | ⬜ | 🟩 | 🟩 | 🟩 | 🟩 | ⬜ | ⬜ |
| target const | 🟩 | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | ⬜ | 🟩 | 🟩 | 🟩 | 🟩 | ⬜ | ⬜ |
| prefix match | 🟩 | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | ⬜ | 🟩 | 🟩 | 🟩 | 🟩 | ⬜ | ⬜ |
| class name | 🟩 | 🟥 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | ⬜ | 🟩 | 🟩 | 🟩 | 🟥 | ⬜ | ⬜ |
| Python syntax | 🟩 | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | ⬜ | 🟩 | 🟩 | 🟩 | 🟥 | ⬜ | ⬜ |
| type_id | 🟩 | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | ⬜ | ⬜ | 🟩 | 🟩 | 🟩 | 🟩 | ⬜ | ⬜ |
| skip pure py | 🟩 | 🟩 | 🟩 | ⬜ | 🟩 | 🟩 | ⬜ | 🟥 | 🟩 | ⬜ | ⬜ | ⬜ | 🟩 | 🟩 | 🟩 | 🟥 | ⬜ | ⬜ |
| **🟩 PASS** | 8 | 6 | 8 | — | 8 | 8 | — | 7 | 8 | — | — | — | 8 | 8 | 8 | 5 | — | — |
| **🟥 FAIL** | — | 2 | — | — | — | — | — | 1 | — | — | — | — | — | — | — | 3 | — | — |
| **⬜ Not impl.** | — | — | — | 8 | — | — | 8 | — | — | 8 | 8 | 8 | — | — | — | — | 8 | 8 |

## Details

### class_name / nim (1)

```
src/toolchain2/emit/nim/emitter.py:154: "Exception", "BaseException", "RuntimeError", "ValueError",
```

### class_name / rs (1)

```
src/toolchain2/emit/rs/emitter.py:1433: is_path_ref = inner_rs in ("Path", "PyPath", "pathlib.Path", "pytra.std.pathlib.Path") or inner_rs.endswith(".Path")
```

### module_name / rs (5)

```
src/toolchain2/emit/rs/emitter.py:1394: if module_id == "os" and attr == "environ":
src/toolchain2/emit/rs/emitter.py:1992: if mod_name == "os":
src/toolchain2/emit/rs/emitter.py:1994: if mod_name == "subprocess":
src/toolchain2/emit/rs/emitter.py:2775: if method == "glob" and len(rendered_args) == 1:
src/toolchain2/emit/rs/emitter.py:3899: if mod_name in ("os", "subprocess"):
```

### python_syntax / nim (1)

```
src/toolchain2/emit/nim/emitter.py:891: if attr == "__init__" and isinstance(owner_node, dict) and _str(owner_node, "repr") == "super()":
```

### skip_pure_python / go (2)

```
src/runtime/go/mapping.json:0: skip_modules contains "pytra.std.pathlib" but pytra.std.pathlib is pure Python (no @extern)
src/runtime/go/mapping.json:0: skip_modules contains "pytra.std.random" but pytra.std.random is pure Python (no @extern)
```

### skip_pure_python / nim (1)

```
src/runtime/nim/mapping.json:0: skip_modules contains "pytra.std.random" but pytra.std.random is pure Python (no @extern)
```
