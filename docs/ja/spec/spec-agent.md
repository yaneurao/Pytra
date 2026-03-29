<a href="../../en/spec/spec-agent.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# エージェント運用仕様（Pytra）

このドキュメントは、Codex および Claude Code（以下「エージェント」）が作業時に従う運用ルールです。

## 1. 起動時チェック

- エージェント起動時は、まず `docs/ja/spec/index.md` と `docs/ja/todo/index.md` を確認します。
- `docs/ja/todo/index.md` の未完了（`[ ]`）項目から、現在の依頼と整合するタスクを作業対象に含めます。

## 1.1 ドキュメント言語運用ルール

- `docs/ja/` を正本（source of truth）として扱い、日本語版を先に更新します。
- 通常運用では `docs/en/`（英語版）を先に直接編集せず、まず `docs/ja/` を更新します。
- ユーザー指示は日本語を基本とし、エージェントは日本語での作業指示を前提に運用します。
- `docs/en/`（英語版）は必要に応じて後追い翻訳で更新してよく、同期が一時的に遅れることを許容します。
- 日本語版と英語版で記述差分がある場合は、`docs/ja/` の内容を正として判断します。
- `docs/ja/` 直下（トップレベル）への新規ファイル追加は原則禁止とし、必要時は同一ターンでの明示指示を必須とします。
- 例外として `docs/ja/AGENTS.md` は運用ブートストラップ入口として常設を許可します。
- ルート `AGENTS.md` はローカル専用ポインタ（`.gitignore` 対象）とし、Git 管理しません。
- 例外として、`docs/ja/plans/`、`docs/ja/language/`、`docs/ja/todo/archive/`、`docs/ja/spec/` 配下は、運用ルールに沿う範囲でエージェントが自律的に新規ファイルを作成してよいものとします。

## 2. TODO 実施ルール

- `docs/ja/todo/index.md` は継続バックログとして扱います。
- `docs/ja/todo/index.md` には未完了タスクのみを置き、セクション単位で完了（全項目 `[x]`）した内容は `docs/ja/todo/archive/index.md`（索引）と `docs/ja/todo/archive/YYYYMMDD.md`（本文）へ移管します。
- 優先度上書きは `docs/ja/todo2.md` ではなく、チャット指示で `対象ID` / `完了条件` / `非対象` を明示して行います（テンプレート: `docs/ja/plans/instruction-template.md`）。
- 各領域の agent は自分の領域ファイル（`docs/ja/todo/{cpp,go,rust,ts,infra}.md`）内で優先度順に着手します。
- `docs/ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細な判断・検証ログは文脈ファイル（`docs/ja/plans/*.md`）の `決定ログ` へ追記します。
- 大きいタスクは文脈ファイルで `-S1` / `-S2` 形式の子タスクへ分割してよく、`tools/check_todo_priority.py` は最上位未完了 `ID` とその子 `ID` を許可します。
- `docs/ja/todo/index.md` または `docs/ja/plans/*.md` に進捗ログを追加したターンでは、`python3 tools/check_todo_priority.py` を通過させます（`plans` 側は `決定ログ` の日付行のみが進捗判定対象）。
- 割り込み等で未コミット差分が残る場合は、同一 `ID` を完了させるか差分を戻してから別 `ID` へ移ります。
- タスク完了時はチェック状態を更新します。

## 3. ドキュメント同期ルール

- 仕様変更・機能追加・手順変更時は、`README.md` を必要に応じて更新します。
- `README.md` からリンクされるドキュメント（`docs/ja/tutorial/README.md`, `sample/README-ja.md`, `docs/ja/spec/index.md`, `docs/ja/plans/pytra-wip.md`, `docs/ja/spec/spec-philosophy.md`）の整合性を確認し、必要なら同時更新します。
- 実装とドキュメントの不一致を残さないことを、変更完了条件に含めます。
- `tools/` にスクリプトを追加・削除・改名した場合は、`docs/ja/spec/spec-tools.md` を同時更新します。
- `docs/ja/README.md` の「更新履歴」は最新 3 件までを保持し、全履歴は `docs/ja/changelog.md` に記録します。
- 用語ルール: type annotation を指す場合は「注釈」ではなく必ず「型注釈」と記載します。
- 記述ルール: 機能やフォルダ構成を説明するときは、何をするためのものか（目的性）を必ず明記します。
- 記述ルール: 「どこに置くか」だけでなく「なぜそこに置くか」を併記し、`std` と `tra` の責務混在を防ぎます。
- `docs/ja/spec/` 直下は現行仕様のみを保持し、退役した仕様は `docs/ja/spec/archive/YYYYMMDD-<slug>.md` へ移動します。
- `docs/ja/spec/archive/index.md` は旧仕様の索引として維持し、アーカイブ追加ごとにリンクを追記します。

## 4. コミット運用

- 作業内容が論理的にまとまった時点で、ユーザーの都度許可なしにコミットしてよいものとします。
- コミット前の「commitしてよいか」の確認は不要とし、エージェントが自己判断で実施します。
- コミットは論理単位で分割し、変更意図が分かるメッセージを付けます。
- TODO 消化コミットはメッセージに `ID` を含めます（例: ``[ID: P0-XXX-01] ...``）。

## 4.1 禁止 git 操作（複数インスタンス環境）

複数のエージェントインスタンス（Codex / Claude Code）が同一ワーキングツリーで同時に動作するため、他インスタンスの未コミット変更を破壊する以下の git 操作を**禁止**する。

- `git stash` — 全未コミット変更を退避し、他インスタンスの作業を巻き戻す
- `git checkout -- <file>` — ファイルの未コミット変更を破棄する
- `git restore <file>` — 同上（`checkout --` の新構文）
- `git reset --hard` — 全変更を破棄する
- `git clean -f` — 未追跡ファイルを削除する

代替手段:
- 変更を取り消したい場合は、手動で Edit/Write で元に戻すか、`git diff <file>` で差分を確認してから対処する。
- 一時退避が必要な場合は、ファイルを `/tmp/` にコピーして手動で復元する。

## 5. 実装・配置ルール

- `src/toolchain/emit/common/` には言語非依存コードのみ配置します。
- 言語固有コードは各 `py2*.py`、`src/toolchain/emit/<lang>/`、`src/toolchain/emit/<lang>/profiles/`、`src/runtime/<lang>/{generated,native}/` に配置します。未移行 backend の `pytra-gen/pytra-core` は一時 debt としてのみ扱います。
- `src/` 直下にはトランスパイラ本体（`py2*.py`）以外を置きません。
- `CodeEmitter` など全言語で共有可能な基底ロジックは `src/toolchain/emit/common/` 側へ寄せ、`py2cpp.py` には C++ 固有ロジックのみを残します。
- 今後の多言語展開を見据え、`py2cpp.py` の肥大化を避けるため、共通化可能な処理は段階的に `src/toolchain/emit/common/` へ移管します。
- 生成コードの補助関数は各ターゲット言語の canonical runtime lane（移行済み backend は `src/runtime/<lang>/{generated,native}/`）へ集約し、生成コードに重複埋め込みしません。
- `src/*_module/` は互換レイヤ扱いとし、新規 runtime 実体ファイルを追加しません（段階撤去対象）。
- `src/runtime/cpp/generated/utils/png.cpp` / `src/runtime/cpp/generated/utils/gif.cpp` は `src/pytra/utils/*.py` からの生成物として扱い、手編集しません（`py2cpp.py` 実行時に自動更新される）。
- `src/runtime/<lang>/generated/` の `png/gif` 書き出し本体は、`src/pytra/utils/png.py` / `src/pytra/utils/gif.py` を正本とした生成物のみを許可し、言語別の手書き実装を禁止します。
- `png/gif` で許可される言語差分は、入出力アダプタや最小のランタイム接続コードに限定し、エンコード本体ロジック（CRC32/Adler32/DEFLATE/LZW/chunk構築）を手で複製してはいけません。
- 画像runtimeは C++ と同じ責務分離を全言語で強制します。canonical 形は `src/runtime/<lang>/native/` に手書き runtime、`src/runtime/<lang>/generated/` に `src/pytra/utils/{png,gif}.py` 由来の生成物のみを置く形です。未移行 backend の `pytra-core/pytra-gen` は rollout debt としてのみ許可します。
- `py_runtime.*` など core 側ファイルへ PNG/GIF エンコード本体（`write_rgb_png` / `save_gif` / `grayscale_palette`）を直書きしてはいけません。必要な場合は canonical generated lane API への薄い委譲だけを許可します。
- generated 側の画像runtime生成物には、生成元と生成導線が追跡できる印（例: `source: src/pytra/utils/png.py`, `source: src/pytra/utils/gif.py`, `generated-by: ...`）を必須とします。
- `json` に限らず、Python 標準ライブラリ相当機能を `runtime/cpp` 側へ追加実装してはいけません。
- Python 標準ライブラリ相当機能の正本は常に `src/pytra/std/*.py` とし、各ターゲット言語ではそのトランスパイル結果を利用します。
- selfhost 対象コード（特に `src/toolchain/misc/east.py` 系）では、動的 import（`try/except ImportError` フォールバック、`importlib` による遅延 import）を使いません。
- import は静的に解決できる形で記述し、自己変換時に未対応構文を増やさないことを優先します。
- selfhost 対象コード（`src/` 配下のトランスパイラ本体・backend・IR 実装）では、Python 標準 `ast` モジュール（`import ast` / `from ast ...`）への依存を禁止します。
- `ast` ベース解析が必要な場合は、EAST ノード走査または既存の selfhost 対応 parser/IR 情報で代替します。
- 例外: `tools/` と `test/` の検査・テストコードは selfhost 非対象のため `ast` 利用を許可します。
- トランスパイル対象の Python コードでは、Python 標準モジュール（`json`, `pathlib`, `sys`, `os`, `glob`, `argparse`, `re` など）の `import` を禁止します。
- 例外として `typing`（`import typing`, `from typing import ...`）は注釈専用 no-op import として許可します。
- 例外として `dataclasses`（`import dataclasses`, `from dataclasses import ...`）は decorator 解決専用 no-op import として許可します。
- トランスパイル対象コードが import できるのは `src/pytra/std/`・`src/pytra/utils/` モジュールと、ユーザー自作 `.py` モジュールです。

## 6. テスト・最適化ルール

- 変換器都合で `test/fixtures/` の入力ケースを変更してはなりません。
- 変換器の互換性検証に使う原本（`materials/` 配下、特に `materials/refs/microgpt/*.py`）を変換都合で改変してはなりません。
- 変換回避の検証用派生ファイルが必要な場合は `work/tmp/*-lite.py` を作成して分離し、原本を評価基準（最終的に通す対象）として維持します。
- 実行速度比較時の C++ は `-O3 -ffast-math -flto` を使用します。
- 生成物ディレクトリ（`out/`, `work/transpile/obj/`, `work/transpile/cpp2/`, `sample/obj/`, `sample/out/`）は Git 管理外運用を維持します。
- **以下への一時出力は禁止**: `out/`, `selfhost/`, `sample/obj/`, `/tmp/`。
  - ビルド・変換・検証の一時出力は `work/tmp/` を使用する。
  - selfhost テストの出力は `work/selfhost/` を使用する。
  - `out/` / `selfhost/` / `sample/obj/` は過去の互換ディレクトリであり、新規の出力先として使ってはならない。複数インスタンスの競合リスクがある。
  - `sample/out/` は sample/py の出力見本（PNG/GIF/TXT）専用。それ以外の用途（変換結果、一時ファイル等）での出力は禁止。
  - `/tmp/` はシステム共有領域であり、掃除されずゴミが蓄積する。使用禁止。
  - `tempfile.TemporaryDirectory()` も `/tmp/` を使うため禁止。代わりに `work/tmp/` 配下にサブディレクトリを作成する。
- `src/toolchain/emit/common/emitter/code_emitter.py` を変更した場合は `test/unit/common/test_code_emitter.py` を必ず実行し、共通ユーティリティ回帰を先に確認します。
- `CodeEmitter` / `py2cpp` 系の変更では、最低限 `python3 tools/check_py2cpp_transpile.py` と `python3 tools/build_selfhost.py` の両方を通過させてからコミットします。
- 上記 2 コマンドのいずれかが失敗した状態でのコミットは禁止します。
- 変換器関連ファイル（`src/py2*.py`, `src/pytra/**`, `src/toolchain/emit/**`, `src/toolchain/emit/**/profiles/**`）を変更する場合は、`src/toolchain/misc/transpiler_versions.json` の対応バージョンを minor 以上で更新し、`python3 tools/check_transpiler_version_gate.py` を通過させます。
- sample 再生成は `python3 tools/run_regen_on_version_bump.py --verify-cpp-on-diff` を使用し、バージョン更新で差分が出た C++ ケースを compile/run 検証します。
- アドホックな C++ コンパイル実験（デバッグ・調査目的）を行う場合は、ソースと成果物をリポジトリ直下ではなく `/tmp/` または `work/tmp/` 以下に置いて実行します（`tempfile.TemporaryDirectory()` パターンを参照）。
- GCC ダンプフラグ（`-fdump-tree-all` 等）はカレントディレクトリに出力するため、リポジトリ直下では使用しません。使う場合は `-dumpdir /tmp/` を明示します。
- コンパイルを伴う実験の後は `git status --short` でリポジトリ直下に意図しない生成物が残っていないことを確認します。

## 7. selfhost 運用ノウハウ

- `python3 tools/prepare_selfhost_source.py` を先に実行し、`CodeEmitter` を `work/selfhost/py2cpp.py` へインライン展開した自己完結ソースを作ってから selfhost 変換を行う。
- selfhost 検証前に、`work/selfhost/py2cpp.py` と `work/selfhost/runtime/cpp/*` は `src` の最新へ同期してよい（必要時は同期を優先）。
- `#include "runtime/cpp/..."` は `work/selfhost/` 配下の同名ヘッダが優先解決される。`src/runtime/cpp` だけ更新しても selfhost ビルドは直らないことがある。
- selfhost のビルドログは `stdout` 側に出ることがあるため、`> work/selfhost/build.all.log 2>&1` で統合取得する。
- selfhost 対象コードでは、Python 専用表現が生成 C++ に漏れないことを確認する（例: `super().__init__`, Python 風継承表記）。
- ランタイム変更時は `test/unit/toolchain/emit/cpp/test_py2cpp_features.py` の実行回帰に加え、selfhost の再生成・再コンパイル結果も確認する。
- selfhost 対象の Python コードでも、標準モジュールの直接 import は禁止し、`src/pytra/std/` の shim のみを使う（例: `pytra.std.json`, `pytra.std.pathlib`, `pytra.std.sys`, `pytra.std.os`, `pytra.std.glob`, `pytra.std.argparse`, `pytra.std.re`）。`typing` だけは注釈専用 no-op import として直接 import を許可する。
- selfhost 向けに確実性を優先する箇所では、`continue` に依存した分岐や `x in {"a", "b"}` のようなリテラル集合 membership を避け、`if/elif` と明示比較（`x == "a" or x == "b"`）を優先する。
- 日次の最小回帰は `python3 tools/run_local_ci.py` を実行し、`check_py2cpp_transpile` + unit tests + selfhost build + selfhost diff をまとめて通す。

## 8. 対外リリース版バージョン運用

- 対外リリース版の正本は `docs/VERSION` とし、形式は `MAJOR.MINOR.PATCH`（SemVer）を使います。
- 現在の対外リリース版は `0.7.0` です。
- `PATCH` の更新はエージェントが実施してよいものとします。
- `MAJOR` / `MINOR` の更新は、ユーザーの明示指示がある場合のみ実施します。
- `src/toolchain/misc/transpiler_versions.json` は再生成トリガー用の内部バージョンであり、対外リリース版（`docs/VERSION`）とは別管理です。
