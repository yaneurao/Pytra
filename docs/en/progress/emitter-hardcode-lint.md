<a href="../../ja/progress/emitter-hardcode-lint.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Emitter hardcode violation matrix

> Machine-generated file. Run `python3 tools/check/check_emitter_hardcode_lint.py` to update.
> Generated at: 2026-03-30T07:24:17
> [Links](./index.md)

Matrix of grep-detected violations where the emitter hardcodes module names, runtime symbols, or class names instead of using EAST3 data.
Fewer violations means the emitter is more faithfully following the EAST3 source of truth.

| Icon | Meaning |
|---|---|
| 🟩 | No violations |
| 🟥 | Violations found (see details below) |
| ⬜ | Not implemented (no emitter in toolchain2) |

| Category | cpp | rs | cs | ps1 | js | ts | dart | go | java | swift | kotlin | ruby | lua | scala | php | nim | julia | zig |
|--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| module name | 🟩 | 🟥 | ⬜ | ⬜ | ⬜ | 🟥 | ⬜ | 🟥 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| runtime symbol | 🟥 | 🟥 | ⬜ | ⬜ | ⬜ | 🟥 | ⬜ | 🟥 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| target const | 🟩 | 🟩 | ⬜ | ⬜ | ⬜ | 🟩 | ⬜ | 🟩 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| prefix match | 🟩 | 🟩 | ⬜ | ⬜ | ⬜ | 🟩 | ⬜ | 🟩 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| class name | 🟥 | 🟩 | ⬜ | ⬜ | ⬜ | 🟥 | ⬜ | 🟥 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Python syntax | 🟩 | 🟩 | ⬜ | ⬜ | ⬜ | 🟩 | ⬜ | 🟩 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

## Details

### class_name / cpp (3)

```
src/toolchain2/emit/cpp/emitter.py:72: "BaseException", "Exception", "ValueError", "TypeError", "IndexError",
src/toolchain2/emit/cpp/emitter.py:1288: if attr == "add_argument" and owner_type == "ArgumentParser":
src/toolchain2/emit/cpp/emitter.py:2661: if bn in ("BaseException", "Exception", "RuntimeError", "ValueError", "TypeError", "IndexError", "KeyError") or rc == "s
```

### class_name / go (19)

```
src/toolchain2/emit/go/emitter.py:102: "ArgumentParser",
src/toolchain2/emit/go/emitter.py:653: "Exception": (10, 15),
src/toolchain2/emit/go/emitter.py:702: "Exception",
src/toolchain2/emit/go/emitter.py:1281: if op == "Div" and left_rt == "Path" and right_rt == "str":
src/toolchain2/emit/go/emitter.py:2252: if fn_name in ("BaseException", "Exception", "RuntimeError", "ValueError", "TypeError", "IndexError", "KeyError"):
src/toolchain2/emit/go/emitter.py:2718: if bn in ("BaseException", "Exception", "RuntimeError", "ValueError", "TypeError", "IndexError", "KeyError"):
src/toolchain2/emit/go/emitter.py:3965: if ctx.current_return_type == "Exception":
src/toolchain2/emit/go/emitter.py:4006: if ctx.current_return_type == "Exception":
src/toolchain2/emit/go/emitter.py:4026: if return_type == "Exception":
src/toolchain2/emit/go/emitter.py:4361: if return_type == "Exception":
src/toolchain2/emit/go/emitter.py:4624: elif base != "" and base not in ("object", "Exception", "BaseException"):
src/toolchain2/emit/go/emitter.py:5128: if ctx.current_return_type == "Exception":
src/toolchain2/emit/go/emitter.py:5157: if ctx.current_return_type == "Exception":
src/toolchain2/emit/go/emitter.py:5248: elif ctx.current_return_type == "Exception":
src/toolchain2/emit/go/emitter.py:5370: if ctx.current_return_type == "Exception":
src/toolchain2/emit/go/emitter.py:5377: if ctx.current_return_type == "Exception":
src/toolchain2/emit/go/emitter.py:5439: elif ctx.current_return_type == "Exception":
src/toolchain2/emit/go/emitter.py:5442: if ctx.current_return_type == "Exception":
src/toolchain2/emit/go/emitter.py:5457: if bn in ("BaseException", "Exception", "RuntimeError", "ValueError", "TypeError", "IndexError", "KeyError") or rc == "s
```

### class_name / ts (4)

```
src/toolchain2/emit/ts/emitter.py:111: "Path", "PyPath", "py_math_tau", "py_env_target",
src/toolchain2/emit/ts/emitter.py:116: "ArgumentParser",
src/toolchain2/emit/ts/emitter.py:224: "Exception", "BaseException", "RuntimeError", "ValueError",
src/toolchain2/emit/ts/emitter.py:1576: "Exception": "Error",
```

### module_name / go (6)

```
src/toolchain2/emit/go/emitter.py:1169: ctx.imports_needed.add("math")
src/toolchain2/emit/go/emitter.py:1172: ctx.imports_needed.add("math")
src/toolchain2/emit/go/emitter.py:1324: ctx.imports_needed.add("math")
src/toolchain2/emit/go/emitter.py:4883: ctx.imports_needed.add("os")
src/toolchain2/emit/go/emitter.py:4889: ctx.imports_needed.add("os")
src/toolchain2/emit/go/emitter.py:4904: ctx.imports_needed.add("os")
```

### module_name / rs (2)

```
src/toolchain2/emit/rs/emitter.py:3317: "math": "math_native.rs",
src/toolchain2/emit/rs/emitter.py:3318: "time": "time_native.rs",
```

### module_name / ts (1)

```
src/toolchain2/emit/ts/emitter.py:122: "sys", "pyset_argv", "pyset_path",
```

### runtime_symbol / cpp (1)

```
src/toolchain2/emit/cpp/emitter.py:1487: if rc in ("py_print", "py_len") and len(arg_strs) >= 1:
```

### runtime_symbol / go (2)

```
src/toolchain2/emit/go/emitter.py:2383: if dispatch == "py_print" or bn == "print":
src/toolchain2/emit/go/emitter.py:2387: if dispatch == "py_len" or bn == "len":
```

### runtime_symbol / rs (3)

```
src/toolchain2/emit/rs/emitter.py:935: if mapped == "py_len" and len(rendered_args) == 1:
src/toolchain2/emit/rs/emitter.py:963: if mapped == "py_print" and len(rendered_args) >= 1 and all(a.startswith("todo!(") for a in rendered_args):
src/toolchain2/emit/rs/emitter.py:967: if mapped == "py_print" and len(rendered_args) > 1:
```

### runtime_symbol / ts (1)

```
src/toolchain2/emit/ts/emitter.py:120: "perf_counter",
```
