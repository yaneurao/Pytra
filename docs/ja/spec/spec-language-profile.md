<a href="../../en/spec/spec-language-profile.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# LanguageProfile 仕様（CodeEmitter）

このドキュメントは、`CodeEmitter` で利用する言語プロファイル JSON の仕様を定義します。

## 1. 目的

- 言語固有差分（型、演算子、ランタイム呼び出し、構文テンプレート）を Python コードから分離する。
- `py2cpp.py` などの各トランスパイラ本体を薄くし、共通化を進める。
- 例外的な変換のみ `hooks` で扱い、通常ケースは JSON 設定で処理する。

## 2. 配置

全言語のプロファイルを `src/toolchain2/emit/profiles/` に集約する。言語ごとにディレクトリを分けない。

```
src/toolchain2/emit/profiles/
  core.json          # 全言語共通の既定値
  cpp.json           # C++
  go.json            # Go
  rs.json            # Rust
  java.json          # Java
  cs.json            # C#
  kotlin.json        # Kotlin
  swift.json         # Swift
  js.json            # JavaScript
  ts.json            # TypeScript
  dart.json          # Dart
  lua.json           # Lua
  ruby.json          # Ruby
  php.json           # PHP
  nim.json           # Nim
  scala.json         # Scala
  julia.json         # Julia
  powershell.json    # PowerShell
  zig.json           # Zig
```

ファイル名は `<target名>.json` で固定。`target名` は `pytra-cli2 --target` に渡す文字列と一致させる。

各言語の JSON には `types`, `operators`, `runtime_calls`, `syntax`, `lowering` を全て含める。分割ファイル（`types.json`, `operators.json` 等）は廃止し、1言語1ファイルに統合する。`core.json` の既定値を言語 JSON が上書きする。

旧配置（`src/toolchain/emit/<lang>/profiles/`）は互換として残すが、正本は `src/toolchain2/emit/profiles/` とする。

## 3. ロード順序

1. `src/toolchain2/emit/profiles/core.json`（全言語共通の既定値）
2. `src/toolchain2/emit/profiles/<target>.json`（言語固有の上書き）
3. CLI 上書き（必要時）

後勝ちマージを原則とする。`core.json` の既定値を言語 JSON が上書きし、CLI がさらに上書きする。`include` による分割ファイル参照は廃止。

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
    "module": "toolchain.emit.cpp.emitter.hooks_registry",
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
    "module": "toolchain.emit.cpp.emitter.hooks_registry",
    "factory": "build_cpp_hooks"
  }
}
```

`module` は言語固有側（例: `src/toolchain/emit/cpp/emitter/`）に配置し、`src/toolchain/emit/common/` へは置きません。

## 5. Hooks 仕様

`profile.hooks` は JSON で表現しにくい分岐のみ担当します。

selfhost 制約:
- hooks API は `dict[str, Any]` / `list[str]` / `str` / `bool` を中心に扱い、`callable` 型注釈に依存しません。
- `CodeEmitter` 側はフックを「辞書から取り出して呼ぶ」方式で扱い、型注釈由来の selfhost 変換詰まりを避けます。

- `on_emit_stmt(emitter, stmt)`:
  - `True` を返すと既定の文出力をスキップ
- `on_render_call(emitter, call_node, func_node, rendered_args, rendered_kwargs)`
- `on_render_binop(emitter, binop_node, left, right)`
- `on_render_expr_<kind>(emitter, kind, expr_node)`:
  - `render_expr` の kind 単位フック。`<kind>` は EAST kind を snake_case 化した名前を使う。
  - 例: `Name -> on_render_expr_name`, `IfExp -> on_render_expr_if_exp`, `ListComp -> on_render_expr_list_comp`

戻り値:
- `None`: 既定ロジック継続
- `str`: その文字列を採用

### 5.1 `render_expr` hook 優先順位

`render_expr` は次の順でフックを評価します。

1. kind 専用 hook: `on_render_expr_<kind>`
2. 汎用 kind hook: `on_render_expr_kind`
3. leaf hook: `on_render_expr_leaf`（`Name` / `Constant` / `Attribute`）
4. complex hook: `on_render_expr_complex`（`JoinedStr` / `Lambda` / `*Comp`）
5. 各言語 emitter の既定実装

この順序は C++ / Rust / C# / JavaScript で共通です。
TypeScript プレビューは `transpile_to_js()` 経由で JavaScript emitter を利用するため、同じ hook 順序を継承します。

### 5.2 実装位置（C++）

```text
src/toolchain/emit/cpp/emitter/hooks_registry.py
```

## 6. 妥当性ルール

- `schema_version` は必須（現行 `1`）。
- `language` は必須。
- `include` は相対パスのみ許可。
- 未知キーは警告（エラーにはしない）。
- 必須キー欠落は起動時エラー。

## 7. Lowering プロファイル（言語能力宣言）

EAST3 lowering はターゲット言語の能力に依存する。各言語は以下のプロファイルを `profile.json` の `lowering` セクションで宣言し、EAST3 言語別 lowering パス（`east3_lower_<lang>.py`）がこれを参照して言語に合った EAST3 形状を生成する。emitter は lowering 済みのノードを構文に写像するだけであり、lowering 判断を再実装しない。

### 7.1 lowering プロファイルの全スキーマ

```json
{
  "lowering": {
    "tuple_unpack_style": "multi_return",
    "container_covariance": false,
    "closure_style": "closure_syntax",
    "with_style": "defer",
    "property_style": "method_call",
    "swap_style": "multi_assign",
    "none_literal": "nil",
    "bool_literals": ["true", "false"],
    "self_keyword": "",
    "type_position": "postfix",
    "condition_parens": false,
    "block_braces": true,
    "stmt_terminator": "",
    "string_type_owned": true,
    "has_explicit_error_return": true
  }
}
```

### 7.2 `tuple_unpack_style`

入力 EAST3: `Assign(target=Tuple([Name("x"), Name("y")]), value=Call(...))`

| 値 | lowering が生成する EAST3 | emitter の出力例 |
|---|---|---|
| `"subscript"` | `_tmp = f(); x = _tmp[0]; y = _tmp[1]` — temp Assign + Subscript(Constant(0)), Subscript(Constant(1)) | Python: `_tmp = f(); x = _tmp[0]; y = _tmp[1]` |
| `"structured_binding"` | `TupleUnpack(targets=[x, y], value=f())` — 高レベルノードを維持 | C++: `auto [x, y] = f();` |
| `"pattern_match"` | `TupleUnpack(targets=[x, y], value=f())` — 同上 | Rust: `let (x, y) = f();` / Swift: `let (x, y) = f()` |
| `"multi_return"` | `MultiAssign(targets=[x, y], value=f())` — 多値返却専用ノード | Go: `x, y := f()` |
| `"individual_temps"` | `_t0 = rhs_elem_0; _t1 = rhs_elem_1; x = _t0; y = _t1` — tuple を経由しない | 汎用。3変数ローテーションにも対応 |

`TupleUnpack` ノード仕様:
```json
{
  "kind": "TupleUnpack",
  "targets": [{"kind": "Name", "id": "x"}, {"kind": "Name", "id": "y"}],
  "target_types": ["list[str]", "str"],
  "value": {"kind": "Call", "...": "..."},
  "declare": true
}
```

`MultiAssign` ノード仕様（Go 多値返却専用）:
```json
{
  "kind": "MultiAssign",
  "targets": [{"kind": "Name", "id": "x"}, {"kind": "Name", "id": "y"}],
  "target_types": ["list[str]", "str"],
  "value": {"kind": "Call", "...": "..."},
  "declare": true
}
```

関数の戻り値型との関係:
- `"multi_return"` を使う言語では、`tuple[A, B]` を返す関数は EAST3 の `FunctionDef.return_type` を `"multi_return[A, B]"` に正規化する。emitter は `func f() (A, B)` のように多値返却として出力する。
- `"structured_binding"` / `"pattern_match"` の言語では、戻り値型は `tuple[A, B]` のまま維持する。

swap との関係:
- 2要素 swap（`a, b = b, a`）は `Swap` ノードに最適化済み（§7.7 参照）。`tuple_unpack_style` は 3要素以上、または swap でない通常の tuple unpack に適用する。

### 7.3 `container_covariance`

入力 EAST3: `Call(func=Name("list"), args=[Name("params")])` where `params: list[str]`, result type: `list[JsonVal]`

| 値 | lowering が生成する EAST3 | emitter の出力例 |
|---|---|---|
| `true` | そのまま `Call(list, [params])` | TS: `[...params]` / Swift: `Array(params)` |
| `false` | `CovariantCopy(source=params, source_elem_type="str", target_elem_type="JsonVal")` — 要素ごとコピーノード | Go: `func() []any { r := make([]any, len(params)); for i, v := range params { r[i] = v }; return r }()` |

`CovariantCopy` ノード仕様:
```json
{
  "kind": "CovariantCopy",
  "source": {"kind": "Name", "id": "params"},
  "source_type": "list[str]",
  "source_elem_type": "str",
  "target_type": "list[JsonVal]",
  "target_elem_type": "JsonVal"
}
```

emitter は `CovariantCopy` を言語固有のコピーループに写像する:
- Go: `func() []any { ... }()` IIFE
- Rust: `params.iter().map(|v| v.into()).collect()`
- C++: `[&]() { vector<JsonVal> r; for (auto& v : params) r.push_back(v); return r; }()`
- Java: `new ArrayList<>(params)` （Java の generic erasure により実質不要だが、明示 cast が要る場合あり）

### 7.4 `closure_style`

入力 EAST3: `ClosureDef(name="inner", captures=[...], args=[...], body=[...])`

| 値 | emitter の出力例 |
|---|---|
| `"native_nested"` | JS: `function inner(args) { ... }` / TS: 同上 |
| `"closure_syntax"` | Go: `inner := func(args) RetType { ... }` / C++: `auto inner = [captures](args) -> RetType { ... };` / Rust: `let inner = \|args\| -> RetType { ... };` / Swift: `let inner: (Args) -> RetType = { args in ... }` / Kotlin: `val inner: (Args) -> RetType = { args -> ... }` / Java: ラムダまたは anonymous class |

captures の扱い:
- `"native_nested"` の言語: `captures` リストは無視（言語が自動キャプチャ）
- `"closure_syntax"` の言語: `captures` の `mode` に従う
  - C++: `readonly` → 値キャプチャ `[x]`、`mutable` → 参照キャプチャ `[&x]`
  - Go: 全て暗黙参照キャプチャ（`captures` は型検証のみに使用）
  - Rust: コンパイラが自動判定（`captures` は型検証のみに使用）
  - Java: effectively final 制約（`mutable` capture は配列ラッパーが必要 → lowering が `MutableCaptureWrapper` に展開）

### 7.5 `with_style`

入力 EAST3: `With(context_expr=Call(open, [path, "wb"]), var_name="f", body=[...])`

| 値 | emitter の出力 |
|---|---|
| `"raii"` | C++: `{ auto f = open(path, "wb"); ... }` （スコープ終了で自動解放） |
| `"try_with_resources"` | Java: `try (var f = open(path, "wb")) { ... }` |
| `"using"` | C#: `using (var f = open(path, "wb")) { ... }` |
| `"defer"` | Go: `f := open(path, "wb"); defer f.Close(); ...` / Swift: `let f = open(path, "wb"); defer { f.close() }; ...` |
| `"try_finally"` | JS: `const f = open(path, "wb"); try { ... } finally { f.close(); }` / Kotlin: 同構造 |

`var_name` が空の場合（`with open(path, "wb"):`）:
- `"raii"`: 一時変数に束縛（`{ auto _tmp = open(...); ... }`）
- `"defer"`: `defer` のみ emit、変数名は生成名
- `"try_finally"`: 同上

### 7.6 `property_style`

入力 EAST3: `Attribute(value=obj, attr="name", attribute_access_kind="property_getter")`

| 値 | emitter の出力 |
|---|---|
| `"field_access"` | `obj.name` — 括弧なし。C#: `obj.Name`、Kotlin: `obj.name`、Swift: `obj.name` |
| `"method_call"` | `obj.name()` — 括弧付き。Go: `obj.Name()`、Java: `obj.getName()`、C++: `obj.name()` |

`"method_call"` の場合の命名規則:
- Go: `attr` をアッパーキャメルに変換（`name` → `Name`）
- Java: `get` + アッパーキャメル（`name` → `getName`）
- C++ / Rust: そのまま（`name` → `name()`）

`attribute_access_kind != "property_getter"` の場合はこのプロファイルは適用されない（通常のフィールドアクセスまたはメソッド呼び出し）。

### 7.7 `swap_style`

入力 EAST3: `Swap(left=Name("a"), right=Name("b"))`

| 値 | emitter の出力 |
|---|---|
| `"std_swap"` | C++: `std::swap(a, b);` |
| `"multi_assign"` | Go: `a, b = b, a` / Python: `a, b = b, a` |
| `"mem_swap"` | Rust: `std::mem::swap(&mut a, &mut b);` |
| `"swap_func"` | Swift: `swap(&a, &b)` |
| `"temp_var"` | `tmp := a; a = b; b = tmp` — 汎用フォールバック |

### 7.8 `none_literal`

`None` の言語固有リテラル。

| 値 | 言語 |
|---|---|
| `"std::nullopt"` | C++（Optional 文脈） |
| `"nullptr"` | C++（ポインタ文脈） |
| `"nil"` | Go, Swift, Lua |
| `"None"` | Rust（Option 文脈） |
| `"null"` | Java, C#, Kotlin, TS, JS, Dart, PHP |
| `"nothing"` | Julia |

emitter は EAST3 の `Constant(value=None)` をこのリテラルに置換する。

### 7.9 `bool_literals`

`True` / `False` の言語固有リテラル。`[true_literal, false_literal]`。

| 値 | 言語 |
|---|---|
| `["true", "false"]` | C++, Go, Java, C#, Rust, Swift, Kotlin, JS, TS, Dart, PHP, Lua, Nim, Zig |
| `["True", "False"]` | Python, Nim（大文字始まり） |
| `["TRUE", "FALSE"]` | — |

### 7.10 `self_keyword`

メソッド内での自己参照キーワード。

| 値 | 言語 | 用途 |
|---|---|---|
| `"this"` | C++, Java, C#, Kotlin, JS, TS, Dart, PHP | `this->field` / `this.field` |
| `"self"` | Rust, Swift | `self.field` |
| `""` | Go | レシーバー変数名を使う（emitter が生成） |

Go の場合、emitter がクラス名の先頭小文字をレシーバー名として生成する（例: `Circle` → `func (c *Circle) draw()`）。

### 7.11 `type_position`

変数宣言での型の位置。

| 値 | 構文 | 言語 |
|---|---|---|
| `"prefix"` | `Type name = value` | C++, Java, C#, Dart |
| `"postfix_colon"` | `name: Type = value` | Rust, Swift, Kotlin, TS |
| `"postfix_space"` | `name Type = value` | Go |
| `"inferred"` | `name := value` / `var name = value` | Go（短縮）、Kotlin（`val`）、Swift（`let`） |

emitter は `VarDecl` / `Assign(declare=true)` ノードに対してこのスタイルで出力する。`type_position` が `"inferred"` の場合でも型注釈が必要な場面（空コンテナ等）では `"postfix_colon"` / `"postfix_space"` にフォールバックする。

### 7.12 `condition_parens`

`if` / `while` の条件式に括弧が必要か。

| 値 | 構文 | 言語 |
|---|---|---|
| `true` | `if (cond) {` | C++, Java, C#, Dart |
| `false` | `if cond {` | Go, Rust, Swift, Kotlin |

### 7.13 `block_braces`

ブロックの囲み方。

| 値 | 構文 | 言語 |
|---|---|---|
| `"braces"` | `{ ... }` | C++, Go, Java, C#, Rust, Swift, Kotlin, JS, TS, Dart, PHP |
| `"end"` | `... end` | Lua, Ruby, Nim（`do...end` 系） |
| `"indent"` | インデント | — （Pytra のターゲットにはない） |

### 7.14 `stmt_terminator`

文末の記号。

| 値 | 言語 |
|---|---|
| `";"` | C++, Java, C#, Rust, Swift, Kotlin, JS, TS, Dart, PHP, Zig |
| `""` | Go, Lua, Ruby, Nim, Julia, Scala |

### 7.15 `string_type_owned`

文字列型がデフォルトで所有型か参照型か。

| 値 | 説明 | 言語 |
|---|---|---|
| `true` | 文字列リテラルはそのまま所有型 | Go, Java, C#, Kotlin, Swift, JS, TS, Dart |
| `false` | 文字列リテラルは参照型、所有型への変換が必要 | Rust (`&str` → `String::from(...)`), C++ (`const char*` → `str(...)`) |

`false` の場合、emitter は文字列リテラルの Constant ノードに対して所有型変換を出力する。

### 7.16 `has_explicit_error_return`

エラー処理が例外か明示的戻り値か。

| 値 | 説明 | 言語 |
|---|---|---|
| `false` | 例外（`throw` / `raise`） | C++, Java, C#, Kotlin, Swift, JS, TS, Dart, PHP, Ruby, Nim |
| `true` | 明示的エラー戻り値 | Go (`val, err := f()`), Rust (`Result<T, E>`) |

`true` の場合、EAST3 の `Raise` / `Try` ノードは lowering で `if err != nil { return ..., err }` パターンに展開される。

### 7.17 全言語のプロファイル一覧

表が大きいため、2分割で記載する。

**グループ A: C++, Go, Rust, Java, C#, Kotlin, Swift, JS, TS**

| 項目 | C++ | Go | Rust | Java | C# | Kotlin | Swift | JS | TS |
|---|---|---|---|---|---|---|---|---|---|
| tuple_unpack_style | structured_binding | multi_return | pattern_match | individual_temps | individual_temps | pattern_match | pattern_match | subscript | subscript |
| container_covariance | false | false | false | false | false | true | true | true | true |
| closure_style | closure_syntax | closure_syntax | closure_syntax | closure_syntax | closure_syntax | closure_syntax | closure_syntax | native_nested | native_nested |
| with_style | raii | defer | raii | try_with_resources | using | try_finally | defer | try_finally | try_finally |
| property_style | method_call | method_call | method_call | method_call | field_access | field_access | field_access | field_access | field_access |
| swap_style | std_swap | multi_assign | mem_swap | temp_var | temp_var | temp_var | swap_func | temp_var | temp_var |
| none_literal | std::nullopt | nil | None | null | null | null | nil | null | null |
| bool_literals | true/false | true/false | true/false | true/false | true/false | true/false | true/false | true/false | true/false |
| self_keyword | this | (receiver) | self | this | this | this | self | this | this |
| type_position | prefix | postfix_space | postfix_colon | prefix | prefix | postfix_colon | postfix_colon | prefix | postfix_colon |
| condition_parens | true | false | false | true | true | false | false | true | true |
| block_braces | braces | braces | braces | braces | braces | braces | braces | braces | braces |
| stmt_terminator | ; | (none) | ; | ; | ; | (none) | (none) | ; | ; |
| string_type_owned | false | true | false | true | true | true | true | true | true |
| has_explicit_error_return | false | true | true | false | false | false | false | false | false |

**グループ B: Dart, Lua, Ruby, PHP, Nim, Scala, Julia, PowerShell, Zig**

| 項目 | Dart | Lua | Ruby | PHP | Nim | Scala | Julia | PowerShell | Zig |
|---|---|---|---|---|---|---|---|---|---|
| tuple_unpack_style | individual_temps | individual_temps | pattern_match | individual_temps | pattern_match | pattern_match | pattern_match | individual_temps | pattern_match |
| container_covariance | true | true | true | true | false | true | true | true | false |
| closure_style | closure_syntax | closure_syntax | closure_syntax | closure_syntax | closure_syntax | closure_syntax | native_nested | closure_syntax | closure_syntax |
| with_style | try_finally | try_finally | try_finally | try_finally | try_finally | try_with_resources | try_finally | try_finally | defer |
| property_style | field_access | method_call | method_call | method_call | field_access | field_access | field_access | field_access | method_call |
| swap_style | temp_var | temp_var | multi_assign | temp_var | temp_var | temp_var | temp_var | temp_var | temp_var |
| none_literal | null | nil | nil | null | nil | null | nothing | $null | null |
| bool_literals | true/false | true/false | true/false | true/false | true/false | true/false | true/false | $true/$false | true/false |
| self_keyword | this | self | self | $this | (implicit) | this | (implicit) | $this | self |
| type_position | prefix | (dynamic) | (dynamic) | (dynamic) | postfix_colon | postfix_colon | postfix_colon | (dynamic) | postfix_colon |
| condition_parens | true | false | false | true | false | true | false | true | false |
| block_braces | braces | end | end | braces | indent | braces | end | braces | braces |
| stmt_terminator | ; | (none) | (none) | ; | (none) | (none) | (none) | (none) | ; |
| string_type_owned | true | true | true | true | true | true | true | true | false |
| has_explicit_error_return | false | false | false | false | false | false | false | false | true |

## 8. 共通 Renderer（CommonRenderer）

### 8.1 目的

各言語の emitter が EAST3 ノード走査ロジックを個別に実装しているが、大部分は構造的に同一である。共通 Renderer を導入し、emitter を「構文テーブル + 言語固有 override」だけに縮退させる。

### 8.2 設計

```
CommonRenderer（共通基底）
  ├── emit_if()      → syntax テーブルで構文生成
  ├── emit_while()   → 同上
  ├── emit_binop()   → operator_map で演算子置換
  ├── emit_call()    → 引数を emit して結合
  ├── emit_return()  → "return" + 式
  ├── emit_var_decl() → type_position に応じて前置/後置
  └── ...

CppEmitter(CommonRenderer)
  └── emit_class_def() を override（C++ 固有の構文）

GoEmitter(CommonRenderer)
  └── emit_func_decl() を override（Go 固有の戻り値位置）
```

### 8.3 CommonRenderer が担当するノード

以下のノードは言語間で構造が共通であり、CommonRenderer がプロファイルを参照して生成する。emitter は override 不要。

| ノード | 共通ロジック |
|---|---|
| `If` / `While` | 条件式 + ブロック（`block_open`/`block_close` で構文差を吸収） |
| `BinOp` / `Compare` / `UnaryOp` | `operator_map` で演算子を置換 |
| `BoolOp` | `And` → `&&`、`Or` → `\|\|`（`operator_map` で差し替え） |
| `Call` | 関数名 + 括弧 + 引数カンマ区切り |
| `Return` / `Break` / `Continue` | キーワード + 式（あれば） |
| `Constant` | 型に応じたリテラル書式 |
| `Assign` / `AugAssign` | target = value（`stmt_terminator` で文末を制御） |

### 8.4 言語固有 override が必要なノード

以下のノードは言語間で構造が異なるため、各 emitter が override する。

| ノード | 言語間差異の例 |
|---|---|
| `FunctionDef` | 戻り値位置（前置 vs 後置）、`func` キーワードの有無 |
| `ClassDef` | 継承構文、コンストラクタ、フィールド宣言 |
| `For` / `ForCore` | range-for 構文、iterator 構文 |
| `VarDecl` | `auto` / `:=` / `let` / `var` / 型推論の有無 |
| `With` | `lowering.with_style` による分岐 |
| `ClosureDef` | `lowering.closure_style` による分岐 |

### 8.5 効果

- 新言語の emitter が **プロファイル JSON + 数個の override** だけで書ける
- バグ修正が CommonRenderer の 1 箇所で全言語に反映される
- emitter ごとのコード量が 50〜70% 削減される
- EAST3 ノード走査の重複が解消される

## 9. 移行方針

1. C++ から先行移行する。
2. `py2cpp.py` 直書きマップを順次削除する。
3. `BaseEmitter` を `CodeEmitter` へ改名し、`BaseEmitter = CodeEmitter` で互換維持する。
4. lowering プロファイルを C++ / Go から先行導入し、tuple unpack / with / closure の lowering を共通化する。
5. CommonRenderer を導入し、C++ / Go emitter を CommonRenderer + override 構成に移行する。
