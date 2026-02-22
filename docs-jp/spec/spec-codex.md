# Codex 向け運用仕様（Pytra）

<a href="../../docs/spec-codex.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


このドキュメントは、Codex が作業時に従う運用ルールです。

## 1. 起動時チェック

- Codex 起動時は、まず `docs-jp/spec/index.md` と `docs-jp/todo.md` を確認します。
- `docs-jp/todo.md` の未完了（`[ ]`）項目から、現在の依頼と整合するタスクを作業対象に含めます。

## 1.1 ドキュメント言語運用ルール

- `docs-jp/` を正本（source of truth）として扱い、日本語版を先に更新します。
- 通常運用では `docs/`（英語版）を先に直接編集せず、まず `docs-jp/` を更新します。
- ユーザー指示は日本語を基本とし、Codex は日本語での作業指示を前提に運用します。
- `docs/`（英語版）は必要に応じて後追い翻訳で更新してよく、同期が一時的に遅れることを許容します。
- 日本語版と英語版で記述差分がある場合は、`docs-jp/` の内容を正として判断します。
- `docs-jp/` 直下（トップレベル）への新規ファイル追加は原則禁止とし、必要時は同一ターンでの明示指示を必須とします。
- 例外として、`docs-jp/plans/`、`docs-jp/language/`、`docs-jp/todo-history/`、`docs-jp/spec/` 配下は、運用ルールに沿う範囲で Codex が自律的に新規ファイルを作成してよいものとします。

## 2. TODO 実施ルール

- `docs-jp/todo.md` は継続バックログとして扱います。
- `docs-jp/todo.md` には未完了タスクのみを置き、セクション単位で完了（全項目 `[x]`）した内容は `docs-jp/todo-history/index.md`（索引）と `docs-jp/todo-history/YYYYMMDD.md`（本文）へ移管します。
- 優先度上書きは `docs-jp/todo2.md` ではなく、チャット指示で `対象ID` / `完了条件` / `非対象` を明示して行います（テンプレート: `docs-jp/plans/instruction-template.md`）。
- 未完了項目は優先度順に順次実施します。
- タスク完了時はチェック状態を更新します。

## 3. ドキュメント同期ルール

- 仕様変更・機能追加・手順変更時は、`README.md` を必要に応じて更新します。
- `README.md` からリンクされるドキュメント（`docs-jp/how-to-use.md`, `docs-jp/spec/spec-sample-code.md`, `docs-jp/spec/index.md`, `docs-jp/plans/pytra-wip.md`, `docs-jp/spec/spec-philosophy.md`）の整合性を確認し、必要なら同時更新します。
- 実装とドキュメントの不一致を残さないことを、変更完了条件に含めます。
- `tools/` にスクリプトを追加・削除・改名した場合は、`docs-jp/spec/spec-tools.md` を同時更新します。
- 用語ルール: type annotation を指す場合は「注釈」ではなく必ず「型注釈」と記載します。
- 記述ルール: 機能やフォルダ構成を説明するときは、何をするためのものか（目的性）を必ず明記します。
- 記述ルール: 「どこに置くか」だけでなく「なぜそこに置くか」を併記し、`std` と `tra` の責務混在を防ぎます。

## 4. コミット運用

- 作業内容が論理的にまとまった時点で、ユーザーの都度許可なしにコミットしてよいものとします。
- コミット前の「commitしてよいか」の確認は不要とし、Codex が自己判断で実施します。
- コミットは論理単位で分割し、変更意図が分かるメッセージを付けます。

## 5. 実装・配置ルール

- `src/common/` には言語非依存コードのみ配置します。
- 言語固有コードは各 `py2*.py`、`src/hooks/<lang>/`、`src/profiles/<lang>/`、`src/runtime/<lang>/pytra/` に配置します。
- `src/` 直下にはトランスパイラ本体（`py2*.py`）以外を置きません。
- `CodeEmitter` など全言語で共有可能な基底ロジックは `src/common/` 側へ寄せ、`py2cpp.py` には C++ 固有ロジックのみを残します。
- 今後の多言語展開を見据え、`py2cpp.py` の肥大化を避けるため、共通化可能な処理は段階的に `src/common/` へ移管します。
- 生成コードの補助関数は各ターゲット言語ランタイム（`src/runtime/<lang>/pytra/`）へ集約し、生成コードに重複埋め込みしません。
- `src/*_module/` は互換レイヤ扱いとし、新規 runtime 実体ファイルを追加しません（段階撤去対象）。
- `src/runtime/cpp/pytra/utils/png.cpp` / `src/runtime/cpp/pytra/utils/gif.cpp` は `src/pytra/utils/*.py` からの生成物として扱い、手編集しません（`py2cpp.py` 実行時に自動更新される）。
- `json` に限らず、Python 標準ライブラリ相当機能を `runtime/cpp` 側へ追加実装してはいけません。
- Python 標準ライブラリ相当機能の正本は常に `src/pytra/std/*.py` とし、各ターゲット言語ではそのトランスパイル結果を利用します。
- selfhost 対象コード（特に `src/pytra/compiler/east.py` 系）では、動的 import（`try/except ImportError` フォールバック、`importlib` による遅延 import）を使いません。
- import は静的に解決できる形で記述し、自己変換時に未対応構文を増やさないことを優先します。
- トランスパイル対象の Python コードでは、Python 標準モジュール（`json`, `pathlib`, `sys`, `typing`, `os`, `glob`, `argparse`, `re` など）の `import` を全面禁止とします。
- トランスパイル対象コードが import できるのは `src/pytra/std/`・`src/pytra/utils/` モジュールと、ユーザー自作 `.py` モジュールです。

## 6. テスト・最適化ルール

- 変換器都合で `test/fixtures/` の入力ケースを変更してはなりません。
- 実行速度比較時の C++ は `-O3 -ffast-math -flto` を使用します。
- 生成物ディレクトリ（`out/`, `test/transpile/obj/`, `test/transpile/cpp2/`, `sample/obj/`, `sample/out/`）は Git 管理外運用を維持します。
- `out/` はローカル検証の一時出力に限定し、再生成不能な正本データは置きません。
- `src/pytra/compiler/east_parts/code_emitter.py` を変更した場合は `test/unit/test_code_emitter.py` を必ず実行し、共通ユーティリティ回帰を先に確認します。
- `CodeEmitter` / `py2cpp` 系の変更では、最低限 `python3 tools/check_py2cpp_transpile.py` と `python3 tools/build_selfhost.py` の両方を通過させてからコミットします。
- 上記 2 コマンドのいずれかが失敗した状態でのコミットは禁止します。
- 変換器関連ファイル（`src/py2*.py`, `src/pytra/**`, `src/hooks/**`, `src/profiles/**`）を変更する場合は、`src/pytra/compiler/transpiler_versions.json` の対応バージョンを minor 以上で更新し、`python3 tools/check_transpiler_version_gate.py` を通過させます。
- sample 再生成は `python3 tools/run_regen_on_version_bump.py --verify-cpp-on-diff` を使用し、バージョン更新で差分が出た C++ ケースを compile/run 検証します。

## 7. selfhost 運用ノウハウ

- `python3 tools/prepare_selfhost_source.py` を先に実行し、`CodeEmitter` を `selfhost/py2cpp.py` へインライン展開した自己完結ソースを作ってから selfhost 変換を行う。
- selfhost 検証前に、`selfhost/py2cpp.py` と `selfhost/runtime/cpp/*` は `src` の最新へ同期してよい（必要時は同期を優先）。
- `#include "runtime/cpp/..."` は `selfhost/` 配下の同名ヘッダが優先解決される。`src/runtime/cpp` だけ更新しても selfhost ビルドは直らないことがある。
- selfhost のビルドログは `stdout` 側に出ることがあるため、`> selfhost/build.all.log 2>&1` で統合取得する。
- selfhost 対象コードでは、Python 専用表現が生成 C++ に漏れないことを確認する（例: `super().__init__`, Python 風継承表記）。
- ランタイム変更時は `test/unit/test_py2cpp_features.py` の実行回帰に加え、selfhost の再生成・再コンパイル結果も確認する。
- selfhost 対象の Python コードでも、標準モジュールの直接 import は禁止し、`src/pytra/std/` の shim のみを使う（例: `pytra.std.json`, `pytra.std.pathlib`, `pytra.std.sys`, `pytra.std.typing`, `pytra.std.os`, `pytra.std.glob`, `pytra.std.argparse`, `pytra.std.re`）。
- selfhost 向けに確実性を優先する箇所では、`continue` に依存した分岐や `x in {"a", "b"}` のようなリテラル集合 membership を避け、`if/elif` と明示比較（`x == "a" or x == "b"`）を優先する。
- 日次の最小回帰は `python3 tools/run_local_ci.py` を実行し、`check_py2cpp_transpile` + unit tests + selfhost build + selfhost diff をまとめて通す。

## 8. 対外リリース版バージョン運用

- 対外リリース版の正本はリポジトリ直下 `VERSION` とし、形式は `MAJOR.MINOR.PATCH`（SemVer）を使います。
- 現在の対外リリース版は `0.0.1` です。
- `PATCH` の更新は Codex が実施してよいものとします。
- `MAJOR` / `MINOR` の更新は、ユーザーの明示指示がある場合のみ実施します。
- `src/pytra/compiler/transpiler_versions.json` は再生成トリガー用の内部バージョンであり、対外リリース版（`VERSION`）とは別管理です。
