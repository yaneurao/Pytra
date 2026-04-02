<a href="../../en/spec/spec-agent-coder.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# AI agent 運用仕様 — コード担当向け

このドキュメントは、コードの実装・修正・テストを担当する AI agent 向けのルールです。

## 1. golden / テスト生成

- **golden ファイル（east1/east2/east3/east3-opt/linked/selfhost）は git 管理しない（`.gitignore` 対象）。** `python3 tools/gen/regenerate_golden.py` でローカルに再生成して使う。golden をコミットしてはならない。手動編集も禁止。
- **sample の再生成は `python3 tools/gen/regenerate_samples.py` でのみ行うこと。**

## 2. tools/ 配置ルール

- **`tools/` 直下への新規 `.py` ファイル追加は禁止。** 必ず `tools/check/` / `tools/gen/` / `tools/run/` のいずれかに配置する。
- **新規ファイルを追加・削除・移動した場合は `tools/README.md`（台帳）を必ず同時に更新する。** 台帳の更新なしにファイルを追加してはならない。
- CI チェック `python3 tools/check/check_tools_ledger.py` が台帳との突合を行う。台帳に記載のないファイルがあれば FAIL になる。
- `tools/unregistered/` は削除済み。一時的・実験的なスクリプトも最初から正規ディレクトリ（`tools/check/` / `tools/gen/` / `tools/run/`）に配置し、不要になったら削除する。

## 3. test/ 配置ルール

- **`test/fixture/` 配下のディレクトリ構造を勝手に作らないこと。** 既存のディレクトリ構成（`source/py/`, `east1/py/`, `east2/`, `east3/`, `east3-opt/`, `linked/`）に従う。
- **`test/` 直下に新しいサブディレクトリを作らないこと**（`test/fixtures/` のような typo ディレクトリを防ぐ）。

## 4. emitter の禁止事項

- emitter は EAST3 を忠実にレンダリングする。以下は禁止:
  - cast を追加する（EAST に cast がないなら resolve のバグ）
  - 変数の型を変更する
  - for-range のループ変数の型を変更する
  - mapping.json にない名前変換をハードコードする
  - 型推論を再実装する
  - **EAST の body を走査して型を判定する**（例: Return ノードの有無で戻り値型を推測する）
- **EAST の情報が不足している場合は、emitter にワークアラウンドを書くのではなく、EAST（resolve/compile/optimize）を修正すること。**
- **workaround が必要に見える場合は、実装する前にまずユーザーに報告すること。** spec 違反の実装を入れてはならない。
- 詳細は `docs/ja/spec/spec-emitter-guide.md` を参照。

## 5. runtime の禁止事項

- runtime ヘッダーに type_id テーブルのサイズや値をハードコードしてはならない（`g_type_table[4096]` のような固定サイズ配列は禁止）。
- 手書き TID 定数（`PYTRA_TID_VALUE_ERROR = 12` 等）は禁止。linker が生成した `pytra.built_in.type_id_table` の定数を使う。
- 正本ソース（`src/pytra/utils/*.py` 等）を変換器の制約に合わせて書き換えてはならない（例: `with` 文を手動 open/close に崩す）。emitter が対応するのが正しい対処。

## 6. コミット運用

- 作業内容が論理的にまとまった時点で、ユーザーの都度許可なしにコミットしてよい。
- コミットは論理単位で分割し、変更意図が分かるメッセージを付ける。
- TODO 消化コミットはメッセージに `ID` を含める（例: `[ID: P0-XXX-01] ...`）。
- **タスク完了時は `docs/ja/todo/index.md` の該当タスクの `[ ]` を `[x]` に変更し、完了メモ（件数等）を追記してコミットすること。** チェックを入れ忘れると、他のエージェントが同じタスクに着手してしまう。

## 7. バージョン更新

- 内部バージョンゲート（`transpiler_versions.json`）は廃止済み。変更の検証は parity check で行う。
- 対外リリース版は `docs/VERSION` で管理する。`PATCH` はエージェントが更新してよい。`MINOR` / `MAJOR` はユーザーの明示指示がある場合のみ。

## 8. selfhost 運用

- selfhost 対象コード（`src/toolchain/misc/east.py` 系）では、動的 import（`try/except ImportError` フォールバック、`importlib` による遅延 import）を使わない。
- selfhost 対象コードでは、Python 標準 `ast` モジュールへの依存を禁止する。
- トランスパイル対象の Python コードでは、Python 標準モジュール（`json`, `pathlib`, `sys` 等）の直接 `import` を禁止する。`pytra.std.*` を使う。
