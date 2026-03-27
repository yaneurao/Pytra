<a href="../../../en/plans/archive/20260311-p0-selfhost-syntax-diagnostic-filepath.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: self-hosted parser syntax error に file:line:col を必ず付ける

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-SELFHOST-SYNTAX-DIAGNOSTIC-FILEPATH-01`

背景:
- 現在の CLI は self-hosted parser の syntax error を `user_syntax_error` へ包み直すが、detail line に入力ファイル名が落ちる経路が残っている。
- 代表例として `unsupported_syntax: self_hosted parser cannot parse expression token: * at 749:18` は line/col だけで、どの入力ファイルか分からない。
- import diagnostics は `file=...` 付きで比較的整っているのに、syntax error だけ path を欠くのは UX 上かなり不親切で、実験コードのデバッグを止める。

目的:
- self-hosted parser 由来の syntax error を、常に `file:line:col` 付き detail で返す。
- 既存の import diagnostics / structured user error contract を壊さず、syntax lane だけを改善する。

対象:
- `transpile_cli.load_east_document()` の self-hosted syntax error 分類
- file path / line / column を含む detail helper
- representative CLI / unit regression
- ja/en TODO / plan / docs の同期

非対象:
- import diagnostics の再設計
- Python host parser 側の SyntaxError format 変更
- editor integration / JSON diagnostic protocol

受け入れ基準:
- self-hosted parser が返す `unsupported_syntax: ... at line:col` 系 error は CLI detail に入力ファイル path を含むこと。
- import-related `input_invalid` / `unsupported_import_form` contract は維持されること。
- representative unit test と selfhost build が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_diagnostics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_self_hosted_signature.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `git diff --check`

決定ログ:
- 2026-03-11: v1 は self-hosted parser の syntax lane に限定し、detail line へ `file=... at line:col` を必ず残す。import diagnostics との統合再設計は非対象とする。
- 2026-03-11: `load_east_document()` は import diagnostics を先に判定し、その後で token mismatch 系 (`expected token ...` / `cannot parse expression token: ...`) だけを `path:line:col: message` へ正規化する helper で包み直す。`unsupported_syntax` 全体のカテゴリ変更は行わない。

## 分解

- [x] [ID: P0-SELFHOST-SYNTAX-DIAGNOSTIC-FILEPATH-01-S1-01] current syntax error gap と representative message contract を plan/TODO に固定する。
- [x] [ID: P0-SELFHOST-SYNTAX-DIAGNOSTIC-FILEPATH-01-S2-01] self-hosted syntax error helper を追加し、`load_east_document()` の分類経路を file-aware に揃える。
- [x] [ID: P0-SELFHOST-SYNTAX-DIAGNOSTIC-FILEPATH-01-S3-01] representative unit/CLI regression と docs を更新して閉じる。
