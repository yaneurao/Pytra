<a href="../../en/progress-preview/emitter-hardcode-lint.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# emitter ハードコード違反マトリクス

> 機械生成ファイル。`python3 tools/check/check_emitter_hardcode_lint.py` で更新する。
> 生成日時: 2026-04-03 20:18:17
> [関連リンク](./index.md)

emitter が EAST3 の情報を使わず、モジュール名・runtime 関数名・クラス名等を文字列で直書きしている箇所を grep で検出したマトリクス。
違反数が 0 に近づくほど emitter が EAST3 正本に従った実装になっている。

| アイコン | 意味 |
|---|---|
| 🟩 | 違反なし |
| 🟥 | 違反あり（詳細は下の表を参照） |
| ⬜ | 未実装（toolchain2 に emitter なし） |

> **js** は独自 emitter を持たず **ts** emitter を共用するため、js 列は ts と同一の結果を表示する。

| カテゴリ | cpp | rs | cs | ps1 | js | ts | dart | go | java | scala | kotlin | swift | ruby | lua | php | nim | julia | zig |
|--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| module name | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| runtime symbol | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| target const | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| prefix match | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| class name | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| Python syntax | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| type_id | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 |
| skip pure py | 🟩 | 🟩 | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 |
| rt: type_id | 🟥 | 🟥 | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 | 🟩 | 🟥 | 🟩 | 🟩 | 🟩 | 🟩 |
| rt: call_cov | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟥 | 🟩 | 🟥 | 🟥 |
| **🟩 PASS** | 8 | 6 | 9 | 7 | 9 | 9 | 9 | 7 | 9 | 9 | 9 | 4 | 9 | 8 | 9 | 10 | 9 | 8 |
| **🟥 FAIL** | 2 | 4 | 1 | 3 | 1 | 1 | 1 | 3 | 1 | 1 | 1 | 6 | 1 | 2 | 1 | — | 1 | 2 |
| **⬜ 未実装** | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |

## 詳細

### class_name / rs (1)

```
src/toolchain2/emit/rs/emitter.py:1590: is_path_ref = inner_rs in ("Path", "PyPath", "pathlib.Path", "pytra.std.pathlib.Path") or inner_rs.endswith(".Path")
```

### class_name / swift (3)

```
src/toolchain2/emit/swift/emitter.py:1891: if owner_type == "ArgumentParser" and attr_name == "add_argument":
src/toolchain2/emit/swift/emitter.py:1906: if owner_type == "ArgumentParser" and attr_name == "parse_args":
src/toolchain2/emit/swift/emitter.py:3387: lines.append(indent + "} catch let " + handler_name + " as " + _safe_ident(handler_type_any.get("id"), "Exception") + " 
```

### module_name / rs (5)

```
src/toolchain2/emit/rs/emitter.py:1551: if module_id == "os" and attr == "environ":
src/toolchain2/emit/rs/emitter.py:2151: if mod_name == "os":
src/toolchain2/emit/rs/emitter.py:2153: if mod_name == "subprocess":
src/toolchain2/emit/rs/emitter.py:2940: if method == "glob" and len(rendered_args) == 1:
src/toolchain2/emit/rs/emitter.py:4068: if mod_name in ("os", "subprocess"):
```

### module_name / swift (2)

```
src/toolchain2/emit/swift/emitter.py:1224: if owner_id == "math":
src/toolchain2/emit/swift/emitter.py:1800: if owner_id == "math" and attr_name in _SWIFT_MATH_RUNTIME_SYMBOLS:
```

### prefix_match / swift (1)

```
src/toolchain2/emit/swift/emitter.py:4407: module_id.startswith("pytra.built_in.")
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

### rt:call_coverage / go (17)

```
src/runtime/go/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_chr"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_enumerate"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_float_from_str"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_floordiv"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_len"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_ord"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["py_reversed"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["sorted"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["std::runtime_error"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["str.count"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["str.index"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["str.isspace"] not found in any EAST3 golden
src/runtime/go/mapping.json:0: calls["str.rfind"] not found in any EAST3 golden
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

### rt:call_coverage / julia (63)

```
src/runtime/julia/mapping.json:0: calls["abs"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["acos"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["asin"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["atan"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["atan2"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bool"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["ceil"] not found in any EAST3 golden
src/runtime/julia/mapping.json:0: calls["cos"] not found in any EAST3 golden
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

### rt:call_coverage / kotlin (15)

```
src/runtime/kotlin/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["float"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["int"] not found in any EAST3 golden
src/runtime/kotlin/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
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

### rt:call_coverage / ps1 (75)

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

### rt:call_coverage / rs (44)

```
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

### rt:call_coverage / scala (13)

```
src/runtime/scala/mapping.json:0: calls["bytearray"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["bytearray_ctor"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["bytes"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["bytes_ctor"] not found in any EAST3 golden
src/runtime/scala/mapping.json:0: calls["list_ctor"] not found in any EAST3 golden
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

### rt:type_id / cpp (4)

```
src/runtime/cpp/core/py_runtime.h:31: bool py_tid_is_subtype(int64 actual_type_id, int64 expected_type_id);
src/runtime/cpp/core/py_runtime.h:32: bool py_tid_issubclass(int64 actual_type_id, int64 expected_type_id);
src/runtime/cpp/core/py_runtime.h:33: bool py_tid_isinstance(const object& value, int64 expected_type_id);
src/runtime/cpp/core/py_runtime.h:34: int64 py_tid_register_class_type(int64 base_type_id);
```

### rt:type_id / go (2)

```
src/runtime/go/built_in/py_runtime.go:248: func pytra_isinstance(actualTypeId int64, tid int64) bool {
src/runtime/go/built_in/py_runtime.go:302: func py_runtime_object_type_id(value any) int64 {
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

### rt:type_id / ps1 (8)

```
src/runtime/powershell/built_in/py_runtime.ps1:505: function __pytra_isinstance {
src/runtime/powershell/built_in/py_runtime.ps1:509: if ($type_name -eq "PYTRA_TID_BOOL") { $type_name = "bool" }
src/runtime/powershell/built_in/py_runtime.ps1:510: elseif ($type_name -eq "PYTRA_TID_INT") { $type_name = "int" }
src/runtime/powershell/built_in/py_runtime.ps1:511: elseif ($type_name -eq "PYTRA_TID_FLOAT") { $type_name = "float" }
src/runtime/powershell/built_in/py_runtime.ps1:512: elseif ($type_name -eq "PYTRA_TID_STR") { $type_name = "str" }
src/runtime/powershell/built_in/py_runtime.ps1:513: elseif ($type_name -eq "PYTRA_TID_LIST") { $type_name = "list" }
src/runtime/powershell/built_in/py_runtime.ps1:514: elseif ($type_name -eq "PYTRA_TID_DICT") { $type_name = "dict" }
src/runtime/powershell/built_in/py_runtime.ps1:515: elseif ($type_name -eq "PYTRA_TID_NONE") { return ($obj -eq $null) }
```

### rt:type_id / rs (62)

```
src/runtime/rs/built_in/py_runtime.rs:1201: pub const PYTRA_TID_NONE: i64 = 0;
src/runtime/rs/built_in/py_runtime.rs:1202: pub const PYTRA_TID_BOOL: i64 = 1;
src/runtime/rs/built_in/py_runtime.rs:1203: pub const PYTRA_TID_INT: i64 = 2;
src/runtime/rs/built_in/py_runtime.rs:1204: pub const PYTRA_TID_FLOAT: i64 = 3;
src/runtime/rs/built_in/py_runtime.rs:1205: pub const PYTRA_TID_STR: i64 = 4;
src/runtime/rs/built_in/py_runtime.rs:1206: pub const PYTRA_TID_LIST: i64 = 5;
src/runtime/rs/built_in/py_runtime.rs:1207: pub const PYTRA_TID_DICT: i64 = 6;
src/runtime/rs/built_in/py_runtime.rs:1208: pub const PYTRA_TID_SET: i64 = 7;
src/runtime/rs/built_in/py_runtime.rs:1209: pub const PYTRA_TID_OBJECT: i64 = 8;
src/runtime/rs/built_in/py_runtime.rs:1225: PYTRA_TID_NONE,
src/runtime/rs/built_in/py_runtime.rs:1227: order: PYTRA_TID_NONE,
src/runtime/rs/built_in/py_runtime.rs:1228: min: PYTRA_TID_NONE,
src/runtime/rs/built_in/py_runtime.rs:1229: max: PYTRA_TID_NONE,
src/runtime/rs/built_in/py_runtime.rs:1233: PYTRA_TID_BOOL,
src/runtime/rs/built_in/py_runtime.rs:1235: order: PYTRA_TID_BOOL,
src/runtime/rs/built_in/py_runtime.rs:1236: min: PYTRA_TID_BOOL,
src/runtime/rs/built_in/py_runtime.rs:1237: max: PYTRA_TID_BOOL,
src/runtime/rs/built_in/py_runtime.rs:1241: PYTRA_TID_INT,
src/runtime/rs/built_in/py_runtime.rs:1243: order: PYTRA_TID_INT,
src/runtime/rs/built_in/py_runtime.rs:1244: min: PYTRA_TID_INT,
src/runtime/rs/built_in/py_runtime.rs:1245: max: PYTRA_TID_INT,
src/runtime/rs/built_in/py_runtime.rs:1249: PYTRA_TID_FLOAT,
src/runtime/rs/built_in/py_runtime.rs:1251: order: PYTRA_TID_FLOAT,
src/runtime/rs/built_in/py_runtime.rs:1252: min: PYTRA_TID_FLOAT,
src/runtime/rs/built_in/py_runtime.rs:1253: max: PYTRA_TID_FLOAT,
src/runtime/rs/built_in/py_runtime.rs:1257: PYTRA_TID_STR,
src/runtime/rs/built_in/py_runtime.rs:1259: order: PYTRA_TID_STR,
src/runtime/rs/built_in/py_runtime.rs:1260: min: PYTRA_TID_STR,
src/runtime/rs/built_in/py_runtime.rs:1261: max: PYTRA_TID_STR,
src/runtime/rs/built_in/py_runtime.rs:1265: PYTRA_TID_LIST,
src/runtime/rs/built_in/py_runtime.rs:1267: order: PYTRA_TID_LIST,
src/runtime/rs/built_in/py_runtime.rs:1268: min: PYTRA_TID_LIST,
src/runtime/rs/built_in/py_runtime.rs:1269: max: PYTRA_TID_LIST,
src/runtime/rs/built_in/py_runtime.rs:1273: PYTRA_TID_DICT,
src/runtime/rs/built_in/py_runtime.rs:1275: order: PYTRA_TID_DICT,
src/runtime/rs/built_in/py_runtime.rs:1276: min: PYTRA_TID_DICT,
src/runtime/rs/built_in/py_runtime.rs:1277: max: PYTRA_TID_DICT,
src/runtime/rs/built_in/py_runtime.rs:1281: PYTRA_TID_SET,
src/runtime/rs/built_in/py_runtime.rs:1283: order: PYTRA_TID_SET,
src/runtime/rs/built_in/py_runtime.rs:1284: min: PYTRA_TID_SET,
src/runtime/rs/built_in/py_runtime.rs:1285: max: PYTRA_TID_SET,
src/runtime/rs/built_in/py_runtime.rs:1289: PYTRA_TID_OBJECT,
src/runtime/rs/built_in/py_runtime.rs:1291: order: PYTRA_TID_OBJECT,
src/runtime/rs/built_in/py_runtime.rs:1292: min: PYTRA_TID_OBJECT,
src/runtime/rs/built_in/py_runtime.rs:1293: max: PYTRA_TID_OBJECT,
src/runtime/rs/built_in/py_runtime.rs:1328: PYTRA_TID_BOOL
src/runtime/rs/built_in/py_runtime.rs:1333: PYTRA_TID_INT
src/runtime/rs/built_in/py_runtime.rs:1338: PYTRA_TID_FLOAT
src/runtime/rs/built_in/py_runtime.rs:1343: PYTRA_TID_STR
src/runtime/rs/built_in/py_runtime.rs:1348: PYTRA_TID_LIST
src/runtime/rs/built_in/py_runtime.rs:1353: PYTRA_TID_DICT
src/runtime/rs/built_in/py_runtime.rs:1358: PYTRA_TID_SET
src/runtime/rs/built_in/py_runtime.rs:1365: None => PYTRA_TID_NONE,
src/runtime/rs/built_in/py_runtime.rs:1372: PyAny::Int(_) => PYTRA_TID_INT,
src/runtime/rs/built_in/py_runtime.rs:1373: PyAny::Float(_) => PYTRA_TID_FLOAT,
src/runtime/rs/built_in/py_runtime.rs:1374: PyAny::Bool(_) => PYTRA_TID_BOOL,
src/runtime/rs/built_in/py_runtime.rs:1375: PyAny::Str(_) => PYTRA_TID_STR,
src/runtime/rs/built_in/py_runtime.rs:1376: PyAny::List(_) => PYTRA_TID_LIST,
src/runtime/rs/built_in/py_runtime.rs:1377: PyAny::Dict(_) => PYTRA_TID_DICT,
src/runtime/rs/built_in/py_runtime.rs:1378: PyAny::Set(_) => PYTRA_TID_SET,
src/runtime/rs/built_in/py_runtime.rs:1379: PyAny::None => PYTRA_TID_NONE,
src/runtime/rs/built_in/py_runtime.rs:1420: PYTRA_TID_NONE
```

### runtime_symbol / swift (3)

```
src/toolchain2/emit/swift/emitter.py:1517: if runtime_module == "pytra.utils.png" and runtime_name == "write_rgb_png":
src/toolchain2/emit/swift/emitter.py:2521: if name == "perf_counter":
src/toolchain2/emit/swift/emitter.py:2655: if callee == "perf_counter":
```

### skip_pure_python / go (2)

```
src/runtime/go/mapping.json:0: skip_modules contains "pytra.std.pathlib" but pytra.std.pathlib is pure Python (no @extern)
src/runtime/go/mapping.json:0: skip_modules contains "pytra.std.random" but pytra.std.random is pure Python (no @extern)
```

### skip_pure_python / ps1 (9)

```
src/runtime/powershell/mapping.json:0: skip_modules contains "pytra.std." which skips pure Python module pytra.std.argparse
src/runtime/powershell/mapping.json:0: skip_modules contains "pytra.std." which skips pure Python module pytra.std.collections
src/runtime/powershell/mapping.json:0: skip_modules contains "pytra.std." which skips pure Python module pytra.std.env
src/runtime/powershell/mapping.json:0: skip_modules contains "pytra.std." which skips pure Python module pytra.std.json
src/runtime/powershell/mapping.json:0: skip_modules contains "pytra.std." which skips pure Python module pytra.std.pathlib
src/runtime/powershell/mapping.json:0: skip_modules contains "pytra.std." which skips pure Python module pytra.std.random
src/runtime/powershell/mapping.json:0: skip_modules contains "pytra.std." which skips pure Python module pytra.std.re
src/runtime/powershell/mapping.json:0: skip_modules contains "pytra.std." which skips pure Python module pytra.std.template
src/runtime/powershell/mapping.json:0: skip_modules contains "pytra.std." which skips pure Python module pytra.std.timeit
```

### skip_pure_python / zig (1)

```
src/runtime/zig/mapping.json:0: skip_modules contains "pytra.std.pathlib" but pytra.std.pathlib is pure Python (no @extern)
```

### target_constant / swift (2)

```
src/toolchain2/emit/swift/emitter.py:1228: return "M_E"
src/toolchain2/emit/swift/emitter.py:1809: return "M_E"
```
