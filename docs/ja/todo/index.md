# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-21（P0-1〜P0-10, P1 パイプライン段分離, P4 vararg 脱糖 をアーカイブへ移動）

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

### P1: パイプライン段分離 — compile / link / emit の独立化

#### P1-2: backend_registry 依存の除去

文脈: [docs/ja/plans/p1-backend-registry-decoupling.md](../plans/p1-backend-registry-decoupling.md)

1. [x] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S1] `py2x.py` の C++ emit パスを `east2cpp.py` サブプロセスに変更し、`backend_registry` import を除去。→ py2x.py の import グラフに toolchain.emit.* が一切含まれない。
2. [x] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S2] `py2x.py` の非 C++ emit パスを `east2x.py` サブプロセスに変更。→ S1 と同時に完了。
3. [x] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S3] `py2x-selfhost.py` から `backend_registry_static` import を除去。→ C++ emitter のみ直接 import。非 C++ backend は import グラフに含まれない。
4. [x] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S4] selfhost compile+link で 65 モジュール（以前 151）。非 C++ backend 74 件が完全に消えた（57% 削減）。

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
2. [ ] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S2] `toolchain/emit/cpp/cli.py`（emitter）を C++ に transpile 可能にし、`emit_source_typed` のシェルアウトを除去する。→ P7-SELFHOST-MULTIMOD-TRANSPILE-01 が前提。
3. [ ] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S3] シェルアウトがゼロになったことを確認し `src/runtime/cpp/compiler/` を削除、`generated/compiler/` の include を直接 generated C++ に向け直す。

#### P7-2: selfhost multi-module transpile 基盤構築（S2 の前提）

文脈: [docs/ja/plans/p7-selfhost-multimodule-transpile.md](../plans/p7-selfhost-multimodule-transpile.md)

1. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S1] emitter モジュール群（`src/toolchain/emit/cpp/emitter/*.py`）の selfhost 制約準拠を監査し、違反箇所を列挙する。→ 文脈ファイルの決定ログに詳細記録。ブロッカー: 動的 dispatch 4件。
1a. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-01] `pytra.std.pathlib.Path` に `relative_to` / `with_suffix` を実装し、emitter の `from pathlib import Path` を移行。
1b. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-02] `pytra.std.re` に `compile` / `Pattern` を実装し、optimizer の `import re` を移行。
1c. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-03] `multifile_writer.py` の `import os` を `pytra.std` 経由に移行。
1d. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-04] CppEmitter の動的 mixin 注入（`_attach_cpp_emitter_helper_methods` の `setattr`/`__dict__`）を EAST3 mixin 展開による多重継承に置換する。`install_py2cpp_runtime_symbols` の `globals()` 注入を除去する。
2. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S2] `tools/build_selfhost.py` を multi-module transpile パイプライン（compile → link）に拡張する。→ `--multi-module` フラグで py2x.py 経由の compile→link→emit パイプラインを実行。全 150 モジュール EAST3 コンパイル成功。パーサー修正（typing no-op、dict 文字列キー内 `:`、複数型引数 subscript）。依存チェーン全体の object レシーバ修正（40+ ファイル）。
3. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S3] selfhost 66 モジュールの C++ emit 完了。→ compile+link (py2x.py --link-only) → emit (toolchain/emit/cpp.py) の 3 段パイプラインで 233 C++ ファイル (4.1MB) を生成。backend_registry 依存除去により 151→66 モジュールに削減。
4. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S4] リンカーの import 解決で `from toolchain.misc.transpile_cli import make_user_error` 等のシンボルが見つからない問題を調査・修正する。→ `module_export_table` に wildcard re-export 伝播を実装。`from X import *` による再エクスポートが export テーブルに反映されるようになり、151 モジュールの link に成功。wildcard バインディングの重複許容も追加。
