<a href="../../../en/plans/archive/20260309-p1-east-typeexpr-strengthening.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: EAST の型表現を構造化し、union / nominal ADT / narrowing を文字列処理から引き上げる

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-EAST-TYPEEXPR-01`

背景:
- 現行の EAST / emitter / optimizer は、型を主に `resolved_type: "int64|bool"` のような文字列で運んでいる。
- `split_union` / `normalize_type_name` / `split_union_non_none` のような文字列処理 helper が frontend・lowering・backend に分散し、general union と optional、`Any/object` 混じり union、JSON のような nominal ADT を同じ表現で無理に扱っている。
- その結果、`int|bool` のような複合型は annotation/EAST には残せても、backend では `object` や `String` のような fallback へ潰れやすく、IR 側で「何の union なのか」が失われる。
- `JsonValue` は既に public surface として存在するが、現実装は raw `object` / `dict[str, object]` / `list[object]` wrapper が中心で、typed nominal ADT としての lowering はまだ弱い。
- この状態のまま runtime や selfhost の object carrier だけを片付けると、型意味論の debt が EAST 文字列処理に残り続ける。

目的:
- EAST の型表現を `TypeExpr` 相当の構造化表現へ引き上げ、optional / dynamic union / nominal ADT / generic container を文字列分解ではなく意味として保持する。
- `JsonValue` のような closed nominal ADT を「一般 union の一種」ではなく専用 category として扱える土台を作る。
- narrowing / variant check / decode helper の意味論を backend 直書きではなく IR 正本へ寄せる。
- backend が未対応 union を `object` / `String` へ黙って潰す構成をやめ、fail-closed または専用 nominal lowering へ切り替える。

対象:
- `docs/ja/spec/spec-east.md` / `spec-dev.md` / 必要なら `spec-runtime.md` の型表現契約
- frontend の型注釈解析 / 型正規化 / EAST 構築
- `EAST2 -> EAST3` lowering における型・narrowing・union 判定
- backend/emitter/optimizer の stringly-typed 型 helper 依存箇所
- `JsonValue` nominal ADT を使う representative lane
- 回帰テスト / guard / selfhost 互換導線

非対象:
- Python source に新しい pattern matching 構文を入れること
- 任意ユーザー定義 ADT syntax を一気に導入すること
- 全 backend で一般 union を一括実装すること
- `py_runtime.h` の `make_object` overload 群をこの計画だけで削除すること
- stage1 selfhost の host-Python bridge を同時に撤去すること

## 必須ルール

推奨ではなく必須ルールとして扱う。

1. `resolved_type` の文字列だけを真実として扱ってはならない。型意味論の正本は構造化 `TypeExpr` に置く。
2. `T|None`、`Any/object` を含む dynamic union、`JsonValue` のような nominal closed ADT は別 category として区別する。
3. backend は未対応 union を `object` / `String` / 類似 fallback に黙って潰してはならない。暫定互換が必要なら guard と removal plan を必須にする。
4. narrowing / variant 判定 / JSON decode の意味論は frontend/lowering/IR を正本にし、backend は命令写像に徹する。
5. migration 中に string 型名 mirror を残してよいが、`type_expr` と矛盾したときは `type_expr` を正とする。
6. `JsonValue` は general dynamic fallback の言い換えにしてはならない。closed nominal ADT として扱う。
7. 新しい型 category を導入するときは、`spec-east` と unit test に exact schema/例を同時に追加する。

受け入れ基準:
- EAST/EAST3 に `TypeExpr` または等価の構造化型表現が入り、optional / union / nominal ADT / generic container を区別して保持できる。
- frontend は `int | bool`, `T | None`, `JsonValue` 関連型を文字列正規化ではなく構造化表現へ変換する。
- lowering は `dynamic union` と `nominal ADT` を区別し、`JsonValue` decode / narrowing を backend fallback なしで命令化できる。
- representative backend で、一般 union fallback (`object` / `String`) が少なくとも 1 lane で撤去または fail-closed 化される。
- `JsonValue` の後続 nominal 実装が「runtime 先行」ではなく「IR contract 先行」で進められる状態になる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_code_emitter.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east3_optimizer.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_type.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## 実装順

順序は固定する。`JsonValue` nominal runtime を先に深掘りするのではなく、まず EAST の型意味論 debt を止める。

1. stringly-typed 型処理の棚卸し
2. `TypeExpr` schema と category 設計
3. frontend での `TypeExpr` 生成
4. EAST2 -> EAST3 の型/narrowing 命令化
5. backend の fallback 縮退と fail-closed 化
6. `JsonValue` nominal ADT を representative lane へ接続
7. spec / selfhost / guard 固定

## 主要設計方針

### 1. `TypeExpr` を正本にする

少なくとも次を区別できる構造を持たせる。

- `NamedType(name)`
- `GenericType(base, args[])`
- `OptionalType(inner)`
- `UnionType(options[])`
- `DynamicType(kind=Any|object|unknown)`
- `NominalAdtType(name, variants|tag_domain)` または等価 metadata

補足:
- 実際の JSON 形式は実装時に詰めてよいが、backend 固有の型文字列へ再埋め込みしない。
- 互換 migration 中は `resolved_type` string mirror を残してもよいが、`type_expr` が正本である。

### 2. union を 3 系統に分ける

- optional:
  - `T | None`
- dynamic union:
  - `Any/object/unknown` を含む union
- nominal closed union:
  - `JsonValue` のように variant domain が仕様で閉じている ADT

この 3 つを同じ lowering 規則で扱ってはならない。

### 3. JSON は一般 union ではなく nominal ADT として扱う

- `int|bool|str|dict[...]|list[...]` を一般 union として backend に押し込まない。
- `JsonValue` は dedicated nominal surface として IR 側で認識する。
- `std/json.py` の本格 nominal 化は後続実装 slice だが、その前提になる型契約はこの P1 で先に固める。

### 4. backend は fail-closed を基本にする

- `int|bool` のような一般 union をまだ表現できない target は、`object` や `String` に黙って逃がさない。
- 互換 fallback を一時的に残す場合は、guard / TODO / decision log で removal を固定する。

## 分解

- [x] [ID: P1-EAST-TYPEEXPR-01-S1-01] frontend / lowering / optimizer / backend に散在する `split_union` / `normalize_type_name` / `resolved_type` 文字列依存箇所を棚卸しし、`optional` / `dynamic union` / `nominal ADT` / `generic container` ごとに分類する。
- [x] [ID: P1-EAST-TYPEEXPR-01-S1-02] archived `EAST123` / `JsonValue` 契約と矛盾しない end state、non-goal、migration 順序を decision log に固定する。
- [x] [ID: P1-EAST-TYPEEXPR-01-S2-01] `spec-east` / `spec-dev` に `TypeExpr` schema、union 3分類、`type_expr` と `resolved_type` の主従関係を追加する。
- [x] [ID: P1-EAST-TYPEEXPR-01-S2-02] `JsonValue` を general union ではなく nominal closed ADT として扱う IR 契約、decode/narrowing の責務境界、backend fail-closed ルールを spec に固定する。
- [x] [ID: P1-EAST-TYPEEXPR-01-S3-01] frontend の型注釈解析を更新し、`int | bool`, `T | None`, generic nested union から `TypeExpr` を構築する。
- [x] [ID: P1-EAST-TYPEEXPR-01-S3-02] migration 互換として `resolved_type` string mirror を生成するが、`type_expr` を真実とする validator と mismatch guard を追加する。
- [x] [ID: P1-EAST-TYPEEXPR-01-S4-01] EAST2 -> EAST3 lowering で optional / dynamic union / nominal ADT を区別し、narrowing / variant check / decode helper 用の命令または metadata を導入する。
- [x] [ID: P1-EAST-TYPEEXPR-01-S4-02] `JsonValue` に対する representative narrowing path（`as_obj/as_arr/as_int/...` または等価 decode 操作）を backend 直書きではなく IR-first に接続する。
- [x] [ID: P1-EAST-TYPEEXPR-01-S5-01] C++ を先頭 target に、一般 union fallback を `object` へ潰す現行経路の一部を fail-closed または structured lowering へ置換する。
- [x] [ID: P1-EAST-TYPEEXPR-01-S5-02] 他 backend でも `String/object` fallback を棚卸しし、`TypeExpr` 非対応 union の扱いを明示エラーまたは guarded compat に揃える。
- [x] [ID: P1-EAST-TYPEEXPR-01-S6-01] representative `JsonValue` lane を `TypeExpr`/nominal ADT 契約に乗せ、runtime 先行ではなく IR contract 先行で進められることを確認する。
- [x] [ID: P1-EAST-TYPEEXPR-01-S6-02] selfhost / unit / docs / archive を更新し、stringly-typed union debt の再流入を防ぐ guard を追加する。

## 実装者向けメモ

### S1 で必ず出すもの

- どの helper が「optional 専用」なのか
- どの helper が「Any/object 混じり union を dynamic 扱いするため」なのか
- どの helper が「本当は nominal ADT にすべき JSON 経路を一般 union として潰している」のか

### S2 で曖昧にしてはいけないこと

- `type_expr` が無いノードをどう扱うか
- `resolved_type` string mirror をいつまで残すか
- `JsonValue` を `UnionType` で表すのか、専用 nominal category を持つのか

### S4 で先に触るべきもの

- optional 判定
- `Any/object` 混じり union の runtime boundary 判定
- `JsonValue` decode helper に相当する narrowing

### S5 で禁止すること

- C++ の `int|bool -> object` のような無言 fallback を放置したまま「support 済み」と扱うこと
- Rust の `int|bool -> String` のような退化を新しい canonical contract にすること

決定ログ:
- 2026-03-09: ユーザー指示により、`std/json.py` の nominal 化を runtime 先行で進めるのではなく、まず EAST 側の stringly-typed 型 debt を止める P1 を追加した。
- 2026-03-09: この P1 の主眼は `JsonValue` 実装そのものより、`TypeExpr` を正本にして optional / dynamic union / nominal ADT を IR で区別することに置く。
- 2026-03-09: 既存 `JsonValue` public surface は活かすが、それを「一般 union の runtime wrapper」として延命しない。closed nominal ADT として扱う方向を固定した。
- 2026-03-09: `S1-01` の frontend / selfhost parser inventory では、`toolchain/frontends/transpile_cli.py:523` の `normalize_param_annotation()` が union を構造化せず文字列のまま通し、`toolchain/ir/core.py:219` の `_sh_ann_to_type()` が `Optional[T] -> "T | None"` を返し、`toolchain/ir/core.py:118` / `2952` の `_sh_is_type_expr_text()` / `_split_union_types()` が type alias と object/Any receiver guard を文字列分解で支えていることを確認した。ここは `optional` と `dynamic union` の混線源である。
- 2026-03-09: `S1-01` の lowering inventory では、`toolchain/ir/east2_to_east3_lowering.py:27` / `35` / `90` の `_normalize_type_name()` / `_split_union_types()` / `_is_any_like_type()` が union に `Any/object/unknown` を含むかだけで dynamic 判定し、`east2_to_east3_lowering.py:474` の `_wrap_value_for_target_type()` で `Box/Unbox` 境界へ直結していることを確認した。一般 union と dynamic union の区別が IR 入口で失われている。
- 2026-03-09: `S1-01` の generic-container inventory では、`toolchain/link/runtime_template_specializer.py:67` の独自 `_parse_type_expr()` / `_type_expr_to_string()` が `annotation/return_type/resolved_type` を別系統で再解析・再文字列化しており、`backends/common/emitter/code_emitter.py:1516` / `1594` / `1757` の `split_union()` / `split_union_non_none()` / `normalize_type_name()` と二重管理になっていることを確認した。generic container と template specialization も `resolved_type` 文字列正本へ依存している。
- 2026-03-09: `S1-01` の backend inventory では、C++ `backends/cpp/emitter/type_bridge.py:372` が optional だけを `std::optional<T>` へ寄せ、それ以外の general union を `object` へ潰し、`backends/cpp/emitter/header_builder.py:1130` も header 側で同じ fallback を持つ。Rust `backends/rs/emitter/rs_emitter.py:1973` は any-like union を `PyAny`、optional を `Option<T>`、その他 multi-arm union を `String` へ退避し、C# `backends/cs/emitter/cs_emitter.py:676` も non-optional union を `object` へ退避する。`JsonValue` nominal ADT 候補は backend 契約ではなく fallback と decode-first guard で支えられている。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S1-02]: archived `p0-east123-staged-ir.md` との整合上、end state は「`EAST3` が意味論の単一正本」という前提を崩さない。`type_expr` は parser 直後の `EAST1` で未構造でもよいが、遅くとも normalize 済み `EAST2` では構造化され、`EAST2 -> EAST3` 以降の lowering / optimizer / linker / backend は `resolved_type` を再解析して意味論を決めてはならない。migration 中の `resolved_type` は legacy reader 向け mirror に限定し、主従は常に `type_expr` が上位とする。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S1-02]: archived `20260308-p1-jsonvalue-decode-first-contract.md` と `spec-runtime` との整合上、`JsonValue` は `int|float|str|dict[...]|list[...]` の open な一般 union として扱わず、decode-first の public surface を持つ nominal closed ADT lane として扱う。P1 ではこの nominal category を IR/TypeExpr 契約へ持ち上げるところまでを責務とし、`std/json.py` の full nominal carrier 化、compiler/selfhost の typed boundary 化、user-defined ADT syntax や `match`/exhaustiveness はそれぞれ後続の `P2` / `P5` へ送る。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S1-02]: non-goal は 3 つに固定する。(1) すべての backend で一般 union を一括実装すること、(2) migration 初期に `resolved_type` を全面削除すること、(3) runtime 側 `object` / `make_object` debt や selfhost host-Python bridge を同時撤去すること。P1 の完了条件は schema・validator・lowering・representative backend fail-closed の導入であり、runtime carrier の最終形や full language rollout までは含めない。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S1-02]: migration 順序は次で固定する。Step 1: `S2` で `TypeExpr` schema、union 3分類、`type_expr > resolved_type` の主従を spec 化する。Step 2: `S3` で frontend が `type_expr` を生成し、`resolved_type` は mirror と mismatch guard 付き互換層に落とす。Step 3: `S4` で EAST3 lowering が `optional` / `dynamic union` / `nominal ADT` を別 lane に分け、`JsonValue` narrowing を IR-first に接続する。Step 4: `S5` で representative backend が silent fallback を fail-closed または structured lowering に置き換える。Step 5: `S6` で representative `JsonValue` lane と再流入 guard を固定し、その後の internal typed boundary work は `P2`、full nominal ADT language feature は `P5` に送る。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S2-01]: `spec-east` に expression/function level の `type_expr` / `arg_type_exprs` / `return_type_expr`、`NamedType/GenericType/OptionalType/UnionType/DynamicType/NominalAdtType` schema、union 3分類、`type_expr > resolved_type` mirror 規則を追加した。`EAST2` neutral contract でも `OptionalType` / dynamic union / nominal ADT を distinct category とし、`EAST2 -> EAST3` で `resolved_type` 再分解を禁止した。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S2-01]: `spec-dev` には `TypeExpr` 実装契約を追加し、frontend/validator/lowering/template specializer/backend helper が `type_expr` を正本とすること、unsupported general union の `object` / `String` fallback を fail-fast removal plan 付きの一時互換に限定すること、nominal ADT を general union として emit しようとする経路を `semantic_conflict` / `unsupported_syntax` で止めることを固定した。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S2-02]: `spec-east` に `JsonValue` nominal closed ADT lane を追加し、`json.loads`, `json.loads_obj`, `json.loads_arr`, `json.value.as_*`, `json.obj.get_*`, `json.arr.get_*` を canonical semantic tag として固定した。`JsonValue` / `JsonObj` / `JsonArr` は `NominalAdtType` として保持し、general union や `object` fallback へ展開してはならない。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S2-02]: decode/narrowing の責務は frontend/lowering/validator に置き、backend/hook が raw callee/attr 名や `resolved_type` string から JSON decode semantics を再解釈することを禁止した。`JsonValue` nominal carrier や decode op 写像を持たない target は `object` / `PyAny` / `String` へ退化させず fail-closed にする。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S3-01]: `toolchain/frontends/type_expr.py` を shared parser/stringifier として追加し、`transpile_cli.py`・`signature_registry.py`・`toolchain/ir/core.py` が同じ `parse_type_expr_text()` / `normalize_type_text()` / `type_expr_to_string()` を使う形へ揃えた。quoted annotation、`int | bool`、`typing.Optional[T]`、nested generic union、`JsonValue` nominal ADT が frontend/selfhost で同じ `TypeExpr` へ正規化される。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S3-01]: selfhost parser は `FunctionDef.arg_type_exprs` / `return_type_expr`、`AnnAssign.annotation_type_expr` / `decl_type_expr`、typed `Name.type_expr` を emit するよう更新し、`tools/prepare_selfhost_source.py` も shared `TypeExpr` helper を selfhost support block へ同梱するようにした。確認は `python3 -m py_compile src/toolchain/frontends/type_expr.py src/toolchain/frontends/transpile_cli.py src/toolchain/frontends/signature_registry.py src/toolchain/ir/core.py tools/prepare_selfhost_source.py`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core.py' -k quoted_type_annotation_is_normalized`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core.py' -k type_expr_is_emitted_for_union_optional_and_nested_generic_annotations`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core.py' -k type_expr_is_built_for_union_optional_and_nominal_annotations`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k normalize_param_annotation_coarse_types`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k extract_function_signatures_from_python_source_parses_defs`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_stdlib_signature_registry.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_self_hosted_signature.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S3-02]: `sync_type_expr_mirrors()` を `type_expr -> resolved_type` を含む generic mirror filler / mismatch guard として仕上げ、`unknown` は migration 中の placeholder としてだけ自動補完する規則にした。`toolchain/ir/east_io.py` / `east2.py` / `east3.py` / `link/program_validator.py` で同じ guard を通すことで、frontend/selfhost が生成した `type_expr` と loaded/normalized/validated document の legacy string mirror が drift していれば fail-fast する。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S3-02]: `test_frontend_type_expr.py` を追加し、(1) `type_expr` から `resolved_type` / `annotation` / `decl_type` / `arg_types` / `return_type` が埋まること、(2) concrete mismatch は `RuntimeError` になること、(3) `normalize_east1_to_east2_document()` と `validate_raw_east3_doc()` が同じ guard を使うことを固定した。確認は `python3 -m py_compile src/toolchain/frontends/type_expr.py src/toolchain/frontends/transpile_cli.py src/toolchain/frontends/signature_registry.py src/toolchain/ir/core.py tools/prepare_selfhost_source.py`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_frontend_type_expr.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_stdlib_signature_registry.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_self_hosted_signature.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k any_basic_runtime`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k any_dict_items_runtime`、`python3 tools/check_todo_priority.py`、`git diff --check`。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S3-02]: `toolchain/frontends/type_expr.py` に `sync_type_expr_mirrors()` を追加し、`type_expr -> resolved_type`、`annotation_type_expr -> annotation`、`decl_type_expr -> decl_type`、`return_type_expr -> return_type`、`arg_type_exprs[*] -> arg_types[*]` の legacy mirror を一括同期・検証する形にした。mirror が欠落・空文字・`unknown` の場合は `type_expr` から補完し、それ以外の不一致は path 付き `RuntimeError` で止める。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S3-02]: mismatch guard の適用点を selfhost 出力終端 (`toolchain/ir/core.py`)、`EAST1 -> EAST2` normalizer (`toolchain/ir/east2.py`)、generic EAST root loader (`toolchain/ir/east_io.py`)、frontend `load_east3_document()` (`toolchain/ir/east3.py`)、linker raw EAST3 gate (`toolchain/link/program_validator.py`) まで広げた。これで `runtime_template_specializer.py` など legacy `resolved_type` reader に入る前に mirror drift を fail-fast できる。確認は `python3 -m py_compile src/toolchain/frontends/type_expr.py src/toolchain/ir/core.py src/toolchain/ir/east2.py src/toolchain/ir/east3.py src/toolchain/ir/east_io.py src/toolchain/link/program_validator.py`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_frontend_type_expr.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_pylib_json.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core.py' -k type_expr`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east2_to_east3_lowering.py' -k load_east3_document_helper_lowers_from_json_input`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east2_to_east3_lowering.py' -k load_east3_document_normalizes_existing_forcore_runtime_dispatch_mode`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k normalize_param_annotation_coarse_types`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_self_hosted_signature.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S4-01]: `frontend_semantics.py` / `signature_registry.py` / `toolchain/ir/core.py` を更新し、`pytra.std.json.loads(_obj/_arr)` と `JsonValue/JsonObj/JsonArr` decode helper が `json.*` semantic tag family を持つようにした。`toolchain/ir/east2_to_east3_lowering.py` では `decl_type_expr` / `annotation_type_expr` / target `type_expr` を優先して boundary 判定を行い、代表 lane に `type_expr_summary_v1` と `json_decode_v1` metadata を付けることで optional / dynamic union / nominal ADT を EAST3 上で区別できるようにした。確認は `python3 -m py_compile src/toolchain/frontends/frontend_semantics.py src/toolchain/frontends/signature_registry.py src/toolchain/frontends/type_expr.py src/toolchain/ir/core.py src/toolchain/ir/east2_to_east3_lowering.py test/unit/ir/test_east_core.py test/unit/ir/test_east2_to_east3_lowering.py`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east2_to_east3_lowering.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_frontend_type_expr.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_pylib_json.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k json`。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S4-02]: representative lane として `JsonValue.as_obj()` を `Call.lowered_kind=JsonDecodeCall` と `json_decode_receiver` に正規化し、`json_decode_v1.ir_category=JsonDecodeCall` を持つ IR-first narrowing path にした。C++ backend はこの lane を raw `attr` 名ではなく `semantic_tag + lowered_kind + json_decode_receiver` から描画するようにして、backend-local な method-name 再解釈を避けた。確認は `python3 -m py_compile src/toolchain/ir/east2_to_east3_lowering.py src/backends/cpp/emitter/call.py test/unit/ir/test_east2_to_east3_lowering.py test/unit/backends/cpp/test_east3_cpp_bridge.py`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east2_to_east3_lowering.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_pylib_json.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k json`、`python3 tools/check_todo_priority.py`、`git diff --check`。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S5-01]: C++ の representative fail-closed lane は `TypeExpr` を持つ `AnnAssign` / `FunctionDef` signature に絞って先に締めた。`backends/cpp/emitter/type_bridge.py` が nested general union を検出すると `unsupported_syntax` で止まり、`stmt.py` / `cpp_emitter.py` は `annotation_type_expr` / `decl_type_expr` / `arg_type_exprs` / `return_type_expr` を優先して guard を通す。これで `int|bool` や `list[int|bool]` は `TypeExpr` がある限り `object` へ黙って潰れない。確認は `python3 -m py_compile src/backends/cpp/emitter/type_bridge.py src/backends/cpp/emitter/stmt.py src/backends/cpp/emitter/cpp_emitter.py test/unit/backends/cpp/test_cpp_type.py test/unit/backends/cpp/test_east3_cpp_bridge.py`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_type.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S5-02]: 他 backend の棚卸しでは Rust `rs_emitter.py:1973` が general union を `String`、C# `cs_emitter.py:681` が `object`、Go/Java/Kotlin/Scala/Swift/Nim が `any/Object/Any/auto` へ退避していることを確認した。Rust/C# の既存 local TypeExpr guard は維持しつつ、残る Go/Java/Kotlin/Scala/Swift/Nim には shared helper `reject_backend_general_union_type_exprs()` を追加して backend 入口で general-union TypeExpr を `unsupported_syntax` に統一した。JS/TS/PHP/Ruby/Lua は dynamic host target なので今回は compat 維持とし、closed ADT/runtime 契約側で別途扱う。確認は `python3 -m py_compile src/backends/common/emitter/code_emitter.py src/backends/go/emitter/go_native_emitter.py src/backends/java/emitter/java_native_emitter.py src/backends/kotlin/emitter/kotlin_native_emitter.py src/backends/scala/emitter/scala_native_emitter.py src/backends/swift/emitter/swift_native_emitter.py src/backends/nim/emitter/nim_native_emitter.py test/unit/backends/cpp/test_noncpp_east3_contract_guard.py`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_noncpp_east3_contract_guard.py'`、`python3 tools/check_todo_priority.py`、`git diff --check`。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S6-01]: representative lane は `json.value.as_obj` に固定したまま、semantic inference を `owner_type == "JsonValue"` ではなく `TypeExpr`/nominal summary へ寄せた。`summarize_type_expr()` は `nominal_adt_name` を持つようにし、`json_decode_v1` には `receiver_nominal_adt_name` を含める。さらに `resolved_type="unknown"` でも `type_expr=JsonValue` なら lane が成立する回帰を追加し、migration 互換の `resolved_type_compat` も `contract_source` で明示するようにした。逆に `semantic_tag=json.value.as_obj` と receiver nominal 名が食い違う場合は `json_decode_contract_violation` で止める。これで後続の runtime nominal 化は raw method 名や string mirror ではなく IR metadata 契約を前提に進められる。確認は `python3 -m py_compile src/toolchain/frontends/type_expr.py src/toolchain/ir/east2_to_east3_lowering.py test/unit/common/test_frontend_type_expr.py test/unit/ir/test_east2_to_east3_lowering.py`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_frontend_type_expr.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east2_to_east3_lowering.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_pylib_json.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`、`python3 tools/check_todo_priority.py`、`git diff --check`。
- 2026-03-09 [ID: P1-EAST-TYPEEXPR-01-S6-02]: 再流入 guard は representative lane だけでなく `json.obj.get_int`, `json.arr.get_bool`, `json.loads_obj` まで広げ、`receiver_nominal_adt_name` / `result_type.nominal_adt_name` / `decode_kind=module_load` を `tools/check_jsonvalue_typeexpr_contract.py` で固定した。tool 自体の import は `toolchain.*` 直参照に寄せ、repo root 実行でも selfhost 近傍の module layout でも安定させた。あわせて `test_east2_to_east3_lowering.py` に guard script 実行回帰、`test_prepare_selfhost_source.py` に selfhost seed の `_JSON_NOMINALS` / `NominalAdtType` helper 維持回帰を追加した。確認は `python3 tools/check_jsonvalue_typeexpr_contract.py`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_jsonvalue_typeexpr_contract.py'`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east2_to_east3_lowering.py' -k json`、`PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`、`python3 tools/build_selfhost.py`、`python3 tools/check_todo_priority.py`、`git diff --check`。
