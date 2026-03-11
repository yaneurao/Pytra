# P1: import diagnostics の構造化

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-IMPORT-DIAGNOSTIC-STRUCTURE-01`

背景:
- relative import / wildcard import / duplicate import binding まわりの診断は、現状 [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py) の `load_east_document()` で英語断片の substring matching に依存している。
- parser 側の feature 実装は進んでいるが、frontend の診断 transport が文字列依存のままだと、parser 側メッセージ変更がそのまま CLI 契約破壊になる。
- 特に `duplicate import binding` は parser/import semantics 由来の診断であり、将来的には parser → frontend 間で structured envelope に寄せたい。

目的:
- frontend import diagnostics の分類を 1 箇所へ集約し、現在の user-facing 契約を壊さずに brittle な分岐を減らす。
- parser 側 import diagnostics を structured envelope へ段階的に移せる seam を先に作る。

対象:
- `transpile_cli.load_east_document()` の import 例外分類 helper 化
- import diagnostics 専用 unit test の追加
- parser / import semantics 側 duplicate-binding 診断の structured 化準備
- TODO / plan / English mirror の整合

非対象:
- relative import / wildcard import の新機能追加
- missing module / cycle / import graph アルゴリズム変更
- import diagnostics 以外の syntax error transport 全般の再設計

受け入れ基準:
- `wildcard` / `relative import` / `duplicate_binding` の現行 CLI category/detail 契約を維持したまま、`load_east_document()` の import 分岐が helper 1 箇所へ集約されること。
- import diagnostics helper を直接叩く focused unit test が追加されること。
- parser/import semantics 側 duplicate-binding の次段 structured 化に向けた slice が plan に明記されていること。
- 既存 relative import / wildcard import 回帰を壊さないこと。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_import_diagnostics.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-11: TODO が空になったため、relative import / wildcard import 実装の次段として import diagnostics transport の構造化を `P1` 起票した。v1 は current CLI 契約維持を優先し、まず frontend の substring matching を helper 境界へ集約する。
- 2026-03-11: `S2-01` として `load_east_document()` の import 例外分類を `_classify_import_user_error()` へ集約し、wildcard / relative / duplicate-binding の current CLI contract を focused unit test と 1 本の integration test で固定した。

## 分解

- [x] [ID: P1-IMPORT-DIAGNOSTIC-STRUCTURE-01-S1-01] current import diagnostics transport と staged end state を棚卸しし、plan/TODO に固定する。
- [x] [ID: P1-IMPORT-DIAGNOSTIC-STRUCTURE-01-S2-01] `transpile_cli.load_east_document()` の import 例外分類を helper 1 箇所へ集約し、focused unit test を追加する。
- [ ] [ID: P1-IMPORT-DIAGNOSTIC-STRUCTURE-01-S2-02] duplicate import binding を parser/import semantics 側から structured envelope として transport できる seam を追加する。
- [ ] [ID: P1-IMPORT-DIAGNOSTIC-STRUCTURE-01-S3-01] import diagnostics の remaining ad hoc 文字列依存を整理し、archive 可能な end state にまとめる。
