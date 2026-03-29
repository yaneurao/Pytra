<a href="../../en/progress/emitter-hardcode-lint.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# emitter ハードコード違反マトリクス

> 機械生成ファイル。`python3 tools/check/check_emitter_hardcode_lint.py` で更新する。
> 生成日時: 2026-03-30T06:59:55
> [関連リンク](./index.md)

emitter が EAST3 の情報を使わず、モジュール名・runtime 関数名・クラス名等を文字列で直書きしている箇所を grep で検出したマトリクス。
違反数が 0 に近づくほど emitter が EAST3 正本に従った実装になっている。

| アイコン | 意味 |
|---|---|
| 🟩 | 違反なし（0件） |
| 🟥 | 違反あり（件数を表示） |
| ⬜ | 未実装（toolchain2 に emitter なし） |

| カテゴリ | cpp | rs | cs | ps1 | js | ts | dart | go | java | swift | kotlin | ruby | lua | scala | php | nim | julia | zig |
|--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| module name | 🟩0 | 🟥2 | ⬜ | ⬜ | ⬜ | 🟥1 | ⬜ | 🟥6 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| runtime symbol | 🟥1 | 🟥3 | ⬜ | ⬜ | ⬜ | 🟥1 | ⬜ | 🟥2 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| target const | 🟩0 | 🟩0 | ⬜ | ⬜ | ⬜ | 🟩0 | ⬜ | 🟩0 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| prefix match | 🟩0 | 🟩0 | ⬜ | ⬜ | ⬜ | 🟩0 | ⬜ | 🟩0 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| class name | 🟥3 | 🟥1 | ⬜ | ⬜ | ⬜ | 🟥6 | ⬜ | 🟥20 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| Python syntax | 🟩0 | 🟩0 | ⬜ | ⬜ | ⬜ | 🟩0 | ⬜ | 🟩0 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |

## 詳細

### class_name / cpp (3)

```
src/toolchain2/emit/cpp/emitter.py:72: "BaseException", "Exception", "ValueError", "TypeError", "IndexError",
src/toolchain2/emit/cpp/emitter.py:1277: if attr == "add_argument" and owner_type == "ArgumentParser":
src/toolchain2/emit/cpp/emitter.py:2650: if bn in ("BaseException", "Exception", "RuntimeError", "ValueError", "TypeError", "IndexError", "KeyError") or rc == "s
```

### class_name / go (20)

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
src/toolchain2/emit/go/types.py:39: "Exception": "*PytraErrorCarrier",
```

### class_name / rs (1)

```
src/toolchain2/emit/rs/types.py:41: "Exception": "Box<dyn std::error::Error>",
```

### class_name / ts (6)

```
src/toolchain2/emit/ts/emitter.py:111: "Path", "PyPath", "py_math_tau", "py_env_target",
src/toolchain2/emit/ts/emitter.py:116: "ArgumentParser",
src/toolchain2/emit/ts/emitter.py:224: "Exception", "BaseException", "RuntimeError", "ValueError",
src/toolchain2/emit/ts/emitter.py:1576: "Exception": "Error",
src/toolchain2/emit/ts/types.py:41: "Exception": "Error",
src/toolchain2/emit/ts/types.py:48: "Path": "PyPath",
```

### module_name / common (1)

```
src/toolchain2/emit/common/code_emitter.py:128: e.g., {"math": "pytra.std.math", "path": "pytra.std.os_path"}
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
src/toolchain2/emit/rs/emitter.py:3308: "math": "math_native.rs",
src/toolchain2/emit/rs/emitter.py:3309: "time": "time_native.rs",
```

### module_name / ts (1)

```
src/toolchain2/emit/ts/emitter.py:122: "sys", "pyset_argv", "pyset_path",
```

### prefix_match / common (1)

```
src/toolchain2/emit/common/code_emitter.py:41: "skip_modules": ["pytra.built_in.", "pytra.std.", "pytra.utils.", "pytra.core."]
```

### runtime_symbol / common (2)

```
src/toolchain2/emit/common/code_emitter.py:36: "py_print": "__pytra_print",
src/toolchain2/emit/common/code_emitter.py:37: "py_len": "__pytra_len",
```

### runtime_symbol / cpp (1)

```
src/toolchain2/emit/cpp/emitter.py:1476: if rc in ("py_print", "py_len") and len(arg_strs) >= 1:
```

### runtime_symbol / go (2)

```
src/toolchain2/emit/go/emitter.py:2383: if dispatch == "py_print" or bn == "print":
src/toolchain2/emit/go/emitter.py:2387: if dispatch == "py_len" or bn == "len":
```

### runtime_symbol / rs (3)

```
src/toolchain2/emit/rs/emitter.py:926: if mapped == "py_len" and len(rendered_args) == 1:
src/toolchain2/emit/rs/emitter.py:954: if mapped == "py_print" and len(rendered_args) >= 1 and all(a.startswith("todo!(") for a in rendered_args):
src/toolchain2/emit/rs/emitter.py:958: if mapped == "py_print" and len(rendered_args) > 1:
```

### runtime_symbol / ts (1)

```
src/toolchain2/emit/ts/emitter.py:120: "perf_counter",
```
