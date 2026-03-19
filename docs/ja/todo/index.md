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

#### P0-2: out/cpp/ 自己完結ビルドディレクトリ（優先）

文脈: [docs/ja/plans/p0-self-contained-cpp-output.md](../plans/p0-self-contained-cpp-output.md)

1. [x] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S1] `py_runtime.h` と native ヘッダーの include パスを namespace 基準の相対パスに変更する（`"py_types.h"` → `"core/py_types.h"` 等）。
2. [x] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S2] `write_cpp_rendered_program` を拡張し、native runtime を `out/cpp/{namespace}/` にコピーし、runtime `.east` を C++ に emit して同じ namespace フォルダに配置する。
3. [x] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S3] エミッターの `#include` 出力パスを `out/cpp/` 基準に変更する。
4. [ ] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S4] Makefile 生成を `out/cpp/` 自己完結に対応させる。
5. [ ] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S5] `pytra-cli.py --build` フローを新パイプラインに対応させる。
6. [ ] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S6] 最小 repro（pathlib import）が `out/cpp/` 内で `make` でビルドできることを検証する。
7. [ ] [ID: P0-SELF-CONTAINED-CPP-OUTPUT-01-S7] `py_runtime.h` ↔ `type_id.h` の循環依存を解消する。→ P0-PY-RUNTIME-H-DECOMPOSITION-01 で解決。

#### P0-4: py_runtime.h 分解・廃止（S7 の前提、優先）

文脈: [docs/ja/plans/p0-py-runtime-h-decomposition.md](../plans/p0-py-runtime-h-decomposition.md)

1. [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S1] `core/str_methods.h` を分離する（`str::split` 等の委譲）。
2. [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S2] `core/conversions.h` を分離する（`py_to`, `py_to_bool`, `py_variant_to_bool`）。
3. [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S3] `built_in/dict_ops.h` を分離する（`py_at(dict)`, `py_index`）。
4. [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S4] `built_in/bounds.h` を分離する（`py_at_bounds`, `py_at_bounds_debug`）。
5. [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S5] `core/type_id_support.h` を分離する（`py_runtime_value_isinstance` 等）。循環依存解消。
6. [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S6] `core/rc_ops.h` を分離する（`operator-(rc<T>)`）。
7. [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S7] `py_runtime.h` を include のみのファサードに書き換える。
8. [ ] [ID: P0-PY-RUNTIME-H-DECOMPOSITION-01-S8] エミッターが `py_runtime.h` ではなく個別ヘッダーを emit するよう変更する。

#### P0-3: リンカーによる C++ include パス確定

文脈: [docs/ja/plans/p0-linker-resolved-includes.md](../plans/p0-linker-resolved-includes.md)

1. [x] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S1] `global_optimizer.py` に `_build_resolved_dependencies` を実装。`import_bindings` + 暗黙 runtime 依存を収集し `resolved_dependencies_v1: list[str]` をメタデータに格納。
2. [x] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S2] `module.py` の `_collect_import_cpp_includes` を修正。`resolved_dependencies_v1` があれば各モジュール ID を `_module_name_to_cpp_include` で C++ パスに変換するだけにする。
3. [x] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S3] `runtime_symbol_index.json` の `compiler_headers` を実体パスに修正する（generated のみのモジュール 17 件）。
4. [ ] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S4] `from pytra.std.pathlib import Path` の最小 repro が `g++` でビルドできることを検証する。→ P0-SELF-CONTAINED-CPP-OUTPUT-01-S6 で解決。
5. [x] [ID: P0-LINKER-RESOLVED-INCLUDES-01-S5] `src/runtime/cpp/generated/` と manifest の C++ ターゲットを撤去する。ビルド生成物はソースツリーに置かない。

### P7: selfhost 完全自立化

#### P7-1: native/compiler/ 完全削除

文脈: [docs/ja/plans/p7-selfhost-native-compiler-elim.md](../plans/p7-selfhost-native-compiler-elim.md)

1. [x] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S1] selfhost ビルドパイプラインを EAST3 JSON 入力専用に統一し、`transpile_cli.cpp` の `.py` シェルアウトパスを除去する。
2. [ ] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S2] `backends/cpp/cli.py`（emitter）を C++ に transpile 可能にし、`emit_source_typed` のシェルアウトを除去する。→ P7-SELFHOST-MULTIMOD-TRANSPILE-01 が前提。
3. [ ] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S3] シェルアウトがゼロになったことを確認し `src/runtime/cpp/compiler/` を削除、`generated/compiler/` の include を直接 generated C++ に向け直す。

#### P7-2: selfhost multi-module transpile 基盤構築（S2 の前提）

文脈: [docs/ja/plans/p7-selfhost-multimodule-transpile.md](../plans/p7-selfhost-multimodule-transpile.md)

1. [ ] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S1] emitter モジュール群（`src/backends/cpp/emitter/*.py`）の selfhost 制約準拠を監査し、違反箇所を列挙する。
2. [ ] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S2] `tools/build_selfhost.py` を multi-module transpile パイプライン（compile → link）に拡張する。
3. [ ] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S3] `py2x-selfhost.py` から `emit_cpp_from_east` を直接呼び出し、`backend_registry_static.cpp` の `emit_source_typed` シェルアウトを除去する。
