# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-21（P0-GPP-COMPILE-HEADERS-01, P1-2/3/4/5, P7-1/2 をアーカイブへ移動）

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

#### P0-11: PowerShell native emitter 実行 parity

文脈: [docs/ja/plans/p0-powershell-native-emitter-execution-parity.md](../plans/p0-powershell-native-emitter-execution-parity.md)

1. [ ] [ID: P0-PS-EXEC-PARITY-01-S1] FunctionDef の `self` パラメータを除外せず `$self` として残す。クラスメソッド呼び出し時に第1引数として渡す。
2. [ ] [ID: P0-PS-EXEC-PARITY-01-S2] `bytearray`, `bytes`, `enumerate`, `sorted`, `reversed`, `zip` 等を `__pytra_*` ランタイム関数にマッピング。不足 runtime 関数を追加。
3. [ ] [ID: P0-PS-EXEC-PARITY-01-S3] `math.sqrt` → `[Math]::Sqrt` 等の stdlib Attribute Call を直接 PowerShell 構文に変換。
4. [ ] [ID: P0-PS-EXEC-PARITY-01-S4] Assign でタプルターゲットが左辺にある場合、一時変数展開を emit する。
5. [ ] [ID: P0-PS-EXEC-PARITY-01-S5] Call の func がクラス名の場合、コンストラクタ関数呼び出しとして emit する。
6. [ ] [ID: P0-PS-EXEC-PARITY-01-S6] `test/unit/toolchain/emit/powershell/test_py2ps_smoke.py` に pwsh 実行テストを追加し、主要 fixture の実行成功を検証する。

#### P0-12: pytra-cli.py が C++ 固有オプションを転送しない

文脈: [docs/ja/plans/p0-12-py2x-cpp-options-forwarding.md](../plans/p0-12-py2x-cpp-options-forwarding.md)

1. [ ] [ID: P0-PY2X-CPP-OPTIONS-01] CLI テスト群を `toolchain/emit/cpp/cli.py` 直接呼び出しに変更する

#### P0-13: テストが旧 src/backends/cpp/cli.py パスを参照

文脈: [docs/ja/plans/p0-13-cli-path-migration.md](../plans/p0-13-cli-path-migration.md)

1. [ ] [ID: P0-CLI-PATH-MIGRATION-01] テスト内の旧 cli.py パスを新パスに更新する

#### P0-15: エミッター出力変化によるテストアサーション不一致

文脈: [docs/ja/plans/p0-15-emitter-output-assertions.md](../plans/p0-15-emitter-output-assertions.md)

1. [ ] [ID: P0-EMITTER-OUTPUT-ASSERTIONS-01] テストアサーションを新エミッター出力に追従させる

#### P0-16: runtime include パスのテストアサーション不一致

文脈: [docs/ja/plans/p0-16-runtime-include-paths.md](../plans/p0-16-runtime-include-paths.md)

1. [ ] [ID: P0-RUNTIME-INCLUDE-PATHS-01] テストアサーションを新インクルードパスに追従させる

#### P0-17: emitter 旧 API 出力の一掃

文脈: [docs/ja/plans/p0-emitter-legacy-api-cleanup.md](../plans/p0-emitter-legacy-api-cleanup.md)

1. [ ] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S1] emitter の `object_new` / `PyListObj` 生成箇所を `object(...)` / `list<object>` に置換。
2. [ ] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S2] emitter の `obj_to_list_ref_or_raise` / `py_object_try_cast` を `object::as<T>()` に置換。
3. [ ] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S3] emitter の `py_list_at_ref` / `py_at(tuple)` を新 API に置換。
4. [ ] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S4] `pytra::utils` namespace の include パス修正。
5. [ ] [ID: P0-EMITTER-LEGACY-API-CLEANUP-02-S5] テストアサーション（`test_cpp_runtime_type_id.py`）を新 API に追従。

> P0-17 の残存問題（include 順序による SFINAE 失敗、object(rc\<dict\>) 変換不可）は P0-18 (Object\<T\> 移行) で根本解決する。

#### P0-18: Object\<T\> 移行 — ControlBlock + テンプレート view 方式

文脈: [docs/ja/plans/p0-object-t-migration.md](../plans/p0-object-t-migration.md)
仕様: [docs/ja/spec/spec-object.md](../spec/spec-object.md)

**フェーズ 1: ControlBlock + Object\<T\> の導入（runtime 並行運用）**

1. [ ] [ID: P0-OBJECT-T-MIGRATION-01-S1] `core/object.h` に `ControlBlock`, `Object<T>`, `make_object<T>`, `upcast<To>` を実装する。
2. [ ] [ID: P0-OBJECT-T-MIGRATION-01-S2] `core/object.h` に `is_subtype` 区間判定を実装する（既存の `type_id_support.h` と並行）。
3. [ ] [ID: P0-OBJECT-T-MIGRATION-01-S3] `TypeInfo` 型テーブルと `g_type_table` を実装する（リンカーの type_id 割り当てと統合）。

**フェーズ 2: emitter の移行（Object\<T\> 形式の C++ を生成）**

4. [ ] [ID: P0-OBJECT-T-MIGRATION-02-S1] emitter のクラス定義 emit を `Object<T>` 対応に変更する。
5. [ ] [ID: P0-OBJECT-T-MIGRATION-02-S2] emitter の変数宣言・代入・upcast emit を `Object<T>` の view 変換に変更する。
6. [ ] [ID: P0-OBJECT-T-MIGRATION-02-S3] emitter の isinstance/downcast emit を `is_subtype` + `static_cast` に変更する。
7. [ ] [ID: P0-OBJECT-T-MIGRATION-02-S4] emitter の関数引数・戻り値の型 emit を `Object<T>` 対応に変更する。
8. [ ] [ID: P0-OBJECT-T-MIGRATION-02-S5] emitter の Any/object 型 emit を型消去版 `Object<>` に変更する。

**フェーズ 3: list\<T\> / dict\<K,V\> の Object 統合**

9. [ ] [ID: P0-OBJECT-T-MIGRATION-03-S1] `list<T>` から `RcObject` 継承を除去し、`Object<list<T>>` で管理する形に移行する。
10. [ ] [ID: P0-OBJECT-T-MIGRATION-03-S2] `dict<K,V>` から `RcObject` 継承を除去し、`Object<dict<K,V>>` で管理する形に移行する。
11. [ ] [ID: P0-OBJECT-T-MIGRATION-03-S3] emitter の list/dict boxing を `Object<list<T>>` / `Object<dict<K,V>>` に変更する。

**フェーズ 4: 旧型の撤去**

12. [ ] [ID: P0-OBJECT-T-MIGRATION-04-S1] `RcObject` クラスを削除する。
13. [ ] [ID: P0-OBJECT-T-MIGRATION-04-S2] `rc<T>` テンプレートを削除する。
14. [ ] [ID: P0-OBJECT-T-MIGRATION-04-S3] 旧 `object` 型を削除し、`Object<void>` または新 `object` typedef に統一する。
15. [ ] [ID: P0-OBJECT-T-MIGRATION-04-S4] `tagged_value.h` を削除する（ControlBlock に統合済み）。
16. [ ] [ID: P0-OBJECT-T-MIGRATION-04-S5] `gc.h` を `ControlBlock` ベースの rc 管理に書き換える。

**フェーズ 5: テスト・検証**

17. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S1] `test_py2cpp_features.py` の全コンパイル + 実行テストが通る。
18. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S2] `test_cpp_runtime_type_id.py` の type_id テストが通る。
19. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S3] selfhost multi-module transpile が動作する。
20. [ ] [ID: P0-OBJECT-T-MIGRATION-05-S4] sample/py の全 18 ケースが C++ で compile + run できる。

### P1: パイプライン段分離 — compile / link / emit の独立化

#### P1-2: backend_registry 依存の除去

文脈: [docs/ja/plans/p1-backend-registry-decoupling.md](../plans/p1-backend-registry-decoupling.md)

1. [x] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S1] `pytra-cli.py` の C++ emit パスを `east2cpp.py` サブプロセスに変更し、`backend_registry` import を除去。→ pytra-cli.py の import グラフに toolchain.emit.* が一切含まれない。
2. [x] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S2] `pytra-cli.py` の非 C++ emit パスを `east2x.py` サブプロセスに変更。→ S1 と同時に完了。
3. [x] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S3] `pytra-cli.py` から `backend_registry_static` import を除去。→ C++ emitter のみ直接 import。非 C++ backend は import グラフに含まれない。
4. [x] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S4] selfhost compile+link で 65 モジュール（以前 151）。非 C++ backend 74 件が完全に消えた（57% 削減）。

#### P1-5: 各言語 emit ラッパーの個別 emitter 直接呼び出し化

文脈: 現在 `toolchain/emit/{rs,cs,go,...}.py` は `toolchain/emit/all.py` に委譲しており、結果として全 backend を import している。`cpp.py` と同様に各言語が自分の emitter だけを直接呼ぶ形にし、`all.py` を廃止する。

1. [x] [ID: P1-EMIT-DIRECT-CALL-01] 14 言語のラッパーを個別 emitter 直接呼び出しに変更。各ラッパーは自分の emitter のみ import。
2. [x] [ID: P1-EMIT-DIRECT-CALL-02] `toolchain/emit/all.py` を削除。

#### P1-3: C++ emitter @staticmethod 対応

文脈: [docs/ja/plans/p1-cpp-staticmethod-emit.md](../plans/p1-cpp-staticmethod-emit.md)

1. [x] [ID: P1-CPP-STATICMETHOD-EMIT-01] `emit_function` で `@staticmethod`/`@classmethod` デコレータを検出し、`static` を emit するよう修正する

#### P1-4: C++ emitter Path が rc<Path> でなく bare 型で宣言される

文脈: [docs/ja/plans/p1-cpp-path-rc-type.md](../plans/p1-cpp-path-rc-type.md)

1. [x] [ID: P1-CPP-PATH-RC-TYPE-01] `pathlib.east` の `class_storage_hint` を `"value"` から `"ref"` に修正

### P7: selfhost 完全自立化

#### P7-1: native/compiler/ 完全削除

文脈: [docs/ja/plans/p7-selfhost-native-compiler-elim.md](../plans/p7-selfhost-native-compiler-elim.md)

1. [x] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S1] selfhost ビルドパイプラインを EAST3 JSON 入力専用に統一し、`transpile_cli.cpp` の `.py` シェルアウトパスを除去する。
2. [x] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S2] `emit_source_typed` のシェルアウトを除去。→ 生成 C++ emitter (transpile_to_cpp) の直接呼び出しに置換。シェルアウト補助関数を全削除。
3. [x] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S3] `src/runtime/cpp/compiler/` を削除。シェルアウトゼロ確認済み。契約インベントリから削除済みファイル参照を除去。

#### P7-2: selfhost multi-module transpile 基盤構築（S2 の前提）

文脈: [docs/ja/plans/p7-selfhost-multimodule-transpile.md](../plans/p7-selfhost-multimodule-transpile.md)

1. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S1] emitter モジュール群（`src/toolchain/emit/cpp/emitter/*.py`）の selfhost 制約準拠を監査し、違反箇所を列挙する。→ 文脈ファイルの決定ログに詳細記録。ブロッカー: 動的 dispatch 4件。
1a. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-01] `pytra.std.pathlib.Path` に `relative_to` / `with_suffix` を実装し、emitter の `from pathlib import Path` を移行。
1b. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-02] `pytra.std.re` に `compile` / `Pattern` を実装し、optimizer の `import re` を移行。
1c. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-03] `multifile_writer.py` の `import os` を `pytra.std` 経由に移行。
1d. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-04] CppEmitter の動的 mixin 注入（`_attach_cpp_emitter_helper_methods` の `setattr`/`__dict__`）を EAST3 mixin 展開による多重継承に置換する。`install_py2cpp_runtime_symbols` の `globals()` 注入を除去する。
2. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S2] `tools/build_selfhost.py` を multi-module transpile パイプライン（compile → link）に拡張する。→ `--multi-module` フラグで pytra-cli.py 経由の compile→link→emit パイプラインを実行。全 150 モジュール EAST3 コンパイル成功。パーサー修正（typing no-op、dict 文字列キー内 `:`、複数型引数 subscript）。依存チェーン全体の object レシーバ修正（40+ ファイル）。
3. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S3] selfhost 66 モジュールの C++ emit 完了。→ compile+link (pytra-cli.py --link-only) → emit (toolchain/emit/cpp.py) の 3 段パイプラインで 233 C++ ファイル (4.1MB) を生成。backend_registry 依存除去により 151→66 モジュールに削減。
4. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S4] リンカーの import 解決で `from toolchain.misc.transpile_cli import make_user_error` 等のシンボルが見つからない問題を調査・修正する。→ `module_export_table` に wildcard re-export 伝播を実装。`from X import *` による再エクスポートが export テーブルに反映されるようになり、151 モジュールの link に成功。wildcard バインディングの重複許容も追加。
