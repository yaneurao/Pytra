# Codex 向け運用仕様（Pytra）

このドキュメントは、Codex が作業時に従う運用ルールです。

## 1. 起動時チェック

- Codex 起動時は、まず `docs/spec.md` と `docs/todo.md` を確認します。
- `docs/todo.md` の未完了（`[ ]`）項目から、現在の依頼と整合するタスクを作業対象に含めます。

## 2. TODO 実施ルール

- `docs/todo.md` は継続バックログとして扱います。
- 未完了項目は優先度順に順次実施します。
- タスク完了時はチェック状態を更新します。

## 3. ドキュメント同期ルール

- 仕様変更・機能追加・手順変更時は、`README.md` を必要に応じて更新します。
- `README.md` からリンクされるドキュメント（`docs/how-to-use.md`, `docs/sample-code.md`, `docs/spec.md`, `docs/pytra-readme.md`）の整合性を確認し、必要なら同時更新します。
- 実装とドキュメントの不一致を残さないことを、変更完了条件に含めます。
- 用語ルール: type annotation を指す場合は「注釈」ではなく必ず「型注釈」と記載します。

## 4. コミット運用

- 作業内容が論理的にまとまった時点で、ユーザーの都度許可なしにコミットしてよいものとします。
- コミット前の「commitしてよいか」の確認は不要とし、Codex が自己判断で実施します。
- コミットは論理単位で分割し、変更意図が分かるメッセージを付けます。

## 5. 実装・配置ルール

- `src/common/` には言語非依存コードのみ配置します。
- 言語固有コードは各 `py2*.py` または各 `*_module/` に配置します。
- `src/` 直下にはトランスパイラ本体（`py2*.py`）以外を置きません。
- `BaseEmitter` など全言語で共有可能な基底ロジックは `src/common/` 側へ寄せ、`py2cpp.py` には C++ 固有ロジックのみを残します。
- 今後の多言語展開を見据え、`py2cpp.py` の肥大化を避けるため、共通化可能な処理は段階的に `src/common/` へ移管します。
- 生成コードの補助関数は各ターゲット言語ランタイム（`src/*_module/`）へ集約し、生成コードに重複埋め込みしません。
- selfhost 対象コード（特に `src/common/east.py` 系）では、動的 import（`try/except ImportError` フォールバック、`importlib` による遅延 import）を使いません。
- import は静的に解決できる形で記述し、自己変換時に未対応構文を増やさないことを優先します。

## 6. テスト・最適化ルール

- 変換器都合で `test/fixtures/` の入力ケースを変更してはなりません。
- 実行速度比較時の C++ は `-O3 -ffast-math -flto` を使用します。
- 生成物ディレクトリ（`test/transpile/obj/`, `test/transpile/cpp2/`, `sample/obj/`, `sample/out/`）は Git 管理外運用を維持します。
- `src/common/base_emitter.py` を変更した場合は `test/unit/test_base_emitter.py` を必ず実行し、共通ユーティリティ回帰を先に確認します。

## 7. selfhost 運用ノウハウ

- selfhost 検証前に、`selfhost/py2cpp.py` と `selfhost/cpp_module/*` は `src` の最新へ同期してよい（必要時は同期を優先）。
- `#include "cpp_module/..."` は `selfhost/` 配下の同名ヘッダが優先解決される。`src/cpp_module` だけ更新しても selfhost ビルドは直らないことがある。
- selfhost のビルドログは `stdout` 側に出ることがあるため、`> selfhost/build.all.log 2>&1` で統合取得する。
- selfhost 対象コードでは、Python 専用表現が生成 C++ に漏れないことを確認する（例: `super().__init__`, Python 風継承表記）。
- ランタイム変更時は `test/unit/test_py2cpp_features.py` の実行回帰に加え、selfhost の再生成・再コンパイル結果も確認する。
