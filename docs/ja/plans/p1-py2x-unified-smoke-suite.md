# P1: `py2x` 共通 smoke テスト統合（全言語）

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-PY2X-SMOKE-UNIFY-01`

背景:
- `test/unit/test_py2*_smoke.py` は CLI 経路・`--east-stage 2` 拒否・最小 fixture 変換など、共通の検証観点を各言語で重複実装している。
- 一方で、出力断片や runtime 契約の検証は言語固有性が高く、単純に 1 ファイルへ統合すると回帰検知力が落ちる。
- 現状は `py2x` が正規入口であり、共通観点は `py2x` 前提のパラメタライズ smoke として集約できる。

目的:
- 全言語の共通 smoke 観点を `py2x` ベースの 1 つの共通テスト群へ統合する。
- 言語固有 smoke は「その言語にしかない契約検証」のみに縮退し、重複を削減する。

対象:
- `test/unit/test_py2*_smoke.py` に散在する共通 smoke 観点の棚卸し
- `test/unit` への共通 smoke テスト追加（target パラメタライズ）
- 各言語 smoke から共通化済みケースを削減し、固有ケースへ整理
- `tools/check_py2*_transpile.py` や既存 unit 実行導線との整合確認

非対象:
- backend のコード生成品質改善
- parity テスト仕様の変更
- selfhost マルチステージ仕様の変更

受け入れ基準:
- 共通 smoke 観点（CLI 成功、`--east-stage 2` 拒否、基本変換）を 1 つの共通テスト群で全 target 実行できる。
- 各 `test_py2*_smoke.py` は言語固有契約検証中心に再編され、共通観点の重複が削減される。
- 主要 `test_py2*_smoke.py` と `check_py2*_transpile.py` が通る。
- 以降の新 target 追加時に共通 smoke へ1箇所追記するだけで最低限の回帰が有効化される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2x_smoke*.py'`
- `python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py'`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/check_py2nim_transpile.py`

## 分解

- [ ] [ID: P1-PY2X-SMOKE-UNIFY-01-S1-01] `test_py2*_smoke.py` の共通観点と言語固有観点を棚卸しし、共通化対象を確定する。
- [ ] [ID: P1-PY2X-SMOKE-UNIFY-01-S2-01] `py2x` target パラメタライズの共通 smoke テスト（新規）を追加する。
- [ ] [ID: P1-PY2X-SMOKE-UNIFY-01-S2-02] 各言語 smoke から共通化済みケースを削減し、言語固有検証のみを残す。
- [ ] [ID: P1-PY2X-SMOKE-UNIFY-01-S2-03] 共通 smoke と言語固有 smoke の責務境界をテストコード内コメントと計画書へ明記する。
- [ ] [ID: P1-PY2X-SMOKE-UNIFY-01-S3-01] unit/transpile 回帰を実行し、統合後の非退行を確認する。
- [ ] [ID: P1-PY2X-SMOKE-UNIFY-01-S3-02] `docs/ja/spec`（必要なら `docs/en/spec`）へ smoke テスト運用ルールを反映する。

決定ログ:
- 2026-03-04: ユーザー指示により、「全言語を1つの smoke に統一」案を採用。検知力維持のため、最終形は「共通 smoke + 言語固有 smoke」の2層構成とする。
