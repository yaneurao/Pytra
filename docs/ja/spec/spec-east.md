# EAST仕様（実装準拠）

<a href="../../en/spec/spec-east.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


この文書は `src/toolchain/compiler/east.py` / `src/toolchain/compiler/east_parts/` の現実装に合わせた EAST 仕様の統合正本である。

統合方針:
- 現行実装準拠の EAST2 仕様と、EAST1/EAST2/EAST3 三段構成の責務仕様をこの文書へ統合する。
- 旧ドキュメント（`spec-east123.md`, `spec-east123-migration.md`, `spec-east1-build.md`）は `docs/ja/spec/archive/` に退役移管する。
- 連結段（`type_id` 決定、manifest、中間ファイル再開）の詳細は [spec-linker.md](./spec-linker.md) を参照する。

## 1. 目的

- EAST(Extended AST) は Python AST から、言語非依存の意味注釈付き JSON を生成する中間表現である。
- 型解決、cast情報、引数 readonly/mutable、mainガード分離を前段で確定させる。
- Pythonにはastという抽象構文木を扱うモジュールがあるが、これだと元のソースコードのコメントなどを残してトランスパイルできないのでEASTという表現を考え、そしてこのためのparserをPythonで実装する。


## 2. 入出力

### 2.1 入力

- UTF-8 の Python ソースファイル 1 つ。

### 2.2 出力形式

- 成功時

```json
{
  "ok": true,
  "east": { "...": "..." }
}
```

- 失敗時

```json
{
  "ok": false,
  "error": {
    "kind": "inference_failure | unsupported_syntax | semantic_conflict",
    "message": "...",
    "source_span": {
      "lineno": 1,
      "col": 0,
      "end_lineno": 1,
      "end_col": 5
    },
    "hint": "..."
  }
}
```

### 2.3 CLI

- `python src/toolchain/compiler/east.py <input.py> [-o output.json] [--pretty] [--human-output output.cpp]`
- `--pretty`: 整形 JSON を出力。
- `--human-output`: C++風の人間可読ビューを出力。
- `python3 src/py2x.py <input.py|east.json> --target cpp [-o output.cpp]`: EASTベースの C++ 生成器。

## 3. トップレベルEAST構造

`east` オブジェクトは以下を持つ。

- `kind`: 常に `Module`
- `east_stage`: 常に `2`（`EAST2`）
- `schema_version`: 整数（現行 `1`）
- `source_path`: 入力パス
- `source_span`: モジュール span
- `body`: 通常のトップレベル文
- `main_guard_body`: `if __name__ == "__main__":` の本体
- `renamed_symbols`: rename マップ
- `meta.import_bindings`: import 正本（`ImportBinding[]`）
- `meta.qualified_symbol_refs`: `from-import` の解決済み参照（`QualifiedSymbolRef[]`）
- `meta.import_modules`: `import module [as alias]` の束縛情報（`alias -> module`）
- `meta.import_symbols`: `from module import symbol [as alias]` の束縛情報（`alias -> {module,name}`）
- `meta.dispatch_mode`: `native | type_id`（コンパイル開始時に確定し、`EAST2 -> EAST3` で意味適用する）

注:
- `meta.dispatch_mode` の意味論適用点は `EAST2 -> EAST3` の 1 回のみで、backend/hook で再判断しない。
- 詳細契約は本書と `docs/ja/spec/spec-linker.md` を正本とする。
- linked-program 後の `EAST3` は、引き続き `kind=Module` / `east_stage=3` を維持したまま、`meta.linked_program_v1` を追加で持ち得る。これは新しい EAST stage ではなく、`EAST3 -> linker -> linked EAST3` の materialization として扱う。
- linked-program optimizer が helper を synthetic module として生成する場合も、`kind=Module` / `east_stage=3` を維持し、追加情報は `meta.synthetic_helper_v1` として保持する。helper 専用の別 EAST stage は増やさない。

`ImportBinding` は次を持つ。

- `module_id`
- `export_name`（`import M` では空文字）
- `local_name`
- `binding_kind`（`module` / `symbol`）
- `runtime_module_id`（任意。import 先 symbol の runtime 所属 module）
- `runtime_symbol`（任意。import 先 symbol の runtime symbol）
- `source_file`
- `source_line`

`QualifiedSymbolRef` は次を持つ。

- `module_id`
- `symbol`
- `local_name`
- `runtime_module_id`（任意）
- `runtime_symbol`（任意）

## 4. 構文正規化

- `if __name__ == "__main__":` は `main_guard_body` に分離。
- 次は rename 対象。
- 重複定義名
- 予約名 `main`, `py_main`, `__pytra_main`
- `FunctionDef`/`ClassDef` は `name`（rename後）と `original_name` を持つ。
- `for ... in range(...)` は `ForRange` に正規化され、`start/stop/step/range_mode` を保持。
- `range(...)` は EAST 構築段階で専用表現へ lower し、後段（`py2x.py --target cpp` など）へ生の `Call(Name("range"), ...)` を渡さない。
  - つまり、後段エミッタは Python 組み込み `range` の意味解釈を持たず、EAST の正規化済みノードのみを処理する。
- `for` 以外の式位置 `range(...)` は `RangeExpr` へ lower する（`ListComp` 含む）。
- `from __future__ import annotations` は frontend 専用ディレクティブとして受理し、EAST ノード/`meta.import_*` には出力しない。
- `__future__` の他機能や `from __future__ import *` は `unsupported_syntax` として fail-closed で拒否する。

## 5. ノード共通属性

式ノード（`_expr`）は以下を持つ。

- `kind`, `source_span`, `resolved_type`, `type_expr`, `borrow_kind`, `casts`, `repr`
- `type_expr` は構造化型表現であり、存在する場合は `resolved_type` より優先する。
- `resolved_type` は migration 互換の推論済み型文字列 mirror。
- `borrow_kind` は `value | readonly_ref | mutable_ref`（`move` は未使用）。
- 主要式は構造化子ノードを持つ（`left/right`, `args`, `elements`, `entries` など）。

関数ノードは以下を持つ。

- `arg_types`, `arg_type_exprs`, `return_type`, `return_type_expr`, `arg_usage`, `renamed_symbols`
- `arg_type_exprs` / `return_type_expr` は `arg_types` / `return_type` の構造化正本。
- `decorators`（raw decorator 文字列の列）
- `meta.runtime_abi_v1`（任意。`@abi` の canonical metadata）
- `meta.template_v1`（任意。`@template` の canonical metadata）
- `meta.template_specialization_v1`（任意。linked-program が materialize した specialization metadata）

代入文ノード（`Assign`, `AnnAssign`）は以下を持ち得る。

- `meta.extern_var_v1`（任意。ambient global extern variable の canonical metadata）

クラスノードは以下を持ち得る。

- `bases`, `decorators`
- `meta.nominal_adt_v1`（任意。nominal ADT family / variant の canonical metadata）

`FunctionDef.meta.runtime_abi_v1` の規則:

- `schema_version: 1`
- `args: {param_name: mode}`
- `ret: mode`
- canonical mode は `default`, `value`, `value_mut`
- `ret` に許可される canonical mode は `default` または `value`
- source surface で legacy `value_readonly` を受理しても、metadata では `value` へ正規化する
- raw `decorators` は Python surface の保存用であり、backend / linker の正本は `meta.runtime_abi_v1`
- linked-program 後もこの function-level metadata は保持し、`meta.linked_program_v1` で置き換えない

`FunctionDef.meta.template_v1` の規則:

- `schema_version: 1`
- `params: [template_param_name, ...]`
- `scope: "runtime_helper"`
- `instantiation_mode: "linked_implicit"`
- `params` は宣言順を保持し、空配列を許可しない
- raw `decorators` は Python surface の保存用であり、parser / linker / backend の正本は `meta.template_v1`
- linked-program 後もこの function-level metadata は保持し、`meta.linked_program_v1` で置き換えない
- v1 では `@instantiate(...)` を materialize しないため、実体化情報はここへ持たない
- `template_v1` は「宣言 metadata」であって、specialization seed や materialized helper 一覧を保持する場所ではない。これらは linked-program optimizer が callsite concrete type から決定する。
- backend は raw decorator や surface syntax から template param を再抽出してはならず、linked module に残った `meta.template_v1` と linker が確定した summary だけを参照する。
- `TypeVar` 注釈だけでは `meta.template_v1` を作らない

`FunctionDef.meta.template_specialization_v1` の規則:

- linked-program optimizer が implicit specialization を materialize した clone のみに付与してよい
- canonical shape は `schema_version: 1`, `origin_symbol: <module_id::name>`, `type_args: [concrete_type, ...]`
- `template_specialization_v1` は `template_v1` の代替ではなく、materialized clone の provenance を示す補助 metadata とする
- backend / ProgramWriter は raw decorator ではなく、この metadata と linker summary を見て specialized helper を扱う

`Assign` / `AnnAssign`.meta.extern_var_v1 の規則:

- `schema_version: 1`
- `symbol: str`
- `same_name: 0 | 1`
- v1 では top-level `name: Any = extern()` / `name: Any = extern("symbol")` にだけ付与してよい
- `extern()` は `symbol == target_name` かつ `same_name == 1`
- `extern("symbol")` は `symbol == <literal>`、`same_name` は target 名との一致で決まる
- `extern(expr)` host fallback / runtime hook では付与してはならない
- backend は raw initializer の `extern(...)` を再解釈せず、ambient-global 判定の正本として `meta.extern_var_v1` を使う

`ClassDef`.meta.nominal_adt_v1 の規則:

- `schema_version: 1`
- `role: "family" | "variant"`
- `family_name: str`
- `surface_phase: "declaration_v1"`
- family の場合:
  - `closed: 1`
  - `variant_name` / `payload_style` を持ってはならない
- variant の場合:
  - `variant_name: str`
  - `payload_style: "unit" | "dataclass"`
  - family 以外の base class を metadata にエンコードしてはならない
- raw `decorators` / `bases` は Python surface 保存用であり、nominal ADT 判定の正本は `meta.nominal_adt_v1`
- v1 では top-level family / top-level variant だけを正規 surface とし、nested variant や namespace sugar は metadata に落としてはならない
- constructor は dedicated node を増やさず、variant class への通常の `Call` を正本とする

### 5.1 `leading_trivia` による C++ パススルー記法

- EAST では、パススルーは新ノードを増やさず、既存の `leading_trivia`（`kind: "comment"`）で保持する。
- 解釈対象コメント:
  - `# Pytra::cpp <C++行>`
  - `# Pytra::cpp: <C++行>`
  - `# Pytra::pass <C++行>`
  - `# Pytra::pass: <C++行>`
  - `# Pytra::cpp begin` ... `# Pytra::cpp end`
  - `# Pytra::pass begin` ... `# Pytra::pass end`
- 出力ルール（C++ エミッタ）:
  - directive コメントは通常コメント化（`// ...`）せず、C++ 行としてそのまま出力する。
- `begin/end` ブロック中の通常コメントは、`#` を除いた本文を C++ 行として順序どおり出力する。
  - 出力位置は `leading_trivia` が付いている文の直前で、文のインデントに合わせる。
  - `blank` trivia は従来どおり空行として維持する。
  - 同一 `leading_trivia` 内の複数 directive は記述順に連結して出力する。
- 優先順位:
  - `leading_trivia` の directive 解釈が最優先。
- 既存の docstring コメント変換（`"""..."""` -> `/* ... */`）とは独立で、互いに上書きしない。

### 5.2 nominal ADT / pattern / `match` 契約（v1）

- Stage A の declaration surface は `ClassDef.meta.nominal_adt_v1` を正本とし、family / variant は既存 `ClassDef` node で表す。
- Stage B 以降の `match/case` 導入では、statement node と pattern helper node を次で表す。
  - `Match`
    - `subject: _expr`
    - `cases: MatchCase[]`
    - `source_span`
    - `repr`（任意）
  - `MatchCase`
    - `pattern: VariantPattern | PatternBind | PatternWildcard`
    - `guard: null`（v1 では guard pattern を許可しないため常に `null`）
    - `body: stmt[]`
    - `source_span`
  - `VariantPattern`
    - `family_name: str`
    - `variant_name: str`
    - `subpatterns: (PatternBind | PatternWildcard)[]`
    - `source_span`
  - `PatternBind`
    - `name: str`
    - `source_span`
  - `PatternWildcard`
    - `source_span`
- v1 pattern surface は「variant pattern + payload bind + wildcard `_`」に限定する。
- literal pattern、nested pattern、guard pattern、expression-form `match` は v1 の node contract に含めない。
- `Match` / pattern node を受け取った backend は dedicated lowering lane を持つことを前提とし、`object` fallback や raw method-name 再解釈に落としてはならない。
- `Match` は static check のために `meta.match_analysis_v1` を持ってよい。
  - `schema_version: 1`
  - `family_name: str`
  - `coverage_kind: "exhaustive" | "wildcard_terminal" | "partial" | "invalid"`
  - `covered_variants: str[]`
  - `uncovered_variants: str[]`
  - `duplicate_case_indexes: int[]`
  - `unreachable_case_indexes: int[]`
  - `match_analysis_v1` は parser surface の代替ではなく、validator / lowering が確定した coverage summary を保持する補助 metadata とする。
- v1 の static check は closed nominal ADT family にだけ適用する。
  - exhaustive 条件は「family の全 variant を 1 回ずつ列挙する」または「末尾の `PatternWildcard` が残余全体を受ける」のどちらかとする。
  - duplicate pattern は同じ `variant_name` の再列挙、または 2 個目以降の `PatternWildcard` を指す。
  - unreachable branch は wildcard で coverage が閉じた後ろ、または同一 variant が既に coverage 済みの後ろに現れる `MatchCase` を指す。

## 6. 型システム

### 6.1 正規型

- 整数型: `int8`, `uint8`, `int16`, `uint16`, `int32`, `uint32`, `int64`, `uint64`
- 浮動小数型: `float32`, `float64`
- 基本型: `bool`, `str`, `None`
- 合成型: `list[T]`, `set[T]`, `dict[K,V]`, `tuple[T1,...]`
- 拡張型: `Path`, `Exception`, クラス名
- 補助型: `unknown`, `module`, `callable[float64]`

### 6.2 注釈正規化

- `int` は `int64` に正規化。
- `float` は `float64` に正規化。
- `byte` は `uint8` に正規化（1文字/1byte用途の注釈エイリアス）。
- `float32/float64` はそのまま保持。
- `any` / `object` は `Any` と同義に扱う。
- C++ ランタイムでの具体表現（`object`, `None`, boxing/unboxing）は [ランタイム仕様](./spec-runtime.md) の `Any` / `object` 表現方針を参照。
- `bytes` / `bytearray` は `list[uint8]` に正規化。
- `pathlib.Path` は `Path` に正規化。
- C++ ランタイムの `str` / `list` / `dict` / `set` / `bytes` / `bytearray` は、STL 継承ではなく wrapper（composition）として実装する。

### 6.3 `TypeExpr` schema（構造化型表現）

`type_expr` は backend 非依存の構造化型表現とし、少なくとも次の kind を持つ。

- `NamedType`
  - `name: str`
  - 例: `int64`, `float64`, `str`, `Path`
- `GenericType`
  - `base: str`
  - `args: TypeExpr[]`
  - 例: `list[T]`, `dict[K,V]`, `tuple[T1,T2]`, `callable[float64]`
- `OptionalType`
  - `inner: TypeExpr`
  - `T | None` の正規形。`UnionType` で表してはならない。
- `UnionType`
  - `options: TypeExpr[]`
  - `union_mode: general | dynamic`
  - `general` は open な一般 union、`dynamic` は `Any/object/unknown` を含む dynamic union を表す。
- `DynamicType`
  - `name: Any | object | unknown`
  - open-world dynamic carrier を表す。
- `NominalAdtType`
  - `name: str`
  - `adt_family: str`（任意。例: `json`）
  - `variant_domain: str`（任意。例: `closed`）
  - `JsonValue` のような closed nominal ADT を表す。

補足:

- `bytes` / `bytearray` は従来どおり `list[uint8]` へ正規化してよく、独立 kind を必須にしない。
- exact JSON field 名は implementation に合わせて snake_case か camelCase に統一してよいが、意味論は上記 kind/field を満たすこと。
- annotation を直接持つ node は、既存の文字列 field に対応する `*_type_expr` field を持ってよい。

### 6.4 union 3分類と `resolved_type` mirror の主従

必須ルール:

- `T | None` は常に `OptionalType(inner=T)` に正規化し、`UnionType(options=[T, None])` のまま残してはならない。
- `Any/object/unknown` を含む union は `UnionType(union_mode=dynamic)` として扱い、general union と同じ lowering 規則で扱ってはならない。
- `JsonValue` / `JsonObj` / `JsonArr` のような JSON decode-first surface は general union ではなく `NominalAdtType` として扱う。
- `resolved_type`, `arg_types`, `return_type` はすべて `type_expr`, `arg_type_exprs`, `return_type_expr` から導出される mirror に格下げする。
- `type_expr` と `resolved_type` が両方ある場合、正本は常に `type_expr` である。矛盾は `semantic_conflict` として fail-closed にする。
- migration 中に legacy node が `resolved_type` だけを持つことは許容してよいが、`EAST2` 正本・`EAST3` 正本・validator・backend contract を追加するときは `type_expr` を優先入力にしなければならない。

例:

- `int | None` -> `OptionalType(NamedType("int64"))`
- `int | bool` -> `UnionType(union_mode="general", options=[NamedType("int64"), NamedType("bool")])`
- `int | Any` -> `UnionType(union_mode="dynamic", options=[NamedType("int64"), DynamicType("Any")])`
- `JsonValue` -> `NominalAdtType(name="JsonValue", adt_family="json", variant_domain="closed")`

### 6.5 `JsonValue` nominal closed ADT lane

`JsonValue` / `JsonObj` / `JsonArr` は、一般 union でも `object` fallback でもなく、JSON 専用の nominal closed ADT lane として扱う。

必須ルール:

- `json.loads(...)` の型は `NominalAdtType(name="JsonValue", adt_family="json", variant_domain="closed")` とする。
- `json.loads_obj(...)` / `json.loads_arr(...)` はそれぞれ `OptionalType(NominalAdtType("JsonObj"))` / `OptionalType(NominalAdtType("JsonArr"))` を返す。
- `JsonValue.as_*`, `JsonObj.get_*`, `JsonArr.get_*` は general-purpose cast ではなく、nominal ADT 向け decode / narrowing operation として扱う。
- `JsonValue` lane を `UnionType(union_mode=general|dynamic)` へ展開してはならない。

`EAST2 -> EAST3` で固定する resolved semantic tag（canonical）:

- `json.loads`
- `json.loads_obj`
- `json.loads_arr`
- `json.value.as_obj`
- `json.value.as_arr`
- `json.value.as_str`
- `json.value.as_int`
- `json.value.as_float`
- `json.value.as_bool`
- `json.obj.get`
- `json.obj.get_obj`
- `json.obj.get_arr`
- `json.obj.get_str`
- `json.obj.get_int`
- `json.obj.get_float`
- `json.obj.get_bool`
- `json.arr.get`
- `json.arr.get_obj`
- `json.arr.get_arr`
- `json.arr.get_str`
- `json.arr.get_int`
- `json.arr.get_float`
- `json.arr.get_bool`

責務境界:

- frontend / lowering は raw `json.loads` / `as_*` / `get_*` surface を上記 semantic tag か等価の dedicated IR category へ正規化する責務を持つ。
- backend / hook は raw callee 名・attribute 名・receiver 型文字列から JSON decode semantics を再解釈してはならない。
- validator は `JsonValue` nominal lane に対して `type_expr` と semantic tag の整合を検証し、`JsonValue` を general union として emit しようとする経路を `semantic_conflict` または `unsupported_syntax` で止める。
- target が `JsonValue` nominal carrier または decode op 写像をまだ持たない場合は fail-closed にし、`object` / `String` / `PyAny` へ黙って退化させてはならない。

## 7. 型推論ルール

- `Name`: 型環境から解決。未解決は `inference_failure`。
- `Constant`:
- 整数リテラルは `int64`
- 実数リテラルは `float64`, 真偽 `bool`, 文字列 `str`, `None`
- `List/Set/Dict`:
- 非空は要素型単一化で推論
- 空は通常 `inference_failure`
- ただし `AnnAssign` で注釈付き空コンテナは注釈型を採用
- `Tuple`: `tuple[...]` を構成。
- `BinOp`:
- 数値演算 `+ - * % // /` を推論
- 混在数値は `float32/float64` を含む型昇格を行い `casts` を付与
- `Path / str` は `Path`
- `str * int`, `list[T] * int` をサポート
- ビット演算 `& | ^ << >>` は整数型として推論
  - 注: `%` の Python/C++ 差異は EAST では吸収しない。
  - EAST は `%` を演算子として保持し、生成器側が `--mod-mode`（`native` / `python`）に応じて出力を切り替える。
- `Subscript`:
- `list[T][i] -> T`
- `dict[K,V][k] -> V`
- `str[i] -> str`
- `list/str` スライスは同型
  - EAST 自体は `Subscript`/`Slice` を保持し、`str-index-mode` / `str-slice-mode` の意味論は生成器側で適用する。
  - 現行 C++ 生成器では `byte` / `native` を実装済み、`codepoint` は未実装。
- `Call`:
- 既知: `int`, `float`, `bool`, `str`, `bytes`, `bytearray`, `len`, `range`, `min`, `max`, `round`, `print`, `write_rgb_png`, `save_gif`, `grayscale_palette`, `perf_counter`, `Path`, `Exception`, `RuntimeError`
- `float(...)`, `round(...)`, `perf_counter()`, `math.*` 主要関数は `float64`
- `bytes(...)` / `bytearray(...)` は `list[uint8]`
- クラスコンストラクタ/メソッドは事前収集した型情報で推論
- `ListComp`: 単一ジェネレータのみ対応
- `BoolOp` (`or`/`and`) は EAST 上では `kind: BoolOp` として保持する。
  - C++ 生成時に、期待型が `bool` のときは真偽演算（`&&`/`||`）として出力する。
  - 期待型が `bool` 以外のときは Python の値選択式として出力する。
    - `a or b` -> `truthy(a) ? a : b`
    - `a and b` -> `truthy(a) ? b : a`
  - 値選択の判定・出力は `src/py2x.py` 側で行い、EAST では追加ノードへ lower しない。

`range` について:

- 入力AST上で `Call(Name("range"), ...)` が現れても、最終EASTでは専用ノード（例: `ForRange` / `RangeExpr` 等）へ変換し、直接の `Call` として残さない。
- `range` のまま残るケースは EAST 構築不備として扱い、後段で暗黙救済しない。

`lowered_kind: BuiltinCall` について:

- EAST は `runtime_call` を付与して後段実装の分岐を削減する。
- 実装済みの主要 runtime_call 例:
  - `py_print`, `py_len`, `py_to_string`, `static_cast`
  - `py_min`, `py_max`, `perf_counter`
  - `list.append`, `list.extend`, `list.pop`, `list.clear`, `list.reverse`, `list.sort`
  - `set.add`, `set.discard`, `set.remove`, `set.clear`
  - `write_rgb_png`, `save_gif`, `grayscale_palette`
  - `py_isdigit`, `py_isalpha`

`runtime_module_id` / `runtime_symbol` / `runtime_call` の責務境界（必須）:

- `runtime_module_id`, `runtime_symbol`, `runtime_call`, `resolved_runtime_call`, `resolved_runtime_source`, `semantic_tag` は EAST3 の正本情報として扱う。
- backend/emitter はこの解決済み情報を描画するだけに限定し、関数名・モジュール名の再解決をしない。
- EAST3 で表現されていない情報が必要になった場合は、まず EAST3 スキーマを拡張し、スキーマ側へ情報を載せる。
- `runtime_module_id` / `runtime_symbol` は target 非依存であり、`runtime/cpp/std/time.gen.h` のような target 固有 path を保持しない。
- target ごとの include path / compile source / companion は `tools/runtime_symbol_index.json` と backend が導出する。

禁止事項:

- emitter や frontends/sig registry に `if runtime_call == "perf_counter"` のような個別シンボル直書き分岐を置くこと。
- emitter や frontends/sig registry に `py_assert_*` / `json.loads` / `write_rgb_png` 等の runtime dispatch 用テーブルを埋めること。
- 「EAST3では不足している」という理由で、呼び出し解決ルールを backend 側へ持ち込むこと。
- target 固有 file path を EAST3 に埋めること。

EAST3 -> backend の解決済み呼び出し契約（固定）:

- 対象ノード:
  - `Call`
  - `Attribute`（`Path.parent/name/stem` 等の属性アクセスを含む）
- backend が参照してよい解決済み属性:
  - `runtime_module_id`
  - `runtime_symbol`
  - `semantic_tag`
  - `runtime_call`
  - `resolved_runtime_call`
  - `resolved_runtime_source`
  - `resolved_type`
- 解決優先順位:
  1. `runtime_module_id + runtime_symbol`
  2. `runtime_call`（移行互換）
  3. `resolved_runtime_call`（`runtime_call` が空の場合）
  4. 上記がすべて空で `semantic_tag` が `stdlib.*` のときは fail-closed（暗黙フォールバック禁止）
- `resolved_runtime_source` 契約:
  - `import_symbol`: `from ... import ...` 経由で解決
  - `module_attr`: `module.symbol` 経由で解決
  - （後方互換として）`runtime_call` / `resolved_runtime_call` の文字列を返す実装は許容するが、新規実装では `import_symbol` / `module_attr` を優先する。
- backend API 制約:
  - emitter は `Call/Attribute` の生 `callee/owner/attr` 名で stdlib/runtime の意味解釈をしない。
  - emitter の runtime-call 描画 API は「解決済み属性を入力に受ける」形に限定し、生 AST ノード依存の再解決ロジックを持たない。
  - `resolved_type` を使った型選択は許可するが、モジュール名・関数名の逆引きは許可しない。

運用上の強制（CI）:

- `python3 tools/check_emitter_runtimecall_guardrails.py`
  - non-C++ emitter の runtime/stdlib 直書き分岐増分を fail にする。
- `python3 tools/check_emitter_forbidden_runtime_symbols.py`
  - emitter への runtime 実装シンボル（`__pytra_write_rgb_png` 等）の再混入増分を fail にする。
- `python3 tools/check_noncpp_east3_contract.py`
  - 言語別 smoke の責務境界コメントや EAST3 契約逸脱を静的検知する。

`dict[str, Any]` の `.get(...).items()` について:

- C++ 生成時は `dict[str, object]` を前提に、`Dict`/`List` リテラル値を `make_object(...)` で再帰変換して初期化する。
- `.get(..., {})` で辞書既定値を与える場合は `dict[str, object]` へ正規化して扱う。

## 8. cast仕様

数値昇格時に `casts` を出力する。

```json
{
  "on": "left | right | body | orelse",
  "from": "int64",
  "to": "float32 | float64",
  "reason": "numeric_promotion | ifexp_numeric_promotion"
}
```

## 9. 引数再代入判定（`arg_usage`）

`FunctionDef` ごとに `arg_usage` を付与する。

- 値は `readonly | reassigned` を使う。
- `reassigned` 条件:
  - 引数名への代入/拡張代入（`Assign` / `AnnAssign` / `AugAssign`）
  - `Swap` の左辺/右辺としての引数名
  - `for` / `for range` のターゲットとしての引数名
  - `except ... as name` の `name` が引数名と一致
- 入れ子 `FunctionDef` / `ClassDef` 内の代入は外側関数の判定対象に含めない。
- 上記以外は `readonly`。

現時点では、この情報は主に backend 側の引数 `mut` 判定に利用する。

## 10. 対応文

- `FunctionDef`, `ClassDef`, `Return`
- `Assign`, `AnnAssign`, `AugAssign`
- `Expr`, `If`, `For`, `ForRange`, `While`, `Try`, `Raise`
- `Import`, `ImportFrom`, `Pass`, `Break`, `Continue`

補足:

- `Assign` は単一ターゲット文のみ。
- タプル代入は対応（例: `x, y = ...`, `a[i], a[j] = ...`）。
- 名前ターゲットについては RHS タプル型が分かる場合に型環境を更新。
- `from module import *`（ワイルドカード import）は未対応。

## 11. クラス情報の事前収集

生成前に以下を収集する。

- クラス名
- 単純継承関係
- メソッド戻り値型
- フィールド型（クラス本体 `AnnAssign` / `__init__` 代入解析）

## 12. エラー契約

`EastBuildError` は `kind`, `message`, `source_span`, `hint` を持つ。

- `inference_failure`
- `unsupported_syntax`
- `semantic_conflict`

`SyntaxError` も同形式に変換する。

## 13. 人間可読ビュー

- `--human-output` で C++風擬似ソースを出力する。
- 目的はレビュー容易化であり、C++としての厳密コンパイル性は保証しない。
- EASTの `source_span`, `resolved_type`, `ForRange`, `renamed_symbols` 等を保持して可視化する。

## 14. 既知の制約

- Python全構文網羅ではない（Pytra対象サブセット）。
- 高度なデータフロー解析（厳密エイリアス/副作用伝播）は未実装。
- `borrow_kind=move` は未使用。

## 15. 検証状態

- `test/fixtures` 32/32 を `src/toolchain/compiler/east.py` で変換可能（`ok: true`）
- `sample/py` 16/16 を `src/toolchain/compiler/east.py` で変換可能（`ok: true`）
- `sample/py` 16/16 を `src/py2x.py` で「変換→コンパイル→実行」可能（`ok`）

<a id="east-stages"></a>
## 16. 現行の段階構成（2026-02-24）

- EAST は `EAST1 -> EAST2 -> EAST3` の三段で扱う。
- 現行実装では `py2*.py` の既定経路を `EAST3` とする。
- `py2x.py --target cpp` は `--east-stage 3` のみ受理し、`--east-stage 2` はエラーで停止する。
- 非 C++ 8変換器（`py2rs.py`, `py2cs.py`, `py2js.py`, `py2ts.py`, `py2go.py`, `py2java.py`, `py2kotlin.py`, `py2swift.py`）は `--east-stage 2` を移行互換モード（警告付き）として維持する。
- `meta.dispatch_mode` は全段で保持し、意味論適用は `EAST2 -> EAST3` の 1 回のみとする。

### 16.1 段階ごとの責務

- `EAST1`（Parsed）:
  - parser 直後 IR。
  - source span / trivia を保持し、backend 固有ノードは混入させない。
- `EAST2`（Normalized）:
  - 構文正規化 IR。
  - `ForRange` / `RangeExpr`、import 正規化、型解決結果を安定化する。
- `EAST3`（Core）:
  - backend 非依存の意味論確定 IR。
  - boxing/unboxing、`Obj*` 命令、`type_id` 判定、反復計画を明示命令化する。
  - ただし program-wide 決定（call graph / SCC / global non-escape / container ownership / final `type_id` table）は linker 段へ委譲する。

### 16.1.1 段階境界表（入力/出力/禁止事項/担当ファイル）

| 段/境界 | 入力 | 出力 | 禁止事項 | 担当ファイル |
| --- | --- | --- | --- | --- |
| `EAST1` | `Source`（`.py` / parser backend 指定） | `east_stage=1` の `Module` 文書 | `EAST2/EAST3` 変換、dispatch 意味適用、target 依存ノード生成 | `src/toolchain/ir/core.py`, `src/toolchain/ir/east1.py` |
| `EAST2` | `EAST1` 文書 | `east_stage=2` の正規化 `Module` 文書 | dispatch 意味適用、boxing/type_id 命令化、backend 構文判断 | `src/toolchain/ir/east2.py` |
| `EAST3` | `EAST2` 文書 + `meta.dispatch_mode` | `east_stage=3` の core 命令化 `Module` 文書 | target 言語構文への写像、hook による意味論再判断 | `src/toolchain/ir/east2_to_east3_lowering.py`, `src/toolchain/ir/east3.py` |
| `Link` | raw `EAST3` 群 + `link-input.v1` | linked module 群（`east_stage=3` 維持） + `link-output.v1` | target 言語レンダリング、runtime 配置、build manifest 生成 | `src/toolchain/link/*`（追加予定） |

注:
- `Link` は新しい `east_stage` ではない。入出力とも module 本体は `east_stage=3` を維持する。
- `Link` が追加する canonical data は `link-output.v1` と linked module の `meta.linked_program_v1` である。

### 16.2 不変条件

1. `east_stage` とノード形状を一致させる。  
2. `dispatch_mode` の意味適用は `EAST2 -> EAST3` の 1 回だけで行う。  
3. backend / hook は `EAST3` の意味論を再判断しない。  
4. whole-program summary は raw `EAST3` 単体では確定せず、linker が `link-output.v1` と linked module へ materialize する。  

<a id="east-pipeline"></a>
## 17. パイプライン仕様（統合）

1. `Source -> EAST1`  
2. `EAST1 -> EAST2`（Normalize pass）  
3. `EAST2 -> EAST3`（Core Lowering pass）  
4. `EAST3(raw module) -> LinkedProgramLoader / LinkedProgramOptimizer`  
5. `linked module(EAST3) -> TargetEmitter`（言語写像）  

補足:
- `--object-dispatch-mode {type_id,native}` はコンパイル開始時に確定し、`EAST2 -> EAST3` で `iter_plan` / `Obj*` 系命令へ反映する。
- backend/hook 側でモード再判定して命令を差し替えてはならない。
- linker は `dispatch_mode` の整合検査と whole-program summary の確定だけを担当し、backend の代わりに target 言語構文を生成してはならない。

### 17.1 linked module `meta` 契約

linked-program 後の module は `kind=Module` / `east_stage=3` を維持しつつ、`meta.linked_program_v1` を持つ。

linked-program optimizer が生成した synthetic helper module は、上記に加えて `meta.synthetic_helper_v1` を持ってよい。

`meta.linked_program_v1` の必須キー:

- `program_id`
- `module_id`
- `entry_modules`
- `type_id_resolved_v1`
- `non_escape_summary`
- `container_ownership_hints_v1`

責務境界:

- raw `EAST3` では `meta.linked_program_v1` を持たない。
- linked module では `meta.linked_program_v1` を必須とする。
- backend は `meta.linked_program_v1` と `link-output.v1` を読むことは許可されるが、同等情報を再計算してはならない。
- function / call 単位の linked summary（例: `FunctionDef.meta.escape_summary`, `Call.meta.non_escape_callsite`）は linker が最終化してよい。
- `FunctionDef.meta.runtime_abi_v1` のような parser/EAST build 由来 metadata は linked module でも保持必須であり、linker は上書きしてはならない。
- `FunctionDef.meta.template_v1` も parser/EAST build 由来 metadata として linked module で保持必須であり、linker は上書きしてはならない。

<a id="east-file-mapping"></a>
## 18. 現行/移行後の責務対応表（2026-02-24）

| 段 | 責務 | 現行実装（着手時点） | 移行後の正本 |
| --- | --- | --- | --- |
| EAST1 | parser 直後 IR 生成 | `src/toolchain/compiler/east_parts/core.py`（互換 shim） | `src/toolchain/ir/core.py` |
| EAST1 | EAST1 入口 API | `src/toolchain/compiler/east_parts/east1.py`（互換ラッパ経由） | `src/toolchain/ir/east1.py` |
| EAST2 | EAST1 -> EAST2 正規化 API | `src/toolchain/compiler/east_parts/east2.py`（互換ラッパ + selfhost fallback） | `src/toolchain/ir/east2.py` |
| EAST3 | EAST2 -> EAST3 lower 本体 | `src/toolchain/compiler/east_parts/east2_to_east3_lowering.py`（互換 shim） | `src/toolchain/ir/east2_to_east3_lowering.py` |
| EAST3 | EAST3 入口 API | `src/toolchain/compiler/east_parts/east3.py`（互換ラッパ経由） | `src/toolchain/ir/east3.py` |
| Bridge | backend 入口（C++） | `src/py2x.py`（`--east-stage 3` 専用） | `src/py2x.py`（`EAST3` 専用） |
| CLI 互換 | 旧 API 公開 | `src/toolchain/compiler/transpile_cli.py`（互換 shim） | `src/toolchain/frontends/transpile_cli.py`（実体） |

<a id="east1-build-boundary"></a>
## 19. `EAST1` build 入口の責務境界

目的:
- `.py/.json -> EAST1` build の入口責務を分離し、`transpile_cli.py` の責務を縮退する。

構成:
- `core.py`: self-hosted parser 実装（低レイヤ、現行正本は `src/toolchain/ir/core.py`）
- `east1_build.py`: build 入口（追加対象）
- `east1.py`: stage 契約 helper（薄い API）
- `py2x.py --target cpp`: `_analyze_import_graph` / `build_module_east_map` は `East1BuildHelpers` への委譲のみを担当
- `transpile_cli.py`: 実体は `src/toolchain/frontends/transpile_cli.py`。`src/toolchain/compiler/transpile_cli.py` は互換公開 thin wrapper。

受け入れ条件:
1. `EAST1` build は `east_stage=1` 付与までに限定し、`EAST1 -> EAST2` を行わない。  
2. `load_east_document_compat` のエラー契約（`input_invalid` 系）を維持する。  
3. `compiler/transpile_cli.py` は build 本体ロジックを持たず、`frontends/transpile_cli.py` への委譲中心とする。  
4. `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented` を回帰導線に含め、差分発生時は `todo` へ切り出して追跡する。  
5. `test/unit/ir/test_east1_build.py` と `test/unit/toolchain/emit/cpp/test_py2cpp_east1_build_bridge.py` で、`EAST1` 入口契約と `py2cpp` 委譲経路を固定する。  
6. import graph 解析本体は `src/toolchain/frontends/east1_build.py`（`_analyze_import_graph_impl`）を正本とし、`compiler/transpile_cli.py` の `analyze_import_graph` / `build_module_east_map` は互換公開用 thin wrapper のみを保持する。  

<a id="east-migration-phases"></a>
## 20. 移行フェーズ（EAST3 主経路化）

1. Phase 0: 契約テスト固定（`EAST3` ルート必須項目、`ForCore`/`iter_plan` 必須性、dispatch 反映点）
2. Phase 1: API 分離（`east1.py` / `east2.py` / `east3.py` へ責務移管）
3. Phase 2: `EAST3` 主経路化（`py2x.py --target cpp` の再判断ロジック棚卸し）
4. Phase 3: hook 分離（移行期間限定で stage 混在を解消）
5. Phase 4: `EAST2` 経路縮退（互換モード化 -> 段階撤去）

補足:
- 各フェーズの進行管理は `docs/ja/todo/index.md` と `docs/ja/plans/plan-east123-migration.md` で行う。
- `Phase 4` の現行運用: 全 `py2*.py` の既定は `--east-stage 3`。`py2x.py --target cpp` は `--east-stage 2` を受理せずエラー停止、非 C++ 8変換器は `warning: --east-stage 2 is compatibility mode; default is 3.` を伴う互換経路を維持する。

## 21. EAST導入の受け入れ基準

- 既存 `test/fixtures` が EAST 経由で変換可能であること。
- 推論失敗時に、`kind` / `source_span` / `hint` を含むエラーを返すこと。
- 仕様差分は文書化し、後段エミッタで暗黙救済しないこと。
- `--object-dispatch-mode` が `EAST2 -> EAST3` のみで適用されること。
- hooks に言語非依存意味論を新規実装しないこと。

## 22. 最低確認コマンド

```bash
python3 tools/check_py2cpp_transpile.py
python3 tools/check_noncpp_east3_contract.py
python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented
```

## 23. 将来拡張（方針）

- `borrow_kind` は現状 `value | readonly_ref | mutable_ref` を使用し、`move` は未使用。
- 将来的には Rust 向けの参照注釈（`&` / `&mut` 相当）へ接続可能な表現を維持する。
  - ただし、Rust 固有の最終判断（所有権・ライフタイム詳細）はバックエンド責務とする。

## 24. EAST2 共通 IR 契約（Depythonization Draft）

目的:
- EAST2 を「複数 frontend 共有の最初の共通 IR」として扱うため、Python 固有名（builtin 名、`py_*` runtime 名）への直接依存を境界外へ隔離する。

### 24.1 ノード種別（EAST2 で保持する情報）

- 構文ノード:
  - `Module`, `FunctionDef`, `ClassDef`, `If`, `While`, `For`, `ForRange`, `Assign`, `AnnAssign`, `AugAssign`, `Return`, `Expr`, `Import`, `ImportFrom`, `Raise`, `Try`, `Pass`, `Break`, `Continue`, `Match`
- 式ノード:
  - `Name`, `Constant`, `Attribute`, `Call`, `Subscript`, `Slice`, `Tuple`, `List`, `Dict`, `Set`, `ListComp`, `GeneratorExp`, `IfExp`, `Lambda`, `BinOp`, `BoolOp`, `Compare`, `UnaryOp`, `RangeExpr`
- 補助ノード:
  - `ForCore` への変換前段として `For` / `ForRange` の正規化情報（`iter_mode`, `target_type`, `range_mode`）を保持
  - `MatchCase`, `VariantPattern`, `PatternBind`, `PatternWildcard`

### 24.2 演算子・型・メタの中立契約

- 演算子:
  - `BinOp.op` は `Add/Sub/Mult/Div/FloorDiv/Mod/BitAnd/BitOr/BitXor/LShift/RShift` を文字列列挙で保持。
  - `Compare.ops` は `Eq/NotEq/Lt/LtE/Gt/GtE/In/NotIn/Is/IsNot` を保持。
  - `BoolOp.op` は `And/Or` を保持。
- 型:
  - `type_expr` を正本の型表現とし、backend 固有表現を持たない。
  - `resolved_type` は論理型名（`int64`, `float64`, `list[T]`, `dict[K,V]`, `tuple[...]`, `Any`, `unknown`）の legacy mirror としてのみ保持してよい。
  - `OptionalType` / `UnionType(union_mode=dynamic)` / `NominalAdtType` を distinct category として保持する。
- メタ:
  - `meta.dispatch_mode` は `native | type_id` のコンパイル方針値として保持し、意味適用は `EAST2 -> EAST3` の 1 回のみで実施する。
  - import 正規化情報（`import_bindings`, `qualified_symbol_refs`, `import_modules`, `import_symbols`）は frontend 解決結果として保持する。

### 24.3 禁止事項（EAST2 境界）

- `builtin_name` を Python 組み込み識別子（`len`, `str`, `range` など）で意味解釈する契約を backend 側へ漏らさない。
- `runtime_call` に `py_*` 文字列を固定して意味付けしない（`py_len`, `py_to_string`, `py_iter_or_raise` など）。
- `py_tid_*` 互換名を EAST2 公開契約として扱わない（互換ブリッジ内部に閉じる）。

### 24.4 診断・fail-closed 契約

- 解決不能ノード/型は `ok=false` + `error.kind`（`inference_failure` / `unsupported_syntax` / `semantic_conflict`）で停止する。
- 中立契約外の入力（不正 `dispatch_mode`, 未対応ノード形、必要メタ欠落）は暗黙救済せず fail-closed で終了する。
- `type_expr` と `resolved_type` mirror が矛盾する入力は `semantic_conflict` として fail-closed で終了する。
- `meta.nominal_adt_v1`, `Match`, pattern node が v1 契約外（nested variant、guard pattern、literal pattern、namespace sugar 依存など）の shape を持つ場合は `unsupported_syntax` または `semantic_conflict` として fail-closed にする。
- `Match.meta.match_analysis_v1` が `coverage_kind=partial` または `invalid` を示す場合は、backend へ流す前に `semantic_conflict` として停止する。
- 互換フォールバックは段階移行中のみ許可し、`legacy` 明示フラグとともにログへ記録する。

### 24.5 EAST2 -> EAST3 への接続原則

- EAST2 は「何をしたいか（意味タグ）」のみを持ち、`EAST3` で object 境界命令（`Obj*`, `ForCore.iter_plan`）へ確定する。
- `EAST2 -> EAST3` lowering は `type_expr` を見て `optional` / `dynamic union` / `nominal ADT` を別 lane に分け、`resolved_type` の文字列再分解で意味論を決めてはならない。
- `JsonValue` decode / narrowing は `EAST2 -> EAST3` で resolved semantic tag（`json.loads`, `json.value.as_*`, `json.obj.get_*`, `json.arr.get_*`）または等価の dedicated IR category へ正規化し、backend に raw method 名解釈を残してはならない。
- frontend 固有（Python builtins/std）の解決は adapter 層で中立タグへ変換してから EAST2 へ渡す。
- backend/hook は EAST3 以降で言語固有写像のみを担当し、EAST2 契約の再解釈をしない。
