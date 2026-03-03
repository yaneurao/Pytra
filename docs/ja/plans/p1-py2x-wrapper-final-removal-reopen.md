# P1: `py2x` 統一の未完了回収（legacy `py2*.py` wrapper 完全撤去）

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01`

背景:
- `P1-PY2X-SINGLE-ENTRY-01` は archive 済みだが、`src/py2rs.py` / `src/py2cs.py` などの legacy wrapper が実体として残っている。
- `tools/check_multilang_selfhost_stage1.py`、`tools/check_noncpp_east3_contract.py`、`test/unit/test_py2*_smoke.py` などが wrapper ファイル名に依存している。
- この状態では「`py2x.py` 一本化」を名目上達成していても、実体としては wrapper 維持運用のままである。

目的:
- `py2x.py`（通常）/ `py2x-selfhost.py`（selfhost）を唯一の CLI 入口として確定する。
- `src/py2*.py` wrapper 群と `toolchain/compiler/py2x_wrapper.py` を撤去する。
- wrapper 前提の検査・回帰を `py2x` 前提へ置換し、再流入を防止する。

対象:
- `src/py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,scala,php,nim}.py` と `toolchain/compiler/py2x_wrapper.py`
- wrapper 名を直接参照する `tools/` / `test/` / `docs/` の置換
- 再発防止ガード（静的検査）

非対象:
- backend 変換ロジックの品質改善
- selfhost multistage 仕様の拡張
- EAST 仕様変更

受け入れ基準:
- `src/` 直下の `py2*.py` は `py2x.py` / `py2x-selfhost.py` のみ。
- `tools/` / `test/` / `docs/` に `src/py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,scala,php,nim}.py` 参照が残らない。
- wrapper 撤去後に主要 transpile check と smoke が通る。
- wrapper 再流入を CI/ローカルで fail-fast 検出できる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `rg -n "src/py2(rs|cs|js|ts|go|java|kotlin|swift|rb|lua|scala|php|nim)\\.py" src tools test docs`
- `python3 tools/check_legacy_cli_references.py`
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

- [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S1-01] wrapper 参照の残存箇所を `tools/test/docs/selfhost` で再棚卸しし、置換順を確定する。
- [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S2-01] `tools/` の wrapper 直参照を `py2x` / backend module 参照へ置換する。
- [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S2-02] `test/unit` の wrapper ファイル依存テストを `py2x` 基準または backend module 基準へ置換する。
- [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S2-03] `docs/ja` / `docs/en` の wrapper 名記述を `py2x` 正規入口へ更新する。
- [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S3-01] `src/py2*.py` wrapper 群と `toolchain/compiler/py2x_wrapper.py` を削除する（`py2x.py` / `py2x-selfhost.py` は除外）。
- [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S3-02] wrapper 再流入を検知する静的ガードを更新し、削除後構成を固定する。
- [ ] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S3-03] transpile/smoke 回帰を実行し、wrapper 撤去後の非退行を確認する。

決定ログ:
- 2026-03-04: archive 済み `P1-PY2X-SINGLE-ENTRY-01` を再開対象として差し戻し。完了条件を「`py2x` 導入」ではなく「legacy wrapper 実ファイル撤去」へ再定義した。
