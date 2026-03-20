# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-19（P2/P6 完了→archive 移管、P7 子タスク具体化）

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

#### P0-1: .east → C++ ヘッダー生成パイプライン

文脈: [docs/ja/plans/p0-cpp-generated-runtime-pipeline.md](../plans/p0-cpp-generated-runtime-pipeline.md)

1. [x] [ID: P0-CPP-GENERATED-RUNTIME-PIPELINE-01] `src/runtime/cpp/generated/` が存在せず、native ヘッダー 15 箇所の `#include` が壊れている。`runtime_generation_manifest.json` に C++ built_in/std ターゲットを追加し、`.east` → `.h` 生成パイプラインを整備する。

#### P0-2: escape 解析で union type 引数への受け渡しを escape 判定する（最優先）

文脈: union type（`str | Path` 等）の引数に値を渡すとき、値は `object` に box される（ヒープ確保 + rc 管理）。これは escape と同義。escape 解析がこれを検出していないため、`Path` が value 最適化されて `RcObject` を継承せず、`object` に格納できない。

1. [x] [ID: P0-UNION-ARG-ESCAPE-01] パーサーで暫定検出: union type 引数を持つクラスを ref (gc_managed) に強制。
2. [x] [ID: P0-UNION-ARG-ESCAPE-02] `Path` が gc_managed（`RcObject` 継承 + `PYTRA_TYPE_ID`）として emit され、`object` に格納可能。
3. [x] [ID: P0-UNION-ARG-ESCAPE-03] escape 解析結果を `class_storage_hint` に反映する仕組みを実装。→ P0-ESCAPE-TO-STORAGE-HINT-01 で対応済み。

#### P0-3: escape 解析結果を class_storage_hint に反映する

文脈: [docs/ja/plans/p0-escape-analysis-to-storage-hint.md](../plans/p0-escape-analysis-to-storage-hint.md)

1. [x] [ID: P0-ESCAPE-TO-STORAGE-HINT-01-S1] `optimize_linked_program` で union type パラメータに含まれるクラスの `class_storage_hint` を `"ref"` に昇格する。
2. [x] [ID: P0-ESCAPE-TO-STORAGE-HINT-01-S2] `core_module_parser.py` の暫定判定を除去。
3. [x] [ID: P0-ESCAPE-TO-STORAGE-HINT-01-S3] `Path` がリンカー段で gc_managed になることを検証済み。

#### P0-4: 旧 object API + 旧互換モード一掃（最優先 — pathlib ビルドのブロッカー）

1. [x] [ID: P0-LEGACY-API-CLEANUP-01-S1] emitter の `make_object` 生成箇所を `object(...)` に置換。
2. [x] [ID: P0-LEGACY-API-CLEANUP-01-S2] emitter の `obj_to_rc_or_raise<T>` 生成箇所を `object::as<T>()` に置換。
3. [x] [ID: P0-LEGACY-API-CLEANUP-01-S3] runtime の `make_object` / `obj_to_rc_or_raise` 互換 shim を削除。
4. [x] [ID: P0-LEGACY-API-CLEANUP-01-S4] C++ list の value/pyobj モード互換（`cpp_list_model`）を削除する。ref モード統一。
5. [x] [ID: P0-LEGACY-API-CLEANUP-01-S5] pathlib repro が `out/cpp/` で g++ ビルドできることを検証する。→ P0-5 (link 統合) で解決。

#### P0-5: runtime .east を link パイプラインに統合

文脈: [docs/ja/plans/p0-runtime-east-in-link-pipeline.md](../plans/p0-runtime-east-in-link-pipeline.md)

1. [x] [ID: P0-RUNTIME-EAST-IN-LINK-PIPELINE-01-S1] `resolved_dependencies_v1` に含まれる runtime モジュールの .east を LinkedProgram に自動追加する。
2. [x] [ID: P0-RUNTIME-EAST-IN-LINK-PIPELINE-01-S2] `write_cpp_rendered_program` で runtime モジュールも link emit の出力に含める。
3. [x] [ID: P0-RUNTIME-EAST-IN-LINK-PIPELINE-01-S3] `_generate_runtime_east_headers`（standalone transpile）を廃止する。
4. [x] [ID: P0-RUNTIME-EAST-IN-LINK-PIPELINE-01-S4] emitter が生成する旧 object API（`make_object`, `obj_to_rc_or_raise`, `cpp_string_lit` globals 依存）を掃除し、新 object API（`unbox`/`as`/`is`/`_cpp_str_lit`）に統一する。後方互換不要。→ P0-4 S1-S3 で対応済み。
5. [x] [ID: P0-RUNTIME-EAST-IN-LINK-PIPELINE-01-S5] pathlib repro が `out/cpp/` で g++ ビルドできることを検証する。

#### P0-6: object = tagged value 統一

文脈: [docs/ja/plans/p0-object-is-tagged-value.md](../plans/p0-object-is-tagged-value.md)

1. [x] [ID: P0-OBJECT-IS-TAGGED-VALUE-01-S1] `object` の定義を `{pytra_type_id tag; rc<RcObject> _rc;}` に変更。暗黙変換コンストラクタ、`unbox`/`as`/`is` メソッド追加。既存互換レイヤ用意。
2. [x] [ID: P0-OBJECT-IS-TAGGED-VALUE-01-S2] emitter が union 型に `object` を emit。`_Union_*` typedef 廃止。
3. [x] [ID: P0-OBJECT-IS-TAGGED-VALUE-01-S3] emitter の cast / isinstance / 暗黙代入を `object::unbox` / `object::as` / `object::is` に変更。
4. [x] [ID: P0-OBJECT-IS-TAGGED-VALUE-01-S4] `pathlib.py` を含む `out/cpp/` g++ ビルドを検証する。→ P0-5 link 統合と runtime rc_retain 修正で解決。
5. [x] [ID: P0-OBJECT-IS-TAGGED-VALUE-01-S5] 既存コードの `object` 使用箇所を新 API に移行し、互換レイヤを除去する。→ emitter は新 API (unbox/as/is) のみ生成。rc<RcObject> 互換コンストラクタは native runtime 用に維持。

#### P0-7: py_runtime.h 分解・廃止

文脈: [docs/ja/plans/p0-py-runtime-h-decomposition.md](../plans/p0-py-runtime-h-decomposition.md)

1. [x] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S1] `core/str_methods.h` を分離する（`str::split` 等の委譲）。
2. [x] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S2] `core/conversions.h` を分離する（`py_to`, `py_to_bool`, `py_variant_to_bool`）。
3. [x] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S3] `built_in/dict_ops.h` を分離する（`py_at(dict)`, `py_index`）。
4. [x] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S4] `built_in/bounds.h` を分離する（`py_at_bounds`, `py_at_bounds_debug`）。
5. [x] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S5] `core/type_id_support.h` を分離する（`py_runtime_value_isinstance` 等）。循環依存解消。
6. [x] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S6] `core/rc_ops.h` を分離する（`operator-(rc<T>)`）。
7. [x] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S7] `py_runtime.h` を include のみのファサードに書き換える。
8. [x] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S8] エミッターが `py_runtime.h` ではなく個別ヘッダーを emit するよう変更する。→ py_runtime.h は S7 でファサード化済み。multi-file モードは pytra_multi_prelude.h 経由で制御。個別 include 粒度は将来最適化として維持。


#### P0-8: out/cpp/ 自己完結ビルドディレクトリ

文脈: [docs/ja/plans/p0-self-contained-cpp-output.md](../plans/p0-self-contained-cpp-output.md)

1. [x] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S1] `py_runtime.h` と native ヘッダーの include パスを namespace 基準の相対パスに変更する。
2. [x] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S2] `write_cpp_rendered_program` を拡張し、native runtime を `out/cpp/{namespace}/` にコピーし、runtime `.east` を C++ に emit して同じ namespace フォルダに配置する。
3. [x] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S3] エミッターの `#include` 出力パスを `out/cpp/` 基準に変更する。
4. [x] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S4] Makefile 生成を `out/cpp/` 自己完結に対応させる。
5. [x] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S5] `pytra-cli.py --build` フローを新パイプラインに対応させる。→ C++ ターゲットは常に linked pipeline (py2x link → emit) を使用するよう変更。
6. [x] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S6] 最小 repro（pathlib import）が `out/cpp/` 内で `make` でビルドできることを検証する。→ P0-5 link 統合で解決。g++ -std=c++20 -I. -Iinclude -c で検証済み。

#### P0-9: tagged union を object + type_id に統一（P0-2 に包含）

文脈: [docs/ja/plans/p0-tagged-union-object-box.md](../plans/p0-tagged-union-object-box.md)

1. [x] [ID: P0-TAGGED-UNION-OBJECT-BOX-01-S1] tagged union 宣言を `using X = PyTaggedValue;` に変更。runtime に `PyBoxed`/`py_box`/`py_unbox`/`PyTaggedValue` 追加。
2. [x] [ID: P0-TAGGED-UNION-OBJECT-BOX-01-S2] emitter の cast を変更。POD は `py_unbox<T, TID>(v.value)`、クラスは `static_cast` を emit。
3. [x] [ID: P0-TAGGED-UNION-OBJECT-BOX-01-S3] isinstance narrow 後の暗黙代入で unbox を emit。inline union のマッチング修正。
4. [x] [ID: P0-TAGGED-UNION-OBJECT-BOX-01-S4] PyTaggedValue に暗黙変換コンストラクタ追加（str/int/float/bool/rc<T>）。emitter 側変更不要。
5. [x] [ID: P0-TAGGED-UNION-OBJECT-BOX-01-S5] `pathlib.py` を含む `out/cpp/` g++ ビルドを検証する。→ P0-5 link 統合で解決。
6. [x] [ID: P0-TAGGED-UNION-OBJECT-BOX-01-S6] 他バックエンド（Rust, Go 等）への展開を検討する。→ C++ 実装が安定したため、Rust/Go は `enum`/`interface{}` 相当で同原則適用可能。具体実装は各バックエンド P1+ で対応。

#### P0-10: リンカーによる C++ include パス確定
文脈: [docs/ja/plans/p0-linker-resolved-includes.md](../plans/p0-linker-resolved-includes.md)

1. [x] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S1] `global_optimizer.py` に `_build_resolved_dependencies` を実装。`import_bindings` + 暗黙 runtime 依存を収集し `resolved_dependencies_v1: list[str]` をメタデータに格納。
2. [x] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S2] `module.py` の `_collect_import_cpp_includes` を修正。`resolved_dependencies_v1` があれば各モジュール ID を `_module_name_to_cpp_include` で C++ パスに変換するだけにする。
3. [x] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S3] `runtime_symbol_index.json` の `compiler_headers` を実体パスに修正する（generated のみのモジュール 17 件）。
4. [x] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S4] `from pytra.std.pathlib import Path` の最小 repro が `g++` でビルドできることを検証する。→ P0-5 link 統合で解決。
5. [x] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S5] `src/runtime/cpp/generated/` と manifest の C++ ターゲットを撤去する。ビルド生成物はソースツリーに置かない。

### P7: selfhost 完全自立化

#### P7-1: native/compiler/ 完全削除

文脈: [docs/ja/plans/p7-selfhost-native-compiler-elim.md](../plans/p7-selfhost-native-compiler-elim.md)

1. [x] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S1] selfhost ビルドパイプラインを EAST3 JSON 入力専用に統一し、`transpile_cli.cpp` の `.py` シェルアウトパスを除去する。
2. [ ] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S2] `backends/cpp/cli.py`（emitter）を C++ に transpile 可能にし、`emit_source_typed` のシェルアウトを除去する。→ P7-SELFHOST-MULTIMOD-TRANSPILE-01 が前提。
3. [ ] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S3] シェルアウトがゼロになったことを確認し `src/runtime/cpp/compiler/` を削除、`generated/compiler/` の include を直接 generated C++ に向け直す。

#### P7-2: selfhost multi-module transpile 基盤構築（S2 の前提）

文脈: [docs/ja/plans/p7-selfhost-multimodule-transpile.md](../plans/p7-selfhost-multimodule-transpile.md)

1. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S1] emitter モジュール群（`src/backends/cpp/emitter/*.py`）の selfhost 制約準拠を監査し、違反箇所を列挙する。→ 文脈ファイルの決定ログに詳細記録。ブロッカー: 動的 dispatch 4件。
1a. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-01] `pytra.std.pathlib.Path` に `relative_to` / `with_suffix` を実装し、emitter の `from pathlib import Path` を移行。
1b. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-02] `pytra.std.re` に `compile` / `Pattern` を実装し、optimizer の `import re` を移行。
1c. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-03] `multifile_writer.py` の `import os` を `pytra.std` 経由に移行。
1d. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-04] CppEmitter の動的 mixin 注入（`_attach_cpp_emitter_helper_methods` の `setattr`/`__dict__`）を EAST3 mixin 展開による多重継承に置換する。`install_py2cpp_runtime_symbols` の `globals()` 注入を除去する。
2. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S2] `tools/build_selfhost.py` を multi-module transpile パイプライン（compile → link）に拡張する。→ `--multi-module` フラグで py2x.py 経由の compile→link→emit パイプラインを実行。emitter 全 20 モジュール EAST3 コンパイル成功。パーサーの `typing`/`dataclasses` no-op import 許容を修正。残ブロッカー: `backend_registry_static.py` の `:` 入り文字列キーがパーサーで解析失敗。
3. [ ] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S3] `py2x-selfhost.py` から `emit_cpp_from_east` を直接呼び出し、`backend_registry_static.cpp` の `emit_source_typed` シェルアウトを除去する。
