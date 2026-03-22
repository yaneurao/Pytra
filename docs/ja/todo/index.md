# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-22（完了タスクをアーカイブへ移動）

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs/ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs/ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs/ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs/ja/todo/index.md` / `docs/ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。
- 一時出力は既存 `out/`（または必要時のみ `/tmp`）を使い、リポジトリ直下に新規一時フォルダを増やさない。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs/ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs/ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs/ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。

## 未完了タスク

### P0: C++ generated runtime ヘッダー生成パイプライン整備

#### P0-18: Object\<T\> 移行 — ControlBlock + テンプレート view 方式

文脈: [docs/ja/plans/p0-object-t-migration.md](../plans/p0-object-t-migration.md)
仕様: [docs/ja/spec/spec-object.md](../spec/spec-object.md)

**フェーズ 1: ControlBlock + Object\<T\> の導入（runtime 並行運用）**

1. [x] [ID: P0-OBJECT-T-MIGRATION-01-S1] `core/object.h` に `ControlBlock`, `Object<T>`, `make_object<T>`, `upcast<To>` を実装する。
2. [x] [ID: P0-OBJECT-T-MIGRATION-01-S2] `core/object.h` に `is_subtype` 区間判定を実装する（既存の `type_id_support.h` と並行）。
3. [x] [ID: P0-OBJECT-T-MIGRATION-01-S3] `TypeInfo` 型テーブルと `g_type_table` を実装する（リンカーの type_id 割り当てと統合）。

**フェーズ 2: emitter の移行（Object\<T\> 形式の C++ を生成）**

4. [x] [ID: P0-OBJECT-T-MIGRATION-02-S1] emitter のクラス定義 emit を `Object<T>` 対応に変更する。
5. [x] [ID: P0-OBJECT-T-MIGRATION-02-S2] emitter の変数宣言・代入・upcast emit を `Object<T>` の view 変換に変更する。
6. [x] [ID: P0-OBJECT-T-MIGRATION-02-S3] emitter の isinstance/downcast emit を `is_subtype` + `static_cast` に変更する。
7. [x] [ID: P0-OBJECT-T-MIGRATION-02-S4] emitter の関数引数・戻り値の型 emit を `Object<T>` 対応に変更する。
8. [x] [ID: P0-OBJECT-T-MIGRATION-02-S5] emitter の Any/object 型 emit を型消去版 `Object<>` に変更する。

**フェーズ 3: list\<T\> / dict\<K,V\> の Object 統合**

9. [x] [ID: P0-OBJECT-T-MIGRATION-03-S1] `list<T>` から `RcObject` 継承を除去し、`Object<list<T>>` で管理する形に移行する。
10. [x] [ID: P0-OBJECT-T-MIGRATION-03-S2] `dict<K,V>` から `RcObject` 継承を除去し、`Object<dict<K,V>>` で管理する形に移行する。
11. [x] [ID: P0-OBJECT-T-MIGRATION-03-S3] emitter の list/dict boxing を `Object<list<T>>` / `Object<dict<K,V>>` に変更する。

**フェーズ 4: 旧型の撤去**

12. [x] [ID: P0-OBJECT-T-MIGRATION-04-S1] `RcObject` クラスの外部依存を除去する。（py_types.h で legacy alias 化、type_id_support.h の specialization 削除）
13. [x] [ID: P0-OBJECT-T-MIGRATION-04-S2] `rc<T>` テンプレートの外部依存を除去する。（S1 と同時。gc.h 定義自体は S5 で削除）
14. [x] [ID: P0-OBJECT-T-MIGRATION-04-S3] 旧 `object` 型を削除し、`Object<void>` または新 `object` typedef に統一する。
15. [x] [ID: P0-OBJECT-T-MIGRATION-04-S4] `tagged_value.h` を空ヘッダー化。（PyBoxed/py_box/py_unbox 削除、rc_ops.h も同時に空化）
16. [ ] [ID: P0-OBJECT-T-MIGRATION-04-S5] `gc.h`/`gc.cpp` を削除する。（全 generated .cpp が rc<T> 不使用になった時点で実施。P0-22 と連動）

**フェーズ 5: テスト・検証**

17. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S1] `test_py2cpp_features.py` の全コンパイル + 実行テストが通る。
18. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S2] `test_cpp_runtime_type_id.py` の type_id テストが通る。
19. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S3] selfhost multi-module transpile が動作する。
20. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S4] sample/py の全 18 ケースが C++ で compile + run できる。

#### P0-28: main_guard_body の Expr Call 戻り値を Discard でラップ

文脈: [docs/ja/plans/p0-main-guard-discard.md](../plans/p0-main-guard-discard.md)

1. [ ] [ID: P0-MAIN-GUARD-DISCARD-01] main_guard_body 内の Expr Call を Discard でラップする。
2. [ ] [ID: P0-MAIN-GUARD-DISCARD-02] ユニットテストを追加する。

#### P0-29: 未使用変数の検出

文脈: [docs/ja/plans/p0-unused-variable-detection.md](../plans/p0-unused-variable-detection.md)

1. [x] [ID: P0-UNUSED-VAR-01] 未使用変数検出パスを実装し、Assign target / VarDecl に `unused` フラグを付与する。
2. [x] [ID: P0-UNUSED-VAR-02] 動作確認（unused_var=True, used=False）。

#### P0-30: タプル代入の正規化（swap 検出）

文脈: [docs/ja/plans/p0-tuple-assign-normalization.md](../plans/p0-tuple-assign-normalization.md)

1. [x] [ID: P0-TUPLE-ASSIGN-NORM-01] 2 要素 swap パターンを検出して Swap ノードに変換する。
2. [x] [ID: P0-TUPLE-ASSIGN-NORM-02] 動作確認（Name swap + Subscript swap）。

#### P0-31: for ループの TupleTarget 事前展開

文脈: [docs/ja/plans/p0-for-tuple-target-expansion.md](../plans/p0-for-tuple-target-expansion.md)

1. [x] [ID: P0-FOR-TUPLE-EXPAND-01] ForCore TupleTarget を事前展開する EAST3 パスを実装する。
2. [x] [ID: P0-FOR-TUPLE-EXPAND-02] 動作確認（TupleTarget → NameTarget + body 先頭に要素代入）。

#### P0-22: REPO_ROOT 修正 + import alias 解決 + conftest extern 関数修正

文脈: [docs/ja/plans/p0-cpp-repo-root-and-import-alias-fix.md](../plans/p0-cpp-repo-root-and-import-alias-fix.md)

1. [ ] [ID: P0-REPO-ROOT-IMPORT-FIX-S1] include path 生成の整合性確保（`_module_name_to_cpp_include` が `-I` フラグで解決可能なパスを生成することを保証）
2. [x] [ID: P0-REPO-ROOT-IMPORT-FIX-S2] `REPO_ROOT` を `parents[5]` に修正する（S1 完了後）
3. [x] [ID: P0-REPO-ROOT-IMPORT-FIX-S3] `_resolve_imported_symbol_cpp_target` で bare module name を正規化（`math` → `pytra.std.math`）
4. [ ] [ID: P0-REPO-ROOT-IMPORT-FIX-S4] `build_multi_cpp.py` の generated source 自動リンク拡張

進捗:
- 2026-03-22: conftest extern stripping 修正済み。runtime_symbol_index.json の utils module パス修正済み。
- 2026-03-22: REPO_ROOT parents[5] + call.py normalize コミット済み。S2,S3 完了。テスト 234 passed (78%)。

### P2: built-in 依存を EAST1 → linker 経由で解決

文脈: [docs/ja/plans/p2-builtin-dependency-via-linker.md](../plans/p2-builtin-dependency-via-linker.md)

1. [x] [ID: P2-BUILTIN-VIA-LINKER-01] EAST1 パーサーに built-in → module 対応テーブルを追加し、`import_bindings` に暗黙依存を記録する。
2. [x] [ID: P2-BUILTIN-VIA-LINKER-02] linker が `pytra.built_in.*` を link-output manifest に含めることを検証する。
3. [ ] [ID: P2-BUILTIN-VIA-LINKER-03] 全 emitter（C++ 含む）から `py_runtime.*` / ヘッダーの決め打ちバンドルを除去する（`@extern` 関数の扱い確定後）。
4. [x] [ID: P2-BUILTIN-VIA-LINKER-04] 既存テストのリグレッションがないことを検証する。

### P2: 全 backend 共通テストスイートの整備

文脈: [docs/ja/plans/p2-cross-backend-common-test-suite.md](../plans/p2-cross-backend-common-test-suite.md)

1. [ ] [ID: P2-COMMON-TEST-S1] 共通テスト基盤の構築（`test/unit/backends/common/conftest.py`, `compile_and_run` ヘルパー, 言語別 skip 管理）
2. [ ] [ID: P2-COMMON-TEST-S2] 既存 fixture から言語非依存テストを抽出（算術・文字列・リスト・制御フロー・関数・クラス）
3. [ ] [ID: P2-COMMON-TEST-S3] 全 18 言語で共通テストを実行し、skip / bug を分類
4. [ ] [ID: P2-COMMON-TEST-S4] `test_py2cpp_features.py` から共通化済みテストを除去し、C++ 固有テストのみに絞る

前提: P0-18（Object\<T\> 移行）完了後に着手。

### P3: pyobj list alias escape 解析を EAST3 パスへ移行

文脈: [docs/ja/plans/p3-pyobj-list-escape-to-east3.md](../plans/p3-pyobj-list-escape-to-east3.md)

1. [ ] [ID: P3-PYOBJ-LIST-ESCAPE-01] lifetime_analysis_pass に list alias escape 解析を追加し、FunctionDef.meta に結果を付与する。
2. [ ] [ID: P3-PYOBJ-LIST-ESCAPE-02] C++ emitter を meta 参照に切り替え、`_collect_pyobj_runtime_list_alias_names` を除去する。
3. [ ] [ID: P3-PYOBJ-LIST-ESCAPE-03] `analysis.py` の `_collect_assigned_name_types` を除去する（依存消滅確認後）。
4. [ ] [ID: P3-PYOBJ-LIST-ESCAPE-04] ユニットテストを追加し、既存 pyobj list テストのリグレッションがないことを検証する。

### P5: Go sample parity

文脈: [docs/ja/plans/p5-go-sample-parity.md](../plans/p5-go-sample-parity.md)

1. [ ] [ID: P5-GO-PARITY-01] `runtime_parity_check.py --targets go` で sample/py の全 18 ケースが PASS する。

### P5: Java sample parity

文脈: [docs/ja/plans/p5-java-sample-parity.md](../plans/p5-java-sample-parity.md)

1. [ ] [ID: P5-JAVA-PARITY-01] `runtime_parity_check.py --targets java` で sample/py の全 18 ケースが PASS する。

### P5: Kotlin sample parity

文脈: [docs/ja/plans/p5-kotlin-sample-parity.md](../plans/p5-kotlin-sample-parity.md)

1. [ ] [ID: P5-KOTLIN-PARITY-01] `runtime_parity_check.py --targets kotlin` で sample/py の全 18 ケースが PASS する。

### P5: Swift sample parity

文脈: [docs/ja/plans/p5-swift-sample-parity.md](../plans/p5-swift-sample-parity.md)

1. [ ] [ID: P5-SWIFT-PARITY-01] `runtime_parity_check.py --targets swift` で sample/py の全 18 ケースが PASS する。

### P7: C++ test_py2cpp_features.py テストパス率改善

文脈: [docs/ja/plans/p7-cpp-test-pass-rate-improvement.md](../plans/p7-cpp-test-pass-rate-improvement.md)

1. [ ] [ID: P7-CPP-TEST-PASS-S1] Multi-file cross-module include 生成修正（~12件）
2. [ ] [ID: P7-CPP-TEST-PASS-S2] conftest 生成 C++ の Object<T> 互換修正（~5件）
3. [ ] [ID: P7-CPP-TEST-PASS-S3] Any/Object<void> runtime 修正（~4件）
4. [ ] [ID: P7-CPP-TEST-PASS-S4] その他テスト修正（~10件）

進捗:
- 2026-03-22: 192/107 (64%) → 268/31 (89.3%)。+76テスト改善。残り31件の計画書起票。

### P6: Zig コンテナ型の Obj（rc）管理

文脈: [docs/ja/plans/p6-zig-obj-managed-containers.md](../plans/p6-zig-obj-managed-containers.md)

1. [ ] [ID: P6-ZIG-OBJ-CONTAINERS-01-S1] `py_runtime.zig` に `make_list` / `list_append` / `list_get` / `list_set` / `list_len` / `make_bytearray` を追加する。
2. [ ] [ID: P6-ZIG-OBJ-CONTAINERS-01-S2] emitter の `_zig_type` で `list[T]` / `bytearray` / `bytes` → `pytra.Obj` に変更。List リテラル / Subscript / `.append` / `len()` をランタイム API 呼び出しに変換する。
3. [ ] [ID: P6-ZIG-OBJ-CONTAINERS-01-S3] test/fixtures の 28/30 テストが通ることを確認する。
4. [ ] [ID: P6-ZIG-OBJ-CONTAINERS-01-S4] sample/py/01_mandelbrot.py が正しい PNG を出力し、Python 版と一致することを確認する。

