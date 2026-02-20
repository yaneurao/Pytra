# LanguageProfile 仕様（CodeEmitter）

このドキュメントは、`CodeEmitter` で利用する言語プロファイル JSON の仕様を定義します。

## 1. 目的

- 言語固有差分（型、演算子、ランタイム呼び出し、構文テンプレート）を Python コードから分離する。
- `py2cpp.py` などの各トランスパイラ本体を薄くし、共通化を進める。
- 例外的な変換のみ `hooks` で扱い、通常ケースは JSON 設定で処理する。

## 2. 配置

- `src/profiles/`
  - `common/core.json`: 全言語共通の既定値
  - `cpp/profile.json`: C++ 向け統合プロファイル（エントリ）
  - `cpp/types.json`: 型マップ
  - `cpp/operators.json`: 演算子マップ
  - `cpp/runtime_calls.json`: 組み込み・`module.attr` 呼び出しマップ
  - `cpp/syntax.json`: 文テンプレート

## 3. ロード順序

1. `common/core.json`
2. `<lang>/profile.json` の `include` 順
3. `<lang>/profile.json` 本体
4. CLI 上書き（必要時）

後勝ちマージを原則とします。

## 4. スキーマ（v1）

`profile.json` の最小例:

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
    "module": "pytra.runtime.cpp.hooks.cpp_hooks",
    "factory": "build_cpp_hooks"
  }
}
```

### 4.1 `types`

EAST 型名 -> 出力言語型名。

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

EAST 演算子 -> 出力トークン。

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

- `builtin_call`: `len`, `print` など
- `module_attr_call`: `module.attr` 形式の呼び出し
- `method_call`: `list.append` など

```json
{
  "runtime_calls": {
    "builtin_call": {
      "len": "py_len",
      "print": "py_print"
    },
    "module_attr_call": {
      "pytra.std.sys": {
        "write_stdout": "py_sys_write_stdout"
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

文テンプレートと構文スイッチ。

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

予約語回避、接頭辞、識別子規則。

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

profile で表現しにくい分岐だけを hooks へ寄せます。

```json
{
  "hooks": {
    "module": "pytra.runtime.cpp.hooks.cpp_hooks",
    "factory": "build_cpp_hooks"
  }
}
```

`module` は言語固有側（例: `src/pytra/runtime/cpp/hooks/`）に配置し、`src/common/` へは置きません。

## 5. Hooks 仕様

`profile.hooks` は JSON で表現しにくい分岐のみ担当します。

selfhost 制約:
- hooks API は `dict[str, Any]` / `list[str]` / `str` / `bool` を中心に扱い、`callable` 型注釈に依存しません。
- `CodeEmitter` 側はフックを「辞書から取り出して呼ぶ」方式で扱い、型注釈由来の selfhost 変換詰まりを避けます。

- `on_emit_stmt(emitter, stmt)`:
  - `True` を返すと既定の文出力をスキップ
- `on_render_call(emitter, call_node, func_node, rendered_args, rendered_kwargs)`
- `on_render_binop(emitter, binop_node, left, right)`

戻り値:
- `None`: 既定ロジック継続
- `str`: その文字列を採用

### 5.1 実装位置（C++）

```text
src/pytra/runtime/cpp/hooks/cpp_hooks.py
```

## 6. 妥当性ルール

- `schema_version` は必須（現行 `1`）。
- `language` は必須。
- `include` は相対パスのみ許可。
- 未知キーは警告（エラーにはしない）。
- 必須キー欠落は起動時エラー。

## 7. 移行方針

1. C++ から先行移行する。
2. `py2cpp.py` 直書きマップを順次削除する。
3. `BaseEmitter` を `CodeEmitter` へ改名し、`BaseEmitter = CodeEmitter` で互換維持する。
