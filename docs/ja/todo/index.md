# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-21（P2-REMOVE-NONCPP-RUNTIME-CALL を起票）

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

#### P0-19: ブロックスコープ変数の hoist（最優先）

文脈: [docs/ja/plans/p0-block-scope-variable-hoist.md](../plans/p0-block-scope-variable-hoist.md)

1. [x] [ID: P0-BLOCK-SCOPE-VAR-HOIST-01-S1] if/else ブロック内の変数宣言 hoist を EAST3 lowering に実装する。
2. [x] [ID: P0-BLOCK-SCOPE-VAR-HOIST-01-S2] for/while ブロック内の変数宣言 hoist を EAST3 lowering に実装する。
3. [x] [ID: P0-BLOCK-SCOPE-VAR-HOIST-01-S3] C++ emitter の既存 hoist ロジックを EAST3 lowering に移行し、emitter から除去する。
4. [x] [ID: P0-BLOCK-SCOPE-VAR-HOIST-01-S4] ユニットテストを追加する（if/else, for, while, nested blocks）。
5. [x] [ID: P0-BLOCK-SCOPE-VAR-HOIST-01-S5] Dart/Zig/Julia emitter が hoist 済み EAST3 で正しく動作することを検証する。

#### P0-11: PowerShell native emitter 実行 parity

文脈: [docs/ja/plans/p0-powershell-native-emitter-execution-parity.md](../plans/p0-powershell-native-emitter-execution-parity.md)

1. [x] [ID: P0-PS-EXEC-PARITY-01-S1] FunctionDef の `self` パラメータを除外せず `$self` として残す。クラスメソッド呼び出し時に第1引数として渡す。
2. [x] [ID: P0-PS-EXEC-PARITY-01-S2] `bytearray`, `bytes`, `enumerate`, `sorted`, `reversed`, `zip` 等を `__pytra_*` ランタイム関数にマッピング。不足 runtime 関数を追加。
3. [x] [ID: P0-PS-EXEC-PARITY-01-S3] `math.sqrt` → `[Math]::Sqrt` 等の stdlib Attribute Call を直接 PowerShell 構文に変換。
4. [x] [ID: P0-PS-EXEC-PARITY-01-S4] Assign でタプルターゲットが左辺にある場合、一時変数展開を emit する。
5. [x] [ID: P0-PS-EXEC-PARITY-01-S5] Call の func がクラス名の場合、コンストラクタ関数呼び出しとして emit する。
6. [x] [ID: P0-PS-EXEC-PARITY-01-S6] `test/unit/backends/powershell/test_py2ps_smoke.py` に pwsh 実行テスト（26件）を追加し、主要 fixture の実行成功を検証する。

#### P0-12: pytra-cli.py が C++ 固有オプションを転送しない

文脈: [docs/ja/plans/p0-12-py2x-cpp-options-forwarding.md](../plans/p0-12-py2x-cpp-options-forwarding.md)

1. [x] [ID: P0-PY2X-CPP-OPTIONS-01] CLI テスト群を `toolchain/emit/cpp/cli.py` 直接呼び出しに変更する

#### P0-13: テストが旧 src/backends/cpp/cli.py パスを参照

文脈: [docs/ja/plans/p0-13-cli-path-migration.md](../plans/p0-13-cli-path-migration.md)

1. [x] [ID: P0-CLI-PATH-MIGRATION-01] テスト内の旧 cli.py パスを新パスに更新する

#### P0-15: エミッター出力変化によるテストアサーション不一致

文脈: [docs/ja/plans/p0-15-emitter-output-assertions.md](../plans/p0-15-emitter-output-assertions.md)

1. [x] [ID: P0-EMITTER-OUTPUT-ASSERTIONS-01] テストアサーションを新エミッター出力に追従させる

#### P0-16: runtime include パスのテストアサーション不一致

文脈: [docs/ja/plans/p0-16-runtime-include-paths.md](../plans/p0-16-runtime-include-paths.md)

1. [x] [ID: P0-RUNTIME-INCLUDE-PATHS-01] テストアサーションを新インクルードパスに追従させる

#### P0-17: emitter 旧 API 出力の一掃

文脈: [docs/ja/plans/p0-emitter-legacy-api-cleanup.md](../plans/p0-emitter-legacy-api-cleanup.md)

1. [x] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S1] emitter の `object_new` / `PyListObj` 生成箇所を `object(...)` / `list<object>` に置換。
2. [x] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S2] emitter の `obj_to_list_ref_or_raise` / `py_object_try_cast` を `object::as<T>()` に置換。
3. [ ] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S3] emitter の `py_list_at_ref` / `py_at(tuple)` を新 API に置換。
4. [ ] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S4] `pytra::utils` namespace の include パス修正。
5. [x] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S5] テストアサーション（`test_cpp_runtime_type_id.py`）を新 API に追従。

> P0-17 の残存問題（include 順序による SFINAE 失敗、object(rc\<dict\>) 変換不可）は P0-18 (Object\<T\> 移行) で根本解決する。

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
6. [ ] [ID: P0-OBJECT-T-MIGRATION-02-S3] emitter の isinstance/downcast emit を `is_subtype` + `static_cast` に変更する。
7. [ ] [ID: P0-OBJECT-T-MIGRATION-02-S4] emitter の関数引数・戻り値の型 emit を `Object<T>` 対応に変更する。
8. [ ] [ID: P0-OBJECT-T-MIGRATION-02-S5] emitter の Any/object 型 emit を型消去版 `Object<>` に変更する。

**フェーズ 3: list\<T\> / dict\<K,V\> の Object 統合**

9. [x] [ID: P0-OBJECT-T-MIGRATION-03-S1] `list<T>` から `RcObject` 継承を除去し、`Object<list<T>>` で管理する形に移行する。
10. [x] [ID: P0-OBJECT-T-MIGRATION-03-S2] `dict<K,V>` から `RcObject` 継承を除去し、`Object<dict<K,V>>` で管理する形に移行する。
11. [x] [ID: P0-OBJECT-T-MIGRATION-03-S3] emitter の list/dict boxing を `Object<list<T>>` / `Object<dict<K,V>>` に変更する。

**フェーズ 4: 旧型の撤去**

12. [ ] [ID: P0-OBJECT-T-MIGRATION-04-S1] `RcObject` クラスを削除する。
13. [ ] [ID: P0-OBJECT-T-MIGRATION-04-S2] `rc<T>` テンプレートを削除する。
14. [x] [ID: P0-OBJECT-T-MIGRATION-04-S3] 旧 `object` 型を削除し、`Object<void>` または新 `object` typedef に統一する。
15. [ ] [ID: P0-OBJECT-T-MIGRATION-04-S4] `tagged_value.h` を削除する（ControlBlock に統合済み）。
16. [ ] [ID: P0-OBJECT-T-MIGRATION-04-S5] `gc.h` を `ControlBlock` ベースの rc 管理に書き換える。

**フェーズ 5: テスト・検証**

17. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S1] `test_py2cpp_features.py` の全コンパイル + 実行テストが通る。
18. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S2] `test_cpp_runtime_type_id.py` の type_id テストが通る。
19. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S3] selfhost multi-module transpile が動作する。
20. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S4] sample/py の全 18 ケースが C++ で compile + run できる。

### P1: Julia native backend

文脈: [docs/ja/plans/p1-julia-native-backend.md](../plans/p1-julia-native-backend.md)

1. [x] [ID: P1-JULIA-NATIVE-01-S1] `src/toolchain/emit/julia/` 配下に emitter パッケージを作成する。
2. [x] [ID: P1-JULIA-NATIVE-01-S2] `src/runtime/julia/built_in/py_runtime.jl` を作成する。
3. [x] [ID: P1-JULIA-NATIVE-01-S3] smoke テスト作成、`transpiler_versions.json`・`check_py2x_profiles.json`・`docs/ja/language/index.md` を更新する。
4. [x] [ID: P1-JULIA-NATIVE-01-S4] smoke テストが通ることを確認する。

### P2: EAST1 パーサーから noncpp_runtime_call を除去

文脈: [docs/ja/plans/p2-remove-noncpp-runtime-call-from-east1.md](../plans/p2-remove-noncpp-runtime-call-from-east1.md)

1. [x] [ID: P2-REMOVE-NONCPP-RUNTIME-CALL-01] `core_expr_resolution_semantics.py` から `noncpp_*` フィールド生成を除去する。
2. [x] [ID: P2-REMOVE-NONCPP-RUNTIME-CALL-02] `core_expr_attr_subscript_annotation.py` から `noncpp_*` 伝播ロジックを除去する。
3. [x] [ID: P2-REMOVE-NONCPP-RUNTIME-CALL-03] `core_runtime_call_semantics.py` / `core_expr_attr_call_annotation.py` から不要関数を除去する。
4. [x] [ID: P2-REMOVE-NONCPP-RUNTIME-CALL-04] 既存テストのリグレッションがないことを検証する。

### P2: backend に link-output manifest 入力を必須化

文脈: [docs/ja/plans/p2-require-link-output-manifest.md](../plans/p2-require-link-output-manifest.md)

1. [x] [ID: P2-REQUIRE-LINK-MANIFEST-01] `loader.py` の raw EAST3 フォールバックを除去する。

### P2: linker サブモジュール import 解決

文脈: [docs/ja/plans/p2-linker-submodule-import-resolution.md](../plans/p2-linker-submodule-import-resolution.md)

1. [x] [ID: P2-LINKER-SUBMODULE-IMPORT-01] `program_loader.py` の `ImportFrom` 処理で import names のサブモジュール解決を追加する。
2. [x] [ID: P2-LINKER-SUBMODULE-IMPORT-02] 既存テストのリグレッションがないことを検証する。

### P3: pyobj list alias escape 解析を EAST3 パスへ移行

文脈: [docs/ja/plans/p3-pyobj-list-escape-to-east3.md](../plans/p3-pyobj-list-escape-to-east3.md)

1. [ ] [ID: P3-PYOBJ-LIST-ESCAPE-01] lifetime_analysis_pass に list alias escape 解析を追加し、FunctionDef.meta に結果を付与する。
2. [ ] [ID: P3-PYOBJ-LIST-ESCAPE-02] C++ emitter を meta 参照に切り替え、`_collect_pyobj_runtime_list_alias_names` を除去する。
3. [ ] [ID: P3-PYOBJ-LIST-ESCAPE-03] `analysis.py` の `_collect_assigned_name_types` を除去する（依存消滅確認後）。
4. [ ] [ID: P3-PYOBJ-LIST-ESCAPE-04] ユニットテストを追加し、既存 pyobj list テストのリグレッションがないことを検証する。

### P4: Dart native backend

文脈: [docs/ja/plans/p4-dart-native-backend.md](../plans/p4-dart-native-backend.md)

1. [x] [ID: P4-DART-NATIVE-01-S1] `src/toolchain/emit/dart/` 配下に emitter パッケージを作成する。
2. [x] [ID: P4-DART-NATIVE-01-S2] `src/runtime/dart/built_in/py_runtime.dart` を作成する。
3. [x] [ID: P4-DART-NATIVE-01-S3] smoke テスト作成、`transpiler_versions.json`・`check_py2x_profiles.json`・`docs/ja/language/index.md` を更新する。
4. [x] [ID: P4-DART-NATIVE-01-S4] smoke テストが通ることを確認する。

### P5: C# multi-module emit parity

文脈: [docs/ja/plans/p5-cs-multimodule-emit-parity.md](../plans/p5-cs-multimodule-emit-parity.md)

1. [x] [ID: P5-CS-MULTIMODULE-01] C# emitter に `emit_main` フラグを追加し、entry module 以外では `Main` を生成しない。クラス名をモジュール ID ベースでユニーク化する。
2. [x] [ID: P5-CS-MULTIMODULE-02] sub-module 間の `using` / namespace 参照を C# の namespace 規約に合わせて修正する。
3. [x] [ID: P5-CS-MULTIMODULE-03] `cs.py` の runtime 生成を S1/S2 の修正に合わせて整合させる。
4. [x] [ID: P5-CS-MULTIMODULE-04] `pytra-cli.py` の C# build/run を `mcs` + `mono` 方式に修正する。
5. [ ] [ID: P5-CS-MULTIMODULE-05] `runtime_parity_check.py --targets cs` で sample/py の全 18 ケースが PASS することを確認する。

### P7: Zig native backend

文脈: [docs/ja/plans/p7-zig-native-backend.md](../plans/p7-zig-native-backend.md)

1. [x] [ID: P7-ZIG-NATIVE-01-S1] `src/toolchain/emit/zig/` 配下に emitter パッケージを作成する。
2. [x] [ID: P7-ZIG-NATIVE-01-S2] `src/runtime/zig/built_in/py_runtime.zig` を作成する。
3. [x] [ID: P7-ZIG-NATIVE-01-S3] smoke テスト作成、`transpiler_versions.json`・`check_py2x_profiles.json`・`docs/ja/language/index.md` を更新する。
4. [x] [ID: P7-ZIG-NATIVE-01-S4] smoke テストが通ることを確認する。
