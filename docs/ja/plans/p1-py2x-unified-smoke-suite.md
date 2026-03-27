<a href="../../en/plans/p1-py2x-unified-smoke-suite.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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

- [x] [ID: P1-PY2X-SMOKE-UNIFY-01-S1-01] `test_py2*_smoke.py` の共通観点と言語固有観点を棚卸しし、共通化対象を確定する。
- [x] [ID: P1-PY2X-SMOKE-UNIFY-01-S2-01] `py2x` target パラメタライズの共通 smoke テスト（新規）を追加する。
- [x] [ID: P1-PY2X-SMOKE-UNIFY-01-S2-02] 各言語 smoke から共通化済みケースを削減し、言語固有検証のみを残す。
- [x] [ID: P1-PY2X-SMOKE-UNIFY-01-S2-03] 共通 smoke と言語固有 smoke の責務境界をテストコード内コメントと計画書へ明記する。
- [x] [ID: P1-PY2X-SMOKE-UNIFY-01-S3-01] unit/transpile 回帰を実行し、統合後の非退行を確認する。
- [x] [ID: P1-PY2X-SMOKE-UNIFY-01-S3-02] `docs/ja/spec`（必要なら `docs/en/spec`）へ smoke テスト運用ルールを反映する。

決定ログ:
- 2026-03-04: ユーザー指示により、「全言語を1つの smoke に統一」案を採用。検知力維持のため、最終形は「共通 smoke + 言語固有 smoke」の2層構成とする。
- 2026-03-04: `S1-01` を完了。`test/unit/test_py2*_smoke.py`（14本）のテスト名を棚卸しし、共通化対象を確定した。共通 smoke へ寄せる対象は `(A) stage2拒否`（14/14）, `(B) CLI最小成功`（14/14）, `(C) load_east default/from_json + profile読込`（13/14）, `(D) add fixture 最小 transpile`（13/14）。`py2cpp` は `load_east/profile` 系を持たないため、共通 smoke では `target=cpp` に対しては `py2x` CLI 検証 + stage2拒否を必須、`load_east/profile` は non-cpp 13言語を必須にする方針を確定した。固有観点は重複を除いて 192 件あり、`S2-02` で各言語 smoke から共通観点のみ削減する。
- 2026-03-04: `S2-01` を完了。`test/unit/test_py2x_smoke_common.py` を新規追加し、`py2x --target` パラメタライズで共通 smoke を実装した。全14言語向けに `CLI最小成功` と `stage2拒否`、non-cpp 13言語向けに `load_east default/from_json` と `add fixture transpile`、加えて non-cpp backend spec の core hook 検証を追加。`PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2x_smoke*.py' -v`（6 tests）で `OK` を確認。
- 2026-03-04: `S2-02` を完了。既存 `test_py2*_smoke.py` 14本から共通化済みケース（CLI成功/`--east-stage 2`拒否/`load_east default+json`/`add fixture`）を削減し、言語固有検証のみを残した。削減件数は 53 件（`py2cpp` 1件 + 非cpp 13言語×4件）。`PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py' -v` は 232 tests `OK`、`test_py2x_smoke*.py` は 6 tests `OK` を確認。
- 2026-03-04: `S2-03` を完了。`test_py2x_smoke_common.py` のモジュールドキュメントに「共通責務」を明記し、`test_py2{cpp,rs,cs,js,ts,go,java,swift,kotlin,rb,lua,scala,php,nim}_smoke.py` 14本に「言語固有責務のみを保持する」コメントを追加した。責務境界をコード上で明示した状態で、`test_py2x_smoke*.py`（6 tests）と `test_py2*_smoke.py`（232 tests）の `OK` を再確認。
- 2026-03-04: `S3-01` を完了。回帰中に `check_py2js_transpile.py` が `check_noncpp_east3_contract.py` の旧前提（各言語 smoke に共通ケースが残る前提）で失敗したため、同スクリプトを新構成へ更新した。`test_py2x_smoke_common.py` の必須パターン検査を追加し、各言語 smoke には責務境界コメント必須 + 共通ケース関数禁止を適用。更新後に `check_py2{cpp,rs,cs,js,ts,go,java,swift,kotlin,rb,lua,scala,php,nim}_transpile.py` 全件 `OK`、`test_py2x_smoke*.py` 6件 `OK`、`test_py2*_smoke.py` 232件 `OK` を確認。
- 2026-03-04: `S3-02` を完了。`docs/ja/spec/spec-tools.md` と `docs/en/spec/spec-tools.md` に「共通 smoke は `test_py2x_smoke_common.py`、言語別 smoke は言語固有契約のみ」の運用ルールを追記し、`check_noncpp_east3_contract.py` を含む推奨回帰順（共通 smoke -> 言語別 smoke -> transpile check）を明文化した。

## S1-01 棚卸し結果（2026-03-04）

- 対象: `test/unit/test_py2*_smoke.py` 14本（`cpp,rs,cs,js,ts,go,java,swift,kotlin,rb,lua,scala,php,nim`）
- 集計結果（関数名ベース）:
  - 共通候補A: `stage2` 拒否系テスト 14/14
  - 共通候補B: CLI最小成功系テスト 14/14（命名差あり）
  - 共通候補C: `load_east_defaults_to_stage3...` + `load_east_from_json` + `load_<lang>_profile_contains_core_sections` 13/14（cpp除く）
  - 共通候補D: `transpile_add_fixture_*` 13/14（cpp除く）
  - 言語固有テスト: 192件（主に emitter/runtime 契約）
- `S2-01` で追加する共通 smoke の最小責務:
  - 全14言語: `py2x` CLI最小成功 / `--east-stage 2` 拒否
  - 非cpp 13言語: `load_east` default/from_json / profile / add-fixture transpile
- `S2-02` では各言語 smoke から上記共通責務のみ削減し、固有契約（コード生成断片・runtime接続・言語固有回帰）は残置する。
