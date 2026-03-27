<a href="../../en/plans/p3-multilang-container-ref-model-rollout.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P3: 非C++ backend へのコンテナ参照管理モデル展開

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P3-MULTILANG-CONTAINER-REF-01`

背景:
- C++ backend では `cpp_list_model=pyobj` により、`object` 境界のコンテナを参照管理しつつ、型既知かつ non-escape 経路は値型へ縮退する方針を採用した。
- 一方で non-C++ backend は言語ごとにメモリモデルと container 実装が分離されており、同等の方針（「動的境界は参照管理、型既知 non-escape は値型」）を明示的に扱えていない。
- この差は出力品質・最適化・保守性のばらつきを生み、backend 間の設計一貫性を下げる。

目的:
- non-C++ backend（`rs/cs/js/ts/go/java/kotlin/swift/ruby/lua`）へ、C++ と同等の抽象方針を展開する。
- 方針は「RC 実装の横展開」ではなく「参照管理境界の統一仕様 + typed/non-escape 値型縮退規則の共通化」とする。

対象:
- 仕様/IR 層: `src/pytra/compiler/east_parts/*`（container 所有形態メタの伝播）
- backend: `src/hooks/{rs,cs,js,ts,go,java,kotlin,swift,ruby,lua}/emitter/*`
- runtime 補助: `src/runtime/{rs,cs,go,java,kotlin,swift,ruby,lua}/**`（必要箇所のみ）
- 検証:
  - `test/unit/test_*emitter*.py`
  - `tools/runtime_parity_check.py`（対象 backend 指定）
  - `sample/*` の再生成差分

非対象:
- C++ backend の追加再設計（既存 `cpp_list_model` の全面改変）
- PHP backend 新規追加
- selfhost 完全化タスク全体（本計画は container 参照管理方針に限定）

受け入れ基準:
- 非C++ backend 向けに「参照管理境界 / 値型縮退」の共通仕様が文書化され、IR メタ契約が定義される。
- 少なくとも `rs` + 1つの GC 系 backend で pilot 実装が完了し、回帰テストで固定される。
- 残り backend への展開手順と blocker が TODO 子タスク単位で追跡可能になる。
- sample/parity の主要ケースで動作非退行を確認できる。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_*emitter*.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py --case-root sample --targets rs,cs,go,java,kotlin,swift,ruby,lua`
- `python3 tools/check_todo_priority.py`

## S1-01 現行モデル棚卸し（差分マトリクス）

| backend | 言語メモリモデル | 型既知コンテナ経路 | 動的境界経路 | 現状ギャップ |
|---|---|---|---|---|
| `rs` | 所有権/borrow（GCなし） | `Vec<T>` / `BTreeMap<K,V>`（一部 `HashMap`） | `PyAny::List/Dict/Set` | ownership hint を参照せず backend 内 heuristics 中心。 |
| `cs` | GC | `List<T>` / `Dictionary<K,V>` | `object` + cast helper | non-escape 判定と value/ref 出し分け契約が未統一。 |
| `go` | GC | 既知型 + 一部構造体型 | `any`, `[]any`, `map[any]any` | `any` fallback 条件が明文化不足。 |
| `java` | GC | primitive + 既知クラス | `Object`, `ArrayList<Object>`, `HashMap<Object,Object>` | dynamic 境界判定が emitter 局所実装。 |
| `kotlin` | GC (JVM) | `MutableList<T>` / `MutableMap<K,V>`（型既知時） | `Any?`, `MutableList<Any?>` | `Any?` への降格条件が backend 固有。 |
| `swift` | ARC | Swift 値型/参照型 | `Any`, `[Any]`, `[AnyHashable: Any]` | ARC 前提の境界運用を IR 契約へ未接続。 |
| `js` | GC | 実質動的（Array/Object） | `py_runtime` helper 経由 | typed/non-escape 概念を未運用。 |
| `ts` | GC | 現状 `js` emitter 流用（JS互換） | `js` と同一 | TS 専用の型境界ルール未整備。 |
| `ruby` | GC | 実質動的（Array/Hash） | runtime helper 経由 | 値型縮退メタを未利用。 |
| `lua` | GC | 実質動的（table） | `__pytra_*` helper 経由 | escape 判定の取り込みが未着手。 |

## S1-02 共通用語と判定規則（v1）

- `container_ref_boundary`:
  - `object/Any/unknown/union(any含む)` に流入する地点、または未知 call へ受け渡す地点。
  - この境界では backend 固有の参照管理表現（boxed/Any/GC 参照）へ寄せる。
- `typed_non_escape_value_path`:
  - 要素型が具体化され、`escape_condition` を満たさない局所経路。
  - ここでは backend の値型寄りコンテナ（`Vec<T>`, `List<T>`, `MutableList<T>` など）を優先。
- `escape_condition`（fail-closed）:
  - 戻り値として外部へ返却される。
  - `object/Any` へ代入される。
  - 未知 call / 外部 call に引数として渡る。
  - フィールド保存・別名化で寿命/所有が局所外へ伸びる。
  - 判定不能は escape 扱いに倒す。
- `backend_adaptation_rule`:
  - 共通IRは「境界判定メタ」を供給し、具体的メモリ管理（GC/ARC/borrow）は各 backend が担当する。
  - 目的は `rc` の移植ではなく、同一境界判定で各言語の自然な参照表現へ落とすこと。

## S2-01 EAST3 ownership hint 最小拡張設計（v1）

- 追加メタ:
  - `module.meta.container_ownership_hints_v1`（dict）
  - key: 安定シンボル名（`<scope>::<name>`）
  - value:
    - `container_type`: 例 `list[Token]`, `dict[str, int64]`
    - `element_type`: 例 `Token`, `int64`
    - `boundary_mode`: `"value_path" | "ref_boundary"`
    - `escape`: `true | false`
    - `reason_codes`: 例 `["unknown_call_escape", "any_flow"]`
    - `source_pass`: 例 `"non_escape_interprocedural_pass"`
- ノード参照:
  - `AnnAssign` / `Assign` / `FunctionDef(args, return)` の `meta.container_ownership_hint_ref` に key を保存し、emit 側はここから参照する。
- 伝播規則:
  - alias（`b = a`）は key を引き継ぐが、escape 条件が1つでも成立した時点で `boundary_mode=ref_boundary` に昇格。
  - Call 引数は callee summary が不明なら fail-closed で `escape=true`。
  - 戻り値に載るコンテナは原則 `escape=true`（明示 non-escape 条件がある場合のみ例外）。
- fail-closed 契約:
  - key 未解決、型不整合、`reason_codes` 不明値はすべて `ref_boundary` として扱う。

## S2-02 CodeEmitter 基底 API 設計（backend 中立）

- `CodeEmitter` へ追加する最小 API（案）:
  - `resolve_container_ownership_hint(symbol: str, east_type: str) -> dict[str, Any]`
  - `classify_container_boundary(hint: dict[str, Any], east_type: str) -> str`
  - `should_emit_typed_value_container(hint: dict[str, Any], east_type: str, backend_caps: dict[str, bool]) -> bool`
- backend capability フラグ（例）:
  - `supports_typed_container_value_path`
  - `supports_dynamic_ref_boundary`
  - `supports_zero_copy_container_iter`
- 基底の責務:
  - hint 解決、fail-closed 判定、境界分類（`value_path` or `ref_boundary`）まで。
- backend の責務:
  - 分類結果を自言語表現へ写像（`Vec<T>` / `List<T>` / `Any` / table など）。
  - 既存 runtime helper との接続（boxing/unboxing/cast）を保持。

## S3-01 Rust pilot 実装メモ

- 変更点:
  - `rs_emitter._render_value_for_decl_type` に「参照引数 -> 値型ローカル」縮退を追加。
  - `current_ref_vars` 上の参照値を `AnnAssign` で値型へ初期化する際、
    - `list[...]` / `bytes` / `bytearray` は `to_vec()`
    - `dict[...]` / `set[...]` / `tuple[...]` / class 型は `clone()`
    を適用する。
- 意図:
  - `typed_non_escape_value_path` で `&[T]` / `&BTreeMap<...>` をそのまま値型変数へ代入してしまう破綻を防ぎ、Rust の所有モデルに沿って値化する。
- 回帰固定:
  - `test_py2rs_smoke.py::test_ref_container_args_materialize_value_path_with_to_vec_or_clone`
  - `tools/check_py2rs_transpile.py`
  - `tools/runtime_parity_check.py --case-root sample --targets rs --ignore-unstable-stdout 18_mini_language_interpreter`

## S3-02 Kotlin pilot 実装メモ（GC backend）

- 変更点:
  - `kotlin_native_emitter` に `ref_vars` 文脈を追加し、関数引数のうちコンテナ型（`list/tuple/dict/set/bytes/bytearray`）を `container_ref_boundary` として追跡する。
  - `AnnAssign/Assign` の宣言・再代入で、右辺が `ref_vars` 起点かつ左辺がコンテナ型のときに
    - `MutableList<...>`: `__pytra_as_list(src).toMutableList()`
    - `MutableMap<...>`: `__pytra_as_dict(src).toMutableMap()`
    を挿入し、typed/non-escape 側を「別インスタンス材料化」に固定した。
  - 判定不能ケースは現行経路へ倒す fail-closed を維持（`Name` 右辺以外や target==source は非適用）。
- 意図:
  - GC backend でも Rust pilot と同じ境界規則で、「参照境界（引数）から値経路（ローカル宣言）」へ縮退する最小実装を確認する。
  - 既存 runtime helper 契約（`__pytra_as_list/__pytra_as_dict`）を再利用し、破壊的変更を避ける。

## S3-03 回帰固定メモ（Rust + Kotlin pilot）

- 追加テスト:
  - `test_py2kotlin_smoke.py::test_ref_container_args_materialize_value_path_with_mutable_copy`
    - `a: list[int] = xs`, `b: dict[str, int] = ys` が alias 代入でなく `toMutableList()/toMutableMap()` になることを固定。
- 実行確認:
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2kotlin_smoke.py' -v`
  - `python3 tools/check_py2kotlin_transpile.py`
  - `python3 tools/runtime_parity_check.py --case-root sample --targets kotlin --ignore-unstable-stdout 18_mini_language_interpreter`

## S4-01 C# 展開メモ（S4-01-S1-01）

- 変更点:
  - `cs_emitter` に `current_ref_vars` と container 判定 helper を追加し、関数引数のコンテナ型を `container_ref_boundary` として追跡する。
  - `AnnAssign/Assign` の初期化・再代入で、右辺が ref 境界の `Name` かつ左辺ヒントがコンテナ型のとき、
    - `list[T] -> new List<T>(src)`
    - `dict[K,V] -> new Dictionary<K,V>(src)`
    - `set[T] -> new HashSet<T>(src)`
    - `bytes/bytearray -> new List<byte>(src)`
    を適用して値経路へ materialize する。
  - `test_py2cs_smoke` に `test_ref_container_args_materialize_value_path_with_copy_ctor` を追加し、alias代入再発を検知する。
- 検証:
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v`（PASS）
  - `python3 tools/runtime_parity_check.py --case-root sample --targets cs --ignore-unstable-stdout 18_mini_language_interpreter`（PASS）
  - `python3 tools/check_py2cs_transpile.py` は既存未対応 fixture（`Yield` / `Swap`）2件で fail 継続（今回変更の新規退行なし）。

## S4-01 JS/TS 展開メモ（S4-01-S2-01）

- 変更点:
  - `js_emitter` に `current_ref_vars` と container 判定 helper を追加し、関数引数のコンテナ型を `container_ref_boundary` として追跡する。
  - `AnnAssign/Assign` の初期化・再代入で、右辺が ref 境界 `Name` かつ左辺ヒントがコンテナ型のとき、
    - `list/tuple/bytes/bytearray`: `Array.isArray(src) ? src.slice() : Array.from(src)`
    - `dict`: `{ ...src }`（非 object は `{}` fallback）
    - `set`: `new Set(src)`（非 Set は空 set fallback）
    を適用して値経路へ materialize する。
  - `test_py2js_smoke` / `test_py2ts_smoke` に ref-container 回帰を追加し、TS preview（JS pipeline）でも同じ出力を固定した。
- 検証:
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2js_smoke.py' -v`（PASS）
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2ts_smoke.py' -v`（PASS）
  - `python3 tools/runtime_parity_check.py --case-root sample --targets js,ts --ignore-unstable-stdout 18_mini_language_interpreter`（PASS）
  - `python3 tools/check_py2js_transpile.py` / `check_py2ts_transpile.py` は `east3-contract` 前段が `FAIL cs: src/py2cs.py missing ['choices=[\"2\", \"3\"]']` で停止（JS/TS実装差分外の共通 blocker）。

## S4-01 Go 展開メモ（S4-01-S3-01）

- 変更点:
  - `go_native_emitter` に `ref_vars` 文脈を追加し、関数引数コンテナ型を `container_ref_boundary` として追跡する。
  - `AnnAssign/Assign` の初期化・再代入で、右辺が ref 境界 `Name` かつ左辺がコンテナ型のとき、
    - slice: `append([]T(nil), src...)`
    - map: IIFE + `make(map[K]V, len(src))` + `range` copy（`nil` は `nil` のまま返却）
    を適用して局所 value path を materialize する。
  - `test_py2go_smoke` に `test_ref_container_args_materialize_value_path_with_copy_expr` を追加し、alias 代入再発を検知する。
- 検証:
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v`（PASS）
  - `python3 tools/check_py2go_transpile.py`（PASS）
  - `python3 tools/runtime_parity_check.py --case-root sample --targets go --ignore-unstable-stdout 18_mini_language_interpreter` は既存 Go 生成の `TokenLike` field 解決失敗で run_failed（本 task 外 blocker）。

分解:
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-01] backend 別の現行コンテナ所有モデル（値/参照/GC/ARC）を棚卸しし、差分マトリクスを作成する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-02] 「参照管理境界」「typed/non-escape 縮退」「escape 条件」の共通用語と判定規則を仕様化する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-01] EAST3 ノードメタに container ownership hint を保持・伝播するための最小拡張設計を作成する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-02] CodeEmitter 基底で利用可能な ownership 判定 API（backend 中立）を定義する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-01] Rust backend へ pilot 実装し、`object` 境界と typed 値型経路の出し分けを追加する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-02] GC 系 backend（Java or Kotlin）へ pilot 実装し、同一判定規則での縮退を確認する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-03] pilot 2 backend の回帰テスト（unit + sample 断片）を追加し、再発検知を固定する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01] `cs/js/ts/go/swift/ruby/lua` へ順次展開し、backend ごとの runtime 依存差を吸収する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S1-01] C# backend へ展開し、ref境界引数のコンテナを copy ctor で value path 材料化する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S2-01] JS/TS backend の動的コンテナ helper 境界へ同一判定規則を展開する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S3-01] Go backend へ展開し、`any` 境界と typed 値型経路を分離する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S4-01] Swift backend へ展開し、`Any` 境界と typed 値型経路を分離する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S5-01] Ruby backend へ展開し、動的 helper 境界と局所値経路の材料化規則を追加する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S6-01] Lua backend へ展開し、table helper 境界と局所値経路の材料化規則を追加する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-02] parity/smoke を実行して non-regression を確認し、未達は blocker として分離記録する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S5-01] `docs/ja/how-to-use.md` と backend 仕様に運用ルール（参照管理境界と rollback 手段）を追記する。

決定ログ:
- 2026-03-01: ユーザー要望により、C++ で採用済みの container 参照管理方針を non-C++ backend にも展開する計画を P3 として新規作成した。
- 2026-03-01: 方針は「各言語に `rc` を強制移植」ではなく、「動的境界は参照管理、型既知 non-escape は値型」の抽象ルール統一を採用した。
- 2026-03-02: S1-01 として非C++ backend の現行モデルを棚卸しし、`rs/cs/go/java/kotlin/swift` は「型付きコンテナ + Any/Object fallback」、`js/ts/ruby/lua` は「動的コンテナ + runtime helper」中心であると整理した。
- 2026-03-02: S1-02 として `container_ref_boundary` / `typed_non_escape_value_path` / `escape_condition` を v1 用語として定義し、判定不能時は escape 扱いに倒す fail-closed 方針を固定した。
- 2026-03-02: S2-01 として EAST3 `container_ownership_hints_v1` スキーマとノード参照キー（`meta.container_ownership_hint_ref`）を定義し、伝播/昇格/fail-closed 規則を固定した。
- 2026-03-02: S2-02 として CodeEmitter 基底の ownership 判定 API 案を定義し、基底責務（判定）と backend 責務（表現写像）の境界を明文化した。
- 2026-03-02: S3-01 として Rust emitter に参照引数から値型ローカルへの `to_vec()/clone()` 材料化を実装し、typed value path を安全に通す pilot を追加した（unit/transpile/parity 通過）。
- 2026-03-02: S3-02 として Kotlin emitter に `ref_vars` 追跡と `AnnAssign/Assign` の `toMutableList()/toMutableMap()` 材料化を実装し、GC backend でも同一境界規則の pilot を追加した。
- 2026-03-02: S3-03 として Kotlin smoke に回帰テストを追加し、`check_py2kotlin_transpile` + sample parity(case18) まで通過を確認した。
- 2026-03-02: S4-01 の分割を追加し、S4-01-S1-01 として C# backend に copy ctor 材料化を実装。`test_py2cs_smoke` と sample parity(case18) を通過、`check_py2cs_transpile` の `Yield/Swap` 失敗は既存既知として継続確認。
- 2026-03-02: S4-01-S2-01 として JS emitter に ref-container 材料化（`slice/Array.from`・`{...src}`・`new Set(src)`）を追加し、TS preview も同時反映。JS/TS smoke と sample parity(case18) は通過し、`check_py2js/ts_transpile` の失敗は共通 `east3-contract`（C# CLI 契約）由来 blocker と分離した。
- 2026-03-02: S4-01-S3-01 として Go emitter に ref-container 材料化（slice copy + map deep copy IIFE）を導入。Go smoke/transpile は通過し、sample/18 parity(go) の run_failed は既存 `TokenLike` field 解決失敗として S4-02 blocker へ分離した。
- 2026-03-02: S4-01-S4-01 として Swift emitter に `ref_vars` 追跡と `AnnAssign/Assign` の container 材料化（`Array(__pytra_as_list(...))` / `Dictionary(uniqueKeysWithValues: __pytra_as_dict(...).map { ... })`）を導入。`test_py2swift_smoke` / `check_py2swift_transpile` は通過し、sample parity(case18) は toolchain_missing skip で run_failed なし。
- 2026-03-02: S4-01-S5-01 として Ruby emitter に `ref_vars` + `decl_type` ベースの container 材料化（`__pytra_as_list(...).dup` / `__pytra_as_dict(...).dup`）を導入し、`dict.get` を `Hash#fetch` lower に更新。`test_py2rb_smoke` は通過、`sample/18` parity(ruby) は既存の `single_char_token_tags` 初期化欠落起因 run_failed を S4-02 blocker として分離。
- 2026-03-02: S4-01-S6-01 として Lua emitter に関数スコープ `ref_vars/type_map` を導入し、`AnnAssign/Assign(Name)` で ref境界コンテナを shallow copy（list: index走査, dict: `pairs` 走査）へ材料化。追加回帰は通過し、`check_py2lua_transpile` + sample/18 parity(lua) は通過（`test_py2lua_smoke` 全体の既存期待差分は S4-02 で切り分け）。
- 2026-03-02: S4-02 を実施し、`check_py2{cs/js/ts/go/swift/rb/lua}_transpile` と sample parity(case18) を横断確認。`go` は `TokenLike` field compile error、`ruby` は tokenize run_failed、`swift` は toolchain_missing skip、`cs/rb/js/ts` transpile は既知 fixture/contract 失敗を blocker として分離記録した。
- 2026-03-02: S5-01 として `docs/ja/how-to-use.md` に non-C++ backend の参照管理境界運用（確認コマンド/rollback）を追記し、`spec-gsk-native-backend.md` / `spec-ruby-native-backend.md` / `spec-lua-native-backend.md` へ同一 v1 契約を反映した。
