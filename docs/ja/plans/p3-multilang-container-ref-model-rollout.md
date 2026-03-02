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

分解:
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-01] backend 別の現行コンテナ所有モデル（値/参照/GC/ARC）を棚卸しし、差分マトリクスを作成する。
- [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-02] 「参照管理境界」「typed/non-escape 縮退」「escape 条件」の共通用語と判定規則を仕様化する。
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-01] EAST3 ノードメタに container ownership hint を保持・伝播するための最小拡張設計を作成する。
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-02] CodeEmitter 基底で利用可能な ownership 判定 API（backend 中立）を定義する。
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-01] Rust backend へ pilot 実装し、`object` 境界と typed 値型経路の出し分けを追加する。
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-02] GC 系 backend（Java or Kotlin）へ pilot 実装し、同一判定規則での縮退を確認する。
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-03] pilot 2 backend の回帰テスト（unit + sample 断片）を追加し、再発検知を固定する。
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01] `cs/js/ts/go/swift/ruby/lua` へ順次展開し、backend ごとの runtime 依存差を吸収する。
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-02] parity/smoke を実行して non-regression を確認し、未達は blocker として分離記録する。
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S5-01] `docs/ja/how-to-use.md` と backend 仕様に運用ルール（参照管理境界と rollback 手段）を追記する。

決定ログ:
- 2026-03-01: ユーザー要望により、C++ で採用済みの container 参照管理方針を non-C++ backend にも展開する計画を P3 として新規作成した。
- 2026-03-01: 方針は「各言語に `rc` を強制移植」ではなく、「動的境界は参照管理、型既知 non-escape は値型」の抽象ルール統一を採用した。
- 2026-03-02: S1-01 として非C++ backend の現行モデルを棚卸しし、`rs/cs/go/java/kotlin/swift` は「型付きコンテナ + Any/Object fallback」、`js/ts/ruby/lua` は「動的コンテナ + runtime helper」中心であると整理した。
- 2026-03-02: S1-02 として `container_ref_boundary` / `typed_non_escape_value_path` / `escape_condition` を v1 用語として定義し、判定不能時は escape 扱いに倒す fail-closed 方針を固定した。
