# Codex 向け運用仕様（Pytra）

このドキュメントは、Codex が作業時に従う運用ルールです。

## 1. 起動時チェック

- Codex 起動時は、まず `docs/spec.md` と `docs/todo.md` を確認します。
- `docs/todo.md` の未完了（`[ ]`）項目から、現在の依頼と整合するタスクを作業対象に含めます。

## 2. TODO 実施ルール

- `docs/todo.md` は継続バックログとして扱います。
- `docs/todo.md` には未完了タスクのみを置き、セクション単位で完了（全項目 `[x]`）した内容は `docs/todo-old.md` へ移管します。
- 未完了項目は優先度順に順次実施します。
- タスク完了時はチェック状態を更新します。

## 3. ドキュメント同期ルール

- 仕様変更・機能追加・手順変更時は、`README.md` を必要に応じて更新します。
- `README.md` からリンクされるドキュメント（`docs/how-to-use.md`, `docs/sample-code.md`, `docs/spec.md`, `docs/pytra-readme.md`）の整合性を確認し、必要なら同時更新します。
- 実装とドキュメントの不一致を残さないことを、変更完了条件に含めます。
- `tools/` にスクリプトを追加・削除・改名した場合は、`docs/tools.md` を同時更新します。
- 用語ルール: type annotation を指す場合は「注釈」ではなく必ず「型注釈」と記載します。
- 記述ルール: 機能やフォルダ構成を説明するときは、何をするためのものか（目的性）を必ず明記します。
- 記述ルール: 「どこに置くか」だけでなく「なぜそこに置くか」を併記し、`std` と `tra` の責務混在を防ぎます。

## 4. コミット運用

- 作業内容が論理的にまとまった時点で、ユーザーの都度許可なしにコミットしてよいものとします。
- コミット前の「commitしてよいか」の確認は不要とし、Codex が自己判断で実施します。
- コミットは論理単位で分割し、変更意図が分かるメッセージを付けます。

## 5. 実装・配置ルール

- `src/common/` には言語非依存コードのみ配置します。
- 言語固有コードは各 `py2*.py` または各 `*_module/` に配置します。
- `src/` 直下にはトランスパイラ本体（`py2*.py`）以外を置きません。
- `CodeEmitter` など全言語で共有可能な基底ロジックは `src/common/` 側へ寄せ、`py2cpp.py` には C++ 固有ロジックのみを残します。
- 今後の多言語展開を見据え、`py2cpp.py` の肥大化を避けるため、共通化可能な処理は段階的に `src/common/` へ移管します。
- 生成コードの補助関数は各ターゲット言語ランタイム（`src/*_module/`）へ集約し、生成コードに重複埋め込みしません。
- `src/runtime/cpp/pytra/runtime/png.cpp` / `src/runtime/cpp/pytra/runtime/gif.cpp` は `src/pytra/runtime/*.py` からの生成物として扱い、手編集しません（更新は `python3 tools/generate_cpp_pylib_runtime.py` を使用）。
- `json` に限らず、Python 標準ライブラリ相当機能を `runtime/cpp` 側へ追加実装してはいけません。
- Python 標準ライブラリ相当機能の正本は常に `src/pylib/*.py` とし、各ターゲット言語ではそのトランスパイル結果を利用します。
- selfhost 対象コード（特に `src/pylib/east.py` 系）では、動的 import（`try/except ImportError` フォールバック、`importlib` による遅延 import）を使いません。
- import は静的に解決できる形で記述し、自己変換時に未対応構文を増やさないことを優先します。
- トランスパイル対象の Python コードでは、Python 標準モジュール（`json`, `pathlib`, `sys`, `typing`, `os`, `glob`, `argparse`, `re` など）の `import` を全面禁止とします。
- トランスパイル対象コードが import できるのは `src/pylib/` モジュールと、ユーザー自作 `.py` モジュールです。

## 6. テスト・最適化ルール

- 変換器都合で `test/fixtures/` の入力ケースを変更してはなりません。
- 実行速度比較時の C++ は `-O3 -ffast-math -flto` を使用します。
- 生成物ディレクトリ（`test/transpile/obj/`, `test/transpile/cpp2/`, `sample/obj/`, `sample/out/`）は Git 管理外運用を維持します。
- `src/pylib/east_parts/code_emitter.py` を変更した場合は `test/unit/test_code_emitter.py` を必ず実行し、共通ユーティリティ回帰を先に確認します。
- `CodeEmitter` / `py2cpp` 系の変更では、最低限 `python3 tools/check_py2cpp_transpile.py` と `python3 tools/build_selfhost.py` の両方を通過させてからコミットします。
- 上記 2 コマンドのいずれかが失敗した状態でのコミットは禁止します。

## 7. selfhost 運用ノウハウ

- `python3 tools/prepare_selfhost_source.py` を先に実行し、`CodeEmitter` を `selfhost/py2cpp.py` へインライン展開した自己完結ソースを作ってから selfhost 変換を行う。
- selfhost 検証前に、`selfhost/py2cpp.py` と `selfhost/runtime/cpp/*` は `src` の最新へ同期してよい（必要時は同期を優先）。
- `#include "runtime/cpp/..."` は `selfhost/` 配下の同名ヘッダが優先解決される。`src/runtime/cpp` だけ更新しても selfhost ビルドは直らないことがある。
- selfhost のビルドログは `stdout` 側に出ることがあるため、`> selfhost/build.all.log 2>&1` で統合取得する。
- selfhost 対象コードでは、Python 専用表現が生成 C++ に漏れないことを確認する（例: `super().__init__`, Python 風継承表記）。
- ランタイム変更時は `test/unit/test_py2cpp_features.py` の実行回帰に加え、selfhost の再生成・再コンパイル結果も確認する。
- selfhost 対象の Python コードでも、標準モジュールの直接 import は禁止し、`src/pylib/` の shim のみを使う（例: `pytra.std.json`, `pytra.std.pathlib`, `pytra.std.sys`, `pytra.std.typing`, `pytra.std.os`, `pytra.std.glob`, `pytra.std.argparse`, `pytra.std.re`）。
- selfhost 向けに確実性を優先する箇所では、`continue` に依存した分岐や `x in {"a", "b"}` のようなリテラル集合 membership を避け、`if/elif` と明示比較（`x == "a" or x == "b"`）を優先する。
- 日次の最小回帰は `python3 tools/run_local_ci.py` を実行し、`check_py2cpp_transpile` + unit tests + selfhost build + selfhost diff をまとめて通す。
