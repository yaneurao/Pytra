<a href="../../ja/progress-preview/emitter-hardcode-lint.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Emitter hardcode violation matrix

> Machine-generated file. Run `python3 tools/check/check_emitter_hardcode_lint.py` to update.
> Generated at: 2026-04-04 20:17:19
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
| module name | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 |
| runtime symbol | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟥 |
| target const | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| prefix match | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| class name | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟥 |
| Python syntax | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| type_id | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| skip pure py | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟥 |
| rt: type_id | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 |
| rt: call_cov | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟩 | 🟥 | 🟥 |
| **🟩 PASS** | 9 | 9 | 9 | 9 | 9 | 9 | 9 | 9 | 9 | 6 | 6 | 9 | 9 | 8 | 9 | 10 | 6 | 5 |
| **🟥 FAIL** | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 4 | 4 | 1 | 1 | 2 | 1 | — | 4 | 5 |
| **⬜ Not impl.** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

## Details

### class_name / julia (1)

```
src/toolchain2/emit/julia/subset.py:145: if base not in {"Exception", "ValueError", "TypeError", "RuntimeError"}:
```

### class_name / kotlin (5)

```
src/toolchain2/emit/kotlin/emitter.py:47: if name in self.module_class_names or name.endswith("Error") or name.endswith("Exception"):
src/toolchain2/emit/kotlin/emitter.py:529: if func_kind == "Name" and (self._str(func, "id").endswith("Error") or self._str(func, "id").endswith("Exception")):
src/toolchain2/emit/kotlin/emitter.py:532: if func_kind == "Attribute" and (self._str(func, "attr").endswith("Error") or self._str(func, "attr").endswith("Exceptio
src/toolchain2/emit/kotlin/emitter.py:1306: if func_id.endswith("Error") or func_id.endswith("Exception"):
src/toolchain2/emit/kotlin/emitter.py:1325: if func_name.startswith("pytra_built_in_error.") and (func_name.endswith("Error") or func_name.endswith("Exception")):
```

### class_name / scala (8)

```
src/toolchain2/emit/scala/emitter.py:44: if name in self.module_class_names or name.endswith("Error") or name.endswith("Exception"):
src/toolchain2/emit/scala/emitter.py:476: if exc_type.endswith("Error") or exc_type.endswith("Exception"):
src/toolchain2/emit/scala/emitter.py:483: if self._str(func, "kind") == "Name" and (self._str(func, "id").endswith("Error") or self._str(func, "id").endswith("Exc
src/toolchain2/emit/scala/emitter.py:486: if self._str(func, "kind") == "Attribute" and (self._str(func, "attr").endswith("Error") or self._str(func, "attr").ends
src/toolchain2/emit/scala/emitter.py:812: if import_path.startswith("pytra_built_in_error.") and (ident.endswith("Error") or ident.endswith("Exception")):
src/toolchain2/emit/scala/emitter.py:849: if module_id in ("pytra.built_in.error", "pytra_built_in_error") and (attr.endswith("Error") or attr.endswith("Exception
src/toolchain2/emit/scala/emitter.py:1149: elif func_id.endswith("Error") or func_id.endswith("Exception"):
src/toolchain2/emit/scala/emitter.py:1154: if func_name.startswith("pytra_built_in_error.") and (func_name.endswith("Error") or func_name.endswith("Exception")):
```

### class_name / zig (2)

```
src/toolchain2/emit/zig/emitter.py:1358: "pytra.std.pathlib": {"Path"},
src/toolchain2/emit/zig/emitter.py:1359: "pytra.std.argparse": {"ArgumentParser", "Namespace"},
```

### module_name / kotlin (8)

```
src/toolchain2/emit/kotlin/emitter.py:263: if mod in ("math", "pytra.std.math"):
src/toolchain2/emit/kotlin/emitter.py:271: if mod in ("time", "pytra.std.time") and name == "perf_counter":
src/toolchain2/emit/kotlin/emitter.py:948: if module_id in ("math", "pytra.std.math"):
src/toolchain2/emit/kotlin/emitter.py:950: if module_id in ("time", "pytra.std.time"):
src/toolchain2/emit/kotlin/emitter.py:954: if module_id in ("os", "pytra.std.os"):
src/toolchain2/emit/kotlin/emitter.py:955: return "os"
src/toolchain2/emit/kotlin/emitter.py:980: if module_id in ("math", "pytra.std.math"):
src/toolchain2/emit/kotlin/emitter.py:986: if module_id in ("time", "pytra.std.time"):
```

### module_name / scala (8)

```
src/toolchain2/emit/scala/emitter.py:226: if mod in ("math", "pytra.std.math"):
src/toolchain2/emit/scala/emitter.py:229: if mod in ("time", "pytra.std.time") and name == "perf_counter":
src/toolchain2/emit/scala/emitter.py:817: if module_id in ("math", "pytra.std.math"):
src/toolchain2/emit/scala/emitter.py:819: if module_id in ("time", "pytra.std.time"):
src/toolchain2/emit/scala/emitter.py:823: if module_id in ("os", "pytra.std.os"):
src/toolchain2/emit/scala/emitter.py:824: return "os"
src/toolchain2/emit/scala/emitter.py:851: if module_id in ("math", "pytra.std.math"):
src/toolchain2/emit/scala/emitter.py:853: if module_id in ("time", "pytra.std.time"):
```

### module_name / zig (7)

```
src/toolchain2/emit/zig/emitter.py:45: "mem", "fmt", "debug", "heap", "io", "os", "fs",
src/toolchain2/emit/zig/emitter.py:237: return tag == "math"
src/toolchain2/emit/zig/emitter.py:1392: if module_id == "math":
src/toolchain2/emit/zig/emitter.py:1395: elif module_id == "time":
src/toolchain2/emit/zig/emitter.py:4341: if isinstance(obj_node_for_attr, dict) and obj_node_for_attr.get("kind") == "Name" and str(obj_node_for_attr.get("id")) 
src/toolchain2/emit/zig/emitter.py:5540: if isinstance(obj_node, dict) and obj_node.get("kind") == "Name" and str(obj_node.get("id")) == "json":
src/toolchain2/emit/zig/emitter.py:5556: if isinstance(obj_node, dict) and obj_node.get("kind") == "Name" and str(obj_node.get("id")) == "math":
```

### python_syntax / common (1)

```
src/toolchain2/emit/common/cli_runner.py:8: if __name__ == "__main__":
```

### rt:call_coverage / cpp (31)

```
src/runtime/cpp/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["ceil"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["cos"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["e"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["exp"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["fabs"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["floor"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["log"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["log10"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["math.e"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["math.pi"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["open"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["path.abspath"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["pi"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["pow"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["py_dumps"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["py_dumps_jv"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["py_loads"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["py_loads_arr"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["py_loads_obj"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["py_write_text"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["sin"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["sqrt"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["std::runtime_error"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["str.index"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/cpp/mapping.json:0: calls["tan"] not found in any EAST3 golden
```

### rt:call_coverage / cs (35)

```
src/runtime/cs/mapping.json:0: calls["SystemExit"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["cast"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["endswith"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["enumerate"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["index"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["isalpha"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["isdigit"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["items"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["lstrip"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["math.e"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["math.pi"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["max"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["min"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["perf_counter"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["py_bool"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["py_in"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["py_isalpha"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["py_isdigit"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["py_mod"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["py_slice"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["pytra_isinstance"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["replace"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["reversed"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["rstrip"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["startswith"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/cs/mapping.json:0: calls["strip"] not found in any EAST3 golden
```

### rt:call_coverage / dart (56)

```
src/runtime/dart/mapping.json:0: calls["abs"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["acos"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["asin"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["atan"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["atan2"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["bool"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["ceil"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["cos"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["exp"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["fabs"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["float"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["floor"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["hypot"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["int"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["isfinite"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["isinf"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["isnan"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["log"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["log10"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["log2"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["makedirs"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["math.e"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["math.inf"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["math.nan"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["math.pi"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["math.tau"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["open"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["perf_counter"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["pow"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["print"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["py_bool"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["py_in"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["py_slice"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["py_truthy"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["pyopen"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["round"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["sin"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["sqrt"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["str.count"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["str.index"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["str.isspace"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["sys.argv"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["sys.path"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["tan"] not found in any EAST3 golden
src/runtime/dart/mapping.json:0: calls["trunc"] not found in any EAST3 golden
```

### rt:call_coverage / go (33)

```
src/runtime/go/mapping.json:0: calls["atan2"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["ceil"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["cos"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["exp"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["fabs"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["floor"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["log"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["log10"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["math.atan2"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["pow"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_enumerate"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_reversed"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["randint"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["random"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["seed"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["sin"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["sorted"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["sqrt"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["std::runtime_error"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["str.count"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["str.index"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["str.isspace"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["tan"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["tuple_ctor"] not found in any EAST3 golden
```

### rt:call_coverage / java (38)

```
src/runtime/java/mapping.json:0: calls["ArgumentParser"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["Path"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["ceil"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["deque"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["dumps"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["fabs"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["floor"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["json.loads_obj"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["loads"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["loads_arr"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["loads_obj"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["makedirs"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["math.e"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["math.pi"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["os.path.basename"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["os.path.dirname"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["os.path.exists"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["os.path.join"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["os.path.splitext"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["perf_counter"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["py_bool"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["py_slice"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["pytra_isinstance"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["sqrt"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["std::runtime_error"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["sub"] not found in any EAST3 golden
src/runtime/java/mapping.json:0: calls["tuple_ctor"] not found in any EAST3 golden
```

### rt:call_coverage / julia (73)

```
src/runtime/julia/mapping.json:0: calls["Exception"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["IndexError"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["RuntimeError"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["TypeError"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["ValueError"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["abs"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["acos"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["asin"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["atan"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["atan2"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bool"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bytearray.append"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bytearray.clear"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bytearray.pop"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["ceil"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["cos"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["deque"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["exp"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["fabs"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["float"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["floor"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["hypot"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["int"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["isfinite"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["isinf"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["isnan"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["log"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["log10"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["log2"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["makedirs"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["math.e"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["math.inf"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["math.nan"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["math.pi"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["math.tau"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["max"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["min"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["open"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["perf_counter"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["pow"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["print"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["py_bool"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["py_enumerate"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["py_in"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["py_isinstance"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["py_reversed"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["py_slice"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["py_truthy"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["pyopen"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["round"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["set"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["sin"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["sorted"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["sqrt"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["std::runtime_error"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["str.count"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["str.index"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["str.isspace"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["sys.argv"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["tan"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["trunc"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["tuple_ctor"] not found in any EAST3 golden
```

### rt:call_coverage / kotlin (17)

```
src/runtime/kotlin/mapping.json:0: calls["bool"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["float"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["int"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["open"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["print"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["range"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["set"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
```

### rt:call_coverage / lua (77)

```
src/runtime/lua/mapping.json:0: calls["ArgumentParser"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["Path"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["abs"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["acos"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["asin"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["atan"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["atan2"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["ceil"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["cos"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["deque"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["dict.update"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["dumps"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["exp"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["fabs"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["float"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["floor"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["hypot"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["int"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["isfinite"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["isinf"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["isnan"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["list.insert"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["list.remove"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["loads"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["loads_arr"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["log"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["log10"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["log2"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["makedirs"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["math.e"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["math.inf"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["math.nan"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["math.pi"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["math.tau"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["max"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["min"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["module_ctor.math"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["open"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["perf_counter"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["pow"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["print"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["py_bool"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["py_enumerate"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["py_in"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["py_isinstance"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["py_reversed"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["py_slice"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["py_truthy"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["pyopen"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["pytra_isinstance"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["round"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["set_argv"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["set_path"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["sin"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["sorted"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["sqrt"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["std::runtime_error"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["str.count"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["str.index"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["str.isspace"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["sub"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["sys.argv"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["sys.path"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["tan"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["trunc"] not found in any EAST3 golden
src/runtime/lua/mapping.json:0: calls["tuple_ctor"] not found in any EAST3 golden
```

### rt:call_coverage / php (66)

```
src/runtime/php/mapping.json:0: calls["abs"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["acos"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["asin"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["atan"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["atan2"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["ceil"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["cos"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["dict.update"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["exp"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["fabs"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["float"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["floor"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["hypot"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["int"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["isfinite"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["isinf"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["isnan"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["list.insert"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["log"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["log10"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["log2"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["makedirs"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["math.e"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["math.inf"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["math.nan"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["math.pi"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["math.tau"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["max"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["min"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["open"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["perf_counter"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["pow"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["print"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["py_bool"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["py_enumerate"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["py_in"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["py_isinstance"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["py_reversed"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["py_slice"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["py_truthy"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["pyopen"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["pytra_isinstance"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["round"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["set"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["sin"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["sorted"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["sqrt"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["std::runtime_error"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["str.count"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["str.index"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["str.isspace"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["tan"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["trunc"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["tuple_ctor"] not found in any EAST3 golden
src/runtime/php/mapping.json:0: calls["type"] not found in any EAST3 golden
```

### rt:call_coverage / ps1 (80)

```
src/runtime/powershell/mapping.json:0: calls["acos"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["asin"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["atan"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["atan2"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["ceil"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["cos"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["dict.update"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["dict_ctor"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["exp"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["fabs"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["floor"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["gif.grayscale_palette"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["gif.save_gif"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["hypot"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["isfinite"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["isinf"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["isnan"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["list.copy"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["list.insert"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["list.remove"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["log"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["log10"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["log2"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["makedirs"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["math.e"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["math.inf"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["math.nan"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["math.pi"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["math.tau"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["open"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["path.abspath"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["path.isdir"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["path.isfile"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["perf_counter"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["pow"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_abs"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_bool"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_dumps"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_enumerate"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_filter"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_in"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_isinstance"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_loads"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_map"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_reversed"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_slice"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_sorted"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_sum"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_truthy"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_write_text"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["py_zip"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["re.findall"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["re.match"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["re.search"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["round"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["sin"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["sqrt"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["std::runtime_error"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["str.count"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["str.format"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["str.index"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["str.isspace"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["sys.argv"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["sys.maxsize"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["sys.path"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["sys.platform"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["sys.stderr"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["sys.stdout"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["tan"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["trunc"] not found in any EAST3 golden
src/runtime/powershell/mapping.json:0: calls["tuple_ctor"] not found in any EAST3 golden
```

### rt:call_coverage / rs (47)

```
src/runtime/rs/mapping.json:0: calls["__import__.os"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["__import__.subprocess"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["basename"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["ceil"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["cos"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["dirname"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["e"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["exists"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["exp"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["fabs"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["floor"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["getcwd"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["gif.save_gif"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["glob"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["join"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["log"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["log10"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["math.e"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["math.pi"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["open"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["perf_counter"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["pi"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["pow"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["py_enumerate"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["py_open"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["py_reversed"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["pytra.std.os.environ"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["pytra_isinstance"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["sin"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["sorted"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["splitext"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["sqrt"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["std::runtime_error"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["str.count"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["str.index"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["str.isspace"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["tan"] not found in any EAST3 golden
src/runtime/rs/mapping.json:0: calls["tuple_ctor"] not found in any EAST3 golden
```

### rt:call_coverage / ruby (74)

```
src/runtime/ruby/mapping.json:0: calls["abs"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["acos"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["asin"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["atan"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["atan2"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["ceil"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["cos"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["exp"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["fabs"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["float"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["floor"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["hypot"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["int"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["isfinite"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["isinf"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["isnan"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["log"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["log10"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["log2"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["makedirs"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["math.e"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["math.inf"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["math.nan"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["math.pi"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["math.tau"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["max"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["min"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["open"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["os.getcwd"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["os.mkdir"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["os_path.abspath"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["os_path.basename"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["os_path.dirname"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["os_path.exists"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["os_path.join"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["os_path.splitext"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["perf_counter"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["pow"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["print"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["py_bool"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["py_enumerate"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["py_in"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["py_reversed"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["py_slice"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["py_truthy"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["pyopen"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["pytra_isinstance"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["round"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["sin"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["sorted"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["sqrt"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["std::runtime_error"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["str.count"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["str.index"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["str.isspace"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["sys.argv"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["sys.path"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["tan"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["trunc"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["tuple_ctor"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["type"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["write_stderr"] not found in any EAST3 golden
src/runtime/ruby/mapping.json:0: calls["write_stdout"] not found in any EAST3 golden
```

### rt:call_coverage / scala (17)

```
src/runtime/scala/mapping.json:0: calls["bool"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["float"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["int"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["open"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["print"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["range"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["set"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
```

### rt:call_coverage / swift (20)

```
src/runtime/swift/mapping.json:0: calls["bool"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["float"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["floor"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["int"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["perf_counter"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["print"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["py_bool"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["py_in"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["py_slice"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["py_truthy"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["sqrt"] not found in any EAST3 golden
src/runtime/swift/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
```

### rt:call_coverage / ts (67)

```
src/runtime/ts/mapping.json:0: calls["abs"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["acos"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["asin"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["atan"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["atan2"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["bool"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["ceil"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["cos"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["exp"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["fabs"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["float"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["floor"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["hypot"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["int"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["isalnum"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["isalpha"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["isdigit"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["isfinite"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["isinf"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["isnan"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["log"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["log10"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["log2"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["makedirs"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["math.e"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["math.inf"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["math.nan"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["math.pi"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["math.tau"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["max"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["min"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["open"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["perf_counter"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["pow"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["print"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["py_bool"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["py_enumerate"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["py_in"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["py_isinstance"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["py_reversed"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["py_slice"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["py_truthy"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["pyopen"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["round"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["sin"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["sorted"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["sqrt"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["std::runtime_error"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["str.count"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["str.index"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["str.isspace"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["sys.argv"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["sys.path"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["tan"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["trunc"] not found in any EAST3 golden
src/runtime/ts/mapping.json:0: calls["tuple_ctor"] not found in any EAST3 golden
```

### rt:call_coverage / zig (20)

```
src/runtime/zig/mapping.json:0: calls["basename"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["dict_ctor"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["dirname"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["exists"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["getcwd"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["glob"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["join"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["math.e"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["math.pi"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["perf_counter"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["pytra_isinstance"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
src/runtime/zig/mapping.json:0: calls["tuple_ctor"] not found in any EAST3 golden
```

### rt:type_id / lua (9)

```
src/runtime/lua/built_in/py_runtime.lua:11: PYTRA_TID_NONE = 0
src/runtime/lua/built_in/py_runtime.lua:12: PYTRA_TID_BOOL = 1
src/runtime/lua/built_in/py_runtime.lua:13: PYTRA_TID_INT = 2
src/runtime/lua/built_in/py_runtime.lua:14: PYTRA_TID_FLOAT = 3
src/runtime/lua/built_in/py_runtime.lua:15: PYTRA_TID_STR = 4
src/runtime/lua/built_in/py_runtime.lua:16: PYTRA_TID_LIST = 5
src/runtime/lua/built_in/py_runtime.lua:17: PYTRA_TID_DICT = 6
src/runtime/lua/built_in/py_runtime.lua:18: PYTRA_TID_SET = 7
src/runtime/lua/built_in/py_runtime.lua:19: PYTRA_TID_OBJECT = 8
```

### runtime_symbol / julia (1)

```
src/toolchain2/emit/julia/subset.py:322: "write_rgb_png",
```

### runtime_symbol / kotlin (1)

```
src/toolchain2/emit/kotlin/emitter.py:271: if mod in ("time", "pytra.std.time") and name == "perf_counter":
```

### runtime_symbol / scala (1)

```
src/toolchain2/emit/scala/emitter.py:229: if mod in ("time", "pytra.std.time") and name == "perf_counter":
```

### runtime_symbol / zig (1)

```
src/toolchain2/emit/zig/emitter.py:241: return runtime_symbol == "perf_counter" or runtime_symbol == "perf_counter_ns"
```

### skip_pure_python / julia (1)

```
src/runtime/julia/mapping.json:0: skip_modules contains "pytra.std.collections" but pytra.std.collections is pure Python (no @extern)
```

### skip_pure_python / zig (1)

```
src/runtime/zig/mapping.json:0: skip_modules contains "pytra.std.pathlib" but pytra.std.pathlib is pure Python (no @extern)
```
