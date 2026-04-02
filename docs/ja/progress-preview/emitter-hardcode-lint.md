<a href="../../en/progress-preview/emitter-hardcode-lint.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# emitter ハードコード違反マトリクス

> 機械生成ファイル。`python3 tools/check/check_emitter_hardcode_lint.py` で更新する。
> 生成日時: 2026-04-02T13:46:19
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
| **⬜ 未実装** | — | — | — | 8 | — | — | 8 | — | — | 8 | 8 | 8 | — | — | — | — | 8 | 8 |

## 詳細

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
