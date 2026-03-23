# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-23（完了タスクをアーカイブへ移動）

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
16. [x] [ID: P0-OBJECT-T-MIGRATION-04-S5] `gc.h`/`gc.cpp` を削除する。（全 generated .cpp が rc<T> 不使用になった時点で実施。P0-22 と連動）

**フェーズ 5: テスト・検証**

17. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S1] `test_py2cpp_features.py` の全コンパイル + 実行テストが通る。
18. [x] [ID: P0-OBJECT-T-MIGRATION-05-S2] `test_cpp_runtime_type_id.py` の type_id テストが通る。
19. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S3] selfhost multi-module transpile が動作する。
20. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S4] sample/py の全 18 ケースが C++ で compile + run できる。


#### P0-22: REPO_ROOT 修正 + import alias 解決 + conftest extern 関数修正

文脈: [docs/ja/plans/p0-cpp-repo-root-and-import-alias-fix.md](../plans/p0-cpp-repo-root-and-import-alias-fix.md)

1. [x] [ID: P0-REPO-ROOT-IMPORT-FIX-S1] include path 生成の整合性確保（`_module_name_to_cpp_include` が `-I` フラグで解決可能なパスを生成することを保証）
2. [x] [ID: P0-REPO-ROOT-IMPORT-FIX-S2] `REPO_ROOT` を `parents[5]` に修正する（S1 完了後）
3. [x] [ID: P0-REPO-ROOT-IMPORT-FIX-S3] `_resolve_imported_symbol_cpp_target` で bare module name を正規化（`math` → `pytra.std.math`）
4. [x] [ID: P0-REPO-ROOT-IMPORT-FIX-S4] `build_multi_cpp.py` の generated source 自動リンク拡張

進捗:
- 2026-03-22: conftest extern stripping 修正済み。runtime_symbol_index.json の utils module パス修正済み。
- 2026-03-22: REPO_ROOT parents[5] + call.py normalize コミット済み。S2,S3 完了。テスト 234 passed (78%)。
- 2026-03-23: S1 完了。user module include を CppEmitter から除去し multifile_writer に一元化。`_includes_from_resolved_dependencies` の `user_module_dependencies_v1` → `#include "helper.h"` 生成を停止。bare_parent_relative_import 等 3 テスト修正。
- 2026-03-23: S4 完了。`build_multi_cpp.py` の `_collect_generated_cpp_sources` をハードコードリストから include 追跡ベースの自動リンクに変更。モジュールソースと include ヘッダーから `#include` を走査し、参照された generated `.cpp` のみをリンク。multi-file テスト 18/22 pass（残 4 件は P0-18 Object<T> 既存バグ）。

#### P0-23: Rust backend コンテナ参照セマンティクス導入

文脈: [docs/ja/plans/p0-rs-container-ref-semantics.md](../plans/p0-rs-container-ref-semantics.md)
仕様: [docs/ja/spec/spec-emitter-guide.md §10](../spec/spec-emitter-guide.md#10-コンテナ参照セマンティクス要件)

**フェーズ 1: runtime に PyList\<T\> 追加**

1. [x] [ID: P0-RS-CONTAINER-REF-S1] `py_runtime.rs` に `PyList<T>` (`Rc<RefCell<Vec<T>>>`) + メソッド群を実装する。

**フェーズ 2: emitter の list 型マッピング変更**

2. [ ] [ID: P0-RS-CONTAINER-REF-S2] emitter の `list[T]` 型を `PyList<T>` で生成するように変更する（リテラル・宣言・append・添字・len・for ループ）。

**フェーズ 3: §10.5 ヒント対応**

3. [ ] [ID: P0-RS-CONTAINER-REF-S3] `container_value_locals_v1` ヒントを読み取り、ヒントありの変数は `Vec<T>` 値型に縮退する。

**フェーズ 4: テスト・検証**

4. [ ] [ID: P0-RS-CONTAINER-REF-S4] 既存 5 pass ケース（01-04 PNG + 17 テキスト）がリグレッションしないことを検証する。

### P1: Dart emitter デッドコード除去

文脈: [docs/ja/plans/p1-dart-dead-code-removal.md](../plans/p1-dart-dead-code-removal.md)

1. [x] [ID: P1-DART-DEAD-CODE-S1] 旧方式のハードコード関数群（`_runtime_symbol_alias_expr` 等 14 関数）を削除する。
2. [x] [ID: P1-DART-DEAD-CODE-S2] sample/py 全 18 ケースが Dart でバイナリ一致することを検証する。

進捗:
- 2026-03-23: S1-S2 完了。14 関数 + 未使用 import 削除。18/18 PASS。

### P1: Dart emitter ランタイムヘルパー重複排除

文脈: [docs/ja/plans/p1-dart-runtime-helper-dedup.md](../plans/p1-dart-runtime-helper-dedup.md)

1. [x] [ID: P1-DART-HELPER-DEDUP-S1] `__pytraPrintRepr` 等のヘルパーを `py_runtime.dart` に集約する。
2. [x] [ID: P1-DART-HELPER-DEDUP-S2] emitter のインライン生成メソッド（`_emit_print_helper` 等）を除去する。
3. [x] [ID: P1-DART-HELPER-DEDUP-S3] sample/py 全 18 ケースが Dart でバイナリ一致することを検証する。

進捗:
- 2026-03-23: S1-S3 完了。`__pytra` prefix → `pytra` prefix（Dart `_` private 制約）。hand-written `std/pathlib.dart` 追加。`cast()` → `as` キャスト生成。18/18 PASS。

### P1: Swift sample parity（EAST3 生成 utils 有効化）

文脈: [docs/ja/plans/p1-swift-gif-lzw-parity.md](../plans/p1-swift-gif-lzw-parity.md)

1. [x] [ID: P1-SWIFT-PARITY-S1] emitter の `let` パラメータ問題を修正（コンテナ型パラメータの `var` 再宣言）。
2. [ ] [ID: P1-SWIFT-PARITY-S2] `pytra.utils.*` スキップを解除し EAST3 生成版を有効化する。→ **§10 ブロック**
3. [ ] [ID: P1-SWIFT-PARITY-S3] py_runtime.swift から画像スタブ（`write_rgb_png` / `__pytra_save_gif`）を除去する。→ **§10 ブロック**
4. [ ] [ID: P1-SWIFT-PARITY-S4] sample/py 01-16 が Swift でバイナリ一致することを検証する。

進捗:
- 2026-03-23: extern_var_v1 対応、int32 型マッピング、PyFile / open() 追加、let→var 修正完了。PNG 4/4 PASS。
- 2026-03-23: EAST3 生成 utils/png.swift を有効化して検証。§10 コンテナ参照セマンティクス（値型 `[Any]` の関数内変更が呼び出し元に反映されない）がブロッカーであることを確認。GIF/PNG とも EAST3 生成版は §10 解決まで使用不可。utils スキップと py_runtime スタブを維持。

### P2: built-in 依存を EAST1 → linker 経由で解決

文脈: [docs/ja/plans/p2-builtin-dependency-via-linker.md](../plans/p2-builtin-dependency-via-linker.md)

1. [x] [ID: P2-BUILTIN-VIA-LINKER-01] EAST1 パーサーに built-in → module 対応テーブルを追加し、`import_bindings` に暗黙依存を記録する。
2. [x] [ID: P2-BUILTIN-VIA-LINKER-02] linker が `pytra.built_in.*` を link-output manifest に含めることを検証する。
3. [ ] [ID: P2-BUILTIN-VIA-LINKER-03] 全 emitter（C++ 含む）から `py_runtime.*` / ヘッダーの決め打ちバンドルを除去する（`@extern` 関数の扱い確定後）。
4. [x] [ID: P2-BUILTIN-VIA-LINKER-04] 既存テストのリグレッションがないことを検証する。

### P2: 全 backend 共通テストスイートの整備

文脈: [docs/ja/plans/p2-cross-backend-common-test-suite.md](../plans/p2-cross-backend-common-test-suite.md)

1. [x] [ID: P2-COMMON-TEST-S1] 共通テスト基盤 — `runtime_parity_check.py --case-root fixture --all-samples` で 128 fixture を全言語実行可能
2. [x] [ID: P2-COMMON-TEST-S2] 言語ごとの unsupported fixture を `_LANG_UNSUPPORTED_FIXTURES` に登録し、skip 分類する
3. [ ] [ID: P2-COMMON-TEST-S3] `test_py2cpp_features.py` から共通化済みテストを除去し、C++ 固有テストのみに絞る
4. [x] [ID: P2-COMMON-TEST-S4] smoke テストのインライン Python ソースを `test/fixtures/` に棚卸し（print 付き main guard 追加）

進捗:
- 2026-03-23: S1 完了。`runtime_parity_check.py` の fixture 対応で代替達成。pytest ラッパーは不要と判断。
- 2026-03-23: S2 完了。`_LANG_UNSUPPORTED_FIXTURES` を `runtime_parity_check.py` に追加。Zig の初期 skip リストを設定。他言語は parity 実行結果を見て追加。

### P2: test/transpile/ → work/transpile/ 移行

1. [ ] [ID: P2-TRANSPILE-DIR-MIGRATE-S1] `test/transpile/` の参照を `work/transpile/` に変更し、`.gitignore` を更新する

### P2: ContainerValueLocalHintPass 汎化（全 backend 共通化）

文脈: [docs/ja/plans/p2-container-value-local-hint-generalize.md](../plans/p2-container-value-local-hint-generalize.md)

1. [x] [ID: P2-CONTAINER-HINT-GENERALIZE-S1] `CppListValueLocalHintPass` を `ContainerValueLocalHintPass` に汎化（target_lang ガード除去、ヒントキー統一）
2. [x] [ID: P2-CONTAINER-HINT-GENERALIZE-S2] linker `_materialize_container_hints` の target フィルタ除去 + ヒントキー汎化
3. [x] [ID: P2-CONTAINER-HINT-GENERALIZE-S3] テスト追加（非 C++ target でヒント populated 確認）+ C++ 回帰なし確認

進捗:
- 2026-03-23: S1-S3 完了。ContainerValueLocalHintPass が全 target で実行される。旧名 CppListValueLocalHintPass / cpp_value_list_locals_v1 は除去済み。

### P2: Swap ノードを Name 限定に制約し、Subscript swap を Assign 展開する

文脈: [docs/ja/plans/p2-swap-name-only-contract.md](../plans/p2-swap-name-only-contract.md)

1. [x] [ID: P2-SWAP-NAME-ONLY-S1] swap 検出で Subscript を含むケースを一時変数付き Assign 列に展開する
2. [x] [ID: P2-SWAP-NAME-ONLY-S2] テスト追加（Name swap → Swap ノード、Subscript swap → Assign 展開）

進捗:
- 2026-03-23: S1-S2 完了。Name-Name swap は Swap ノード、Subscript 含む swap は 3 文の Assign 列に展開。7 テスト追加。

### P2: EAST 型推論改善（tuple target / VarDecl / math.* / decl_type）

文脈: [docs/ja/plans/p2-east-type-inference-fixes.md](../plans/p2-east-type-inference-fixes.md)

1. [x] [ID: P2-EAST-TYPE-FIX-S1] Assign の tuple target で value の resolved_type から要素型を抽出し name_types に登録する
2. [x] [ID: P2-EAST-TYPE-FIX-S2] VarDecl type に value.resolved_type fallback を追加する（S1 で自動解決、追加修正不要）
3. [x] [ID: P2-EAST-TYPE-FIX-S3] math.* の resolved_type が unknown になるケースを修正する（`from pytra.std import math` スタイルの import_symbols チェック追加）

進捗:
- 2026-03-23: S1 tuple target の name_types 更新を `core_stmt_parser.py` に追加。S3 `_SH_IMPORT_SYMBOLS` チェックを `core_expr_attr_call_annotation.py` に追加。全 sample で VarDecl object/unknown と Assign unknown decl_type がゼロに。S2 は S1+S3 で自動解決。

### P2: tuple 分割代入の `_` 要素に unused: true を付与

1. [x] [ID: P2-TUPLE-UNDERSCORE-UNUSED-S1] tuple 分割代入で target 名が `_` の場合に unused: true を付与する

進捗:
- 2026-03-23: S1 完了。`east2_to_east3_unused_var_detection.py` で Tuple target の個々の Name 要素に対して unused 判定を追加。`_` / `_unused` 等が正しく `unused: true` になることを確認。

### P2: cast() の resolved_type 修正 + list.pop() の generic 解決

1. [x] [ID: P2-CAST-POP-FIX-S1] `cast(T, value)` の Call.resolved_type に第 1 引数の型名を設定する
2. [x] [ID: P2-CAST-POP-FIX-S2] `list[T].pop()` の戻り値型を要素型 `T` に解決する

進捗:
- 2026-03-23: S1 完了。`_sh_infer_known_name_call_return_type` に `cast` 分岐追加。`cast(Path, value)` → `Path`、`cast(str, value)` → `str`。
- 2026-03-23: S2 完了。`_lookup_builtin_method_return` の `list` セクションに generic 解決追加。`list[int].pop()` → `int64`、`list[str].pop()` → `str`。

### P2: cast() に semantic_tag 追加 + 非 pytra import_bindings フィルタ

1. [x] [ID: P2-CAST-SEMTAG-S1] cast() の Call ノードに `semantic_tag: "cast.typed"` を設定し、emitter が callee_name ハードコードなしで判定できるようにする
2. [x] [ID: P2-HOST-IMPORT-FILTER-S1] 非 pytra import_bindings に `host_only: true` フラグを付与する

進捗:
- 2026-03-23: S1 完了。`_BUILTIN_SEMANTIC_TAGS` に `cast` 追加、`_resolve_builtin_named_call_kind` と `_apply_builtin_named_call_dispatch` に cast ハンドラ追加。
- 2026-03-23: S2 完了。`_is_host_only_module` で非 pytra module_id を判定し `host_only: true` を import_binding に付与。emitter は `host_only` をチェックしてスキップ可能。

### P2: runtime_call_adapter_kind 拡充 + extern_var_v1 実装

1. [x] [ID: P2-ADAPTER-EXTERN-S1] `runtime_call_adapter_kind` を `runtime_module_id` の group から自動導出する（built_in → "builtin"、std/utils → "extern_delegate"）
2. [x] [ID: P2-ADAPTER-EXTERN-S2] `extern_var_v1` の型注釈制約を緩和し `extern(expr)` フォールバック値もサポートする

進捗:
- 2026-03-23: S1 完了。`_set_runtime_binding_fields` に group ベースの adapter_kind 自動導出を追加。`perf_counter` → `extern_delegate`、`py_print` → `builtin` 等が自動設定。
- 2026-03-23: S2 完了。`core_extern_semantics.py` の `annotation` 制約（Any/object のみ）を除去し、`extern(math.pi)` のような非 Constant 引数もサポート。`pi: float = extern(math.pi)` → `extern_var_v1` が付与されるように。

### P2: verify_sample_outputs.py を除去し runtime_parity_check.py に統一する

文脈: emitter guide §13（parity check の正本ツール）

1. [x] [ID: P2-REMOVE-VERIFY-SAMPLE-S1] `regenerate_samples.py` の `--verify-cpp-on-diff` を `runtime_parity_check.py --targets cpp` に置換
2. [x] [ID: P2-REMOVE-VERIFY-SAMPLE-S2] `verify_sample_outputs.py` を削除し、docs の参照を更新

進捗:
- 2026-03-23: S1-S2 完了。`verify_sample_outputs.py` を削除。`regenerate_samples.py` / `run_regen_on_version_bump.py` / `spec-tools.md` / `spec-emitter-guide.md` / `sample/README.md` / `sample/README-ja.md` を更新。

### P2: C++ multi-file emit の runtime east パス解決修正

1. [x] [ID: P2-CPP-RUNTIME-EAST-PATH-S1] `multifile_writer.py` の `_RUNTIME_EAST_ROOT_STR` / `_RUNTIME_CPP_ROOT_STR` の parents index を修正 + `gen_makefile_from_manifest.py` のパス解決を絶対パス化

進捗:
- 2026-03-23: `multifile_writer.py` の `parents[3]` → `parents[4]` 修正で runtime east モジュールが正しいラベル（`built_in/io_ops` 等）で emit されるように。`gen_makefile_from_manifest.py` のソースパス・include パス・obj パスを絶対パスに resolve し、`make -C emit/` 実行時のパス不一致を解消。@extern モジュールの欠落 .cpp をスキップ。
- 2026-03-23: `program_writer.py` の `_PROJECT_ROOT` パス修正（`parents[3] / "src" / "runtime"` → `parents[3] / "runtime"`）で canonical generated ヘッダー（`generated/std/pathlib.h` 等）が正しくコピーされるように。runtime `.east` 再 transpile による `.tag` エラー解消。

### P2: EAST3 型推論バグ修正（Nim 担当報告 4 件）

1. [x] [ID: P2-NIM-EAST-FIX-S1] Swap left/right 空ノード修正（sample 12）— P2-SWAP-NAME-ONLY で解決済み
2. [x] [ID: P2-NIM-EAST-FIX-S2] returns vs return_type 不整合修正（sample 18）
3. [x] [ID: P2-NIM-EAST-FIX-S3] VarDecl name=None 不正ノード防止（sample 07）— 防御ガード追加 + 先行修正で解消済み
4. [x] [ID: P2-NIM-EAST-FIX-S4] list[unknown] 空リスト初期化の型を後続 Assign から遡及解決（sample 07, 08, 09, 13）— 先行の型推論修正（P2-EAST-TYPE-FIX）で解消済み

進捗:
- 2026-03-23: S1 P2-SWAP-NAME-ONLY で解決済み。S2 type propagation に FunctionDef.returns 同期を追加。S3 VarDecl 生成に空名ガード追加。S4 先行修正で全 sample の list[unknown] がゼロに。

### P2: runtime_parity_check.py の fixture 全言語対応

1. [x] [ID: P2-FIXTURE-PARITY-S1] fixture の自動列挙（`--all-samples --case-root fixture`）と negative test（`ng_*`）のスキップ
2. [x] [ID: P2-FIXTURE-PARITY-S2] emitter guide に fixture parity check の使い方を追記

進捗:
- 2026-03-23: S1 完了。`collect_fixture_case_stems()` を追加し `--all-samples --case-root fixture` で 131 fixture を自動列挙。`ng_*` は除外。S2 完了。emitter guide §13 に fixture parity の使い方とチェックリスト項目を追加。

### P3: Nim emitter spec-emitter-guide 準拠改善

文脈: [docs/ja/plans/p3-nim-emitter-spec-compliance.md](../plans/p3-nim-emitter-spec-compliance.md)
仕様: [docs/ja/spec/spec-emitter-guide.md](../spec/spec-emitter-guide.md)

1. [x] [ID: P3-NIM-SPEC-S1] `build_import_alias_map` を利用する（§7）
2. [ ] [ID: P3-NIM-SPEC-S2] コンテナ参照セマンティクス導入（§10）— `ref seq[T]` ラッパー + `container_value_locals_v1` ヒント対応
3. [x] [ID: P3-NIM-SPEC-S3] `yields_dynamic: true` の明示処理を追加する（§11）
4. [ ] [ID: P3-NIM-SPEC-S4] `runtime_parity_check.py` に Nim toolchain を登録し全 18 sample PASS を達成する（§13）

進捗:
- 2026-03-23: 起票。§1/§2/§3/§4/§5.1/§6/§8/§9/§12 は修正済み。emitter パイプライン経由で 12/18 sample がバイナリ一致（残 6 件は EAST3 型推論不足）。
- 2026-03-23: S1 完了（`build_import_alias_map` 導入）、S3 完了（`yields_dynamic` 明示対応）。残 S2（コンテナ ref）、S4（parity tool）。

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


### P5: Callable 型サポート（func ノードの型付与 + 高階関数型推論）

文脈: [docs/ja/plans/p5-callable-type-support.md](../plans/p5-callable-type-support.md)

**フェーズ 1: 既知関数の func.resolved_type 設定**

1. [ ] [ID: P5-CALLABLE-TYPE-S1] builtin 関数（`len`, `str`, `print` 等）の func ノードに `callable[戻り値型]` を設定する
2. [ ] [ID: P5-CALLABLE-TYPE-S2] stdlib 関数（`math.sqrt`, `perf_counter` 等）の func ノードに `callable[戻り値型]` を設定する
3. [ ] [ID: P5-CALLABLE-TYPE-S3] user-defined 関数の func ノードに `fn_return_types` から `callable[戻り値型]` を設定する

**フェーズ 2: TypeExpr への CallableType 追加**

4. [ ] [ID: P5-CALLABLE-TYPE-S4] `spec-east.md` §6.3 に `CallableType` kind を追加する
5. [ ] [ID: P5-CALLABLE-TYPE-S5] `type_expr.py` に `CallableType` のパース・正規化を実装する
6. [ ] [ID: P5-CALLABLE-TYPE-S6] フェーズ 1 の `callable[ret]` 簡易形を `CallableType` に置換する

**フェーズ 3: 高階関数の型推論**

7. [ ] [ID: P5-CALLABLE-TYPE-S7] `Callable[[T1, T2], R]` 型注釈のパースを実装する
8. [ ] [ID: P5-CALLABLE-TYPE-S8] callable 型変数の間接呼び出し `f(x)` で `Call.resolved_type` を `CallableType.return_type` から導出する
9. [ ] [ID: P5-CALLABLE-TYPE-S9] 高階関数パターンのテスト fixture を追加する

### P7: C++ test_py2cpp_features.py テストパス率改善

文脈: [docs/ja/plans/p7-cpp-test-pass-rate-improvement.md](../plans/p7-cpp-test-pass-rate-improvement.md)

1. [ ] [ID: P7-CPP-TEST-PASS-S1] Multi-file cross-module include 生成修正（~12件）
2. [ ] [ID: P7-CPP-TEST-PASS-S2] conftest 生成 C++ の Object<T> 互換修正（~5件）
3. [ ] [ID: P7-CPP-TEST-PASS-S3] Any/Object<void> runtime 修正（~4件）
4. [ ] [ID: P7-CPP-TEST-PASS-S4] その他テスト修正（~10件）

進捗:
- 2026-03-22: 192/107 (64%) → 268/31 (89.3%)。+76テスト改善。残り31件の計画書起票。
- 2026-03-23: 250/49 → 285/15 (95%)。+35テスト改善。主な修正: wildcard テスト期待値、generated-only include フォールバック、Any is None emit、module_id 正規化、scope_exit.h include、user_module_dependencies pytra.* skip、py_to_bool object unbox、imported class Object<T> 統一、enumerate TupleTarget 型修正、runtime_expr Object<void> iter スタブ化、テスト期待値多数更新。

