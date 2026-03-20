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

## S1-01 棚卸し結果（2026-03-04）

- `tools`（最優先で置換）:
  - direct CLI 参照: `check_noncpp_east3_contract.py`, `check_transpiler_version_gate.py`
  - selfhost 参照: `check_multilang_selfhost_stage1.py`, `check_multilang_selfhost_multistage.py`, `prepare_selfhost_source_cs.py`, `check_cs_single_source_selfhost_compile.py`
- `test/unit`（次点で置換）:
  - wrapper module import 依存: `test_py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,scala,php,nim}_smoke.py`（13本）
  - wrapper 実ファイル文字列依存（`ROOT / "src" / "py2*.py"` を読む検証）: `test_py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,scala}_smoke.py`（11本）
- `docs`（実運用導線を先に置換）:
  - user-facing: `docs/ja/how-to-use.md`, `docs/en/how-to-use.md`
  - spec: `docs/ja/spec/*.md`, `docs/en/spec/*.md` に `py2*.py` 名が残存
  - 履歴用途の `docs/*/plans` / `docs/*/todo/archive` は事実記録として維持し、`S2-03` では運用ドキュメント側を優先置換する

置換順（確定）:
1. `S2-01` で `tools` の direct wrapper 参照を `py2x.py` / `py2x-selfhost.py` と backend module 参照へ更新する。
2. `S2-02` で `test/unit` の import/文字列依存を `py2x` 基準へ更新する。
3. `S2-03` で `docs/ja|en` の運用・仕様ドキュメントを `py2x` 正規入口へ更新する。
4. `S3-01` で `src/py2*.py` wrapper 群と `toolchain/compiler/py2x_wrapper.py` を削除する。
5. `S3-02/S3-03` で再流入ガードと回帰を通して固定する。

## 分解

- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S1-01] wrapper 参照の残存箇所を `tools/test/docs/selfhost` で再棚卸しし、置換順を確定する。
- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S2-01] `tools/` の wrapper 直参照を `py2x` / backend module 参照へ置換する。
- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S2-02] `test/unit` の wrapper ファイル依存テストを `py2x` 基準または backend module 基準へ置換する。
- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S2-03] `docs/ja` / `docs/en` の wrapper 名記述を `py2x` 正規入口へ更新する。
- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S3-01] `src/py2*.py` wrapper 群と `toolchain/compiler/py2x_wrapper.py` を削除する（`py2x.py` / `py2x-selfhost.py` は除外）。
- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S3-02] wrapper 再流入を検知する静的ガードを更新し、削除後構成を固定する。
- [x] [ID: P1-PY2X-WRAPPER-REMOVE-REOPEN-01-S3-03] transpile/smoke 回帰を実行し、wrapper 撤去後の非退行を確認する。

決定ログ:
- 2026-03-04: archive 済み `P1-PY2X-SINGLE-ENTRY-01` を再開対象として差し戻し。完了条件を「`py2x` 導入」ではなく「legacy wrapper 実ファイル撤去」へ再定義した。
- 2026-03-04: `S1-01` として wrapper 参照を `tools/test/docs/selfhost` で再棚卸しし、置換順を「tools -> test -> docs -> wrapper削除 -> guard/回帰」に確定した。
- 2026-03-04: `S2-01` の先行分として `tools/check_noncpp_east3_contract.py` の wrapper 実ファイル前提チェックを除去し、`py2x.py` + backend layer + smoke 契約検証へ整理した。合わせて `tools/check_transpiler_version_gate.py` の言語 direct dependency を `src/py2*.py` から `src/py2x.py` へ置換し、`tools/check_legacy_cli_references.py` の allowlist から上記2ファイルを除外して再流入を抑止した。
- 2026-03-04: `S2-01` を完了。`tools/check_multilang_selfhost_stage1.py` / `tools/check_multilang_selfhost_multistage.py` を `src/py2x.py --target <lang>` 基準へ更新し、JS/RS/CS の stage2/stage3 実行でも `--target` を明示。`tools/prepare_selfhost_source_cs.py` は `src/py2x.py -> selfhost/py2x_cs.py` seed 生成へ簡素化し、`tools/check_cs_single_source_selfhost_compile.py` も `py2x` 基準へ移行した。`rg -n \"py2(rs|cs|js|ts|go|java|kotlin|swift|rb|lua|scala|php|nim)\\.py\" tools` が 0 件、関連ツール実行（stage1/multistage/cs-single-source）はクラッシュなしを確認。
- 2026-03-04: `S2-02` を完了。`test/unit/test_py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,scala,php,nim}_smoke.py` の wrapper import / wrapper 実ファイル文字列依存を backend module + `load_east3_document(..., target_lang=<lang>)` 基準へ置換し、Lua smoke の runtime 外出し（`dofile("py_runtime.lua")`）期待値へ追従。`PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py' -v`（298 tests）で `OK` を確認。
- 2026-03-04: `S2-03` を完了。運用ドキュメントの実行例を `py2x.py --target <lang>` 基準へ統一し、`how-to-use` の互換ラッパ説明を非推奨/段階撤去方針へ更新。`spec-runtime/spec-options/spec-east/spec-east3-optimizer/spec-dev/spec-tools`（ja/en）で `src/py2cpp.py` 前提を `src/py2x.py --target cpp` または `src/toolchain/emit/cpp/cli.py` へ置換し、selfhost 同期手順は `python3 tools/prepare_selfhost_source.py` を正本化。`rg -n \"python3?\\s+src/py2(rs|cs|js|ts|go|java|kotlin|swift|rb|lua|scala|php|nim|cpp)\\.py\" docs/ja docs/en --glob '!**/plans/**' --glob '!**/todo/**' --glob '!**/archive/**' --glob '!**/language/**'` が 0 件であることを確認。
- 2026-03-04: `S3-01` を完了。`src/py2{rs,cs,js,ts,go,java,kotlin,swift,rb,lua,scala,php,nim}.py` と `src/toolchain/compiler/py2x_wrapper.py` を削除し、残存依存は `test/unit/test_error_classification_cross_lang.py` を `load_east3_document(..., target_lang=...)` 基準へ置換、`src/toolchain/emit/cs/emitter/cs_emitter.py` の anchor を `src/py2x.py` へ更新して解消した。回帰として `python3 tools/check_legacy_cli_references.py`、`python3 -m unittest discover -s test/unit -p 'test_error_classification_cross_lang.py' -v`、`PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py' -v`（298 tests）を通過確認。
- 2026-03-04: `S3-02` を完了。`tools/check_legacy_cli_references.py` を更新し、`src/py2x.py` / `src/py2x-selfhost.py` 以外の `src/py2*.py` 実ファイル再流入と `toolchain/compiler/py2x_wrapper.py` の再生成を fail-fast 検知するようにした。合わせて path/import の許可リストを空にして削除後構成を固定し、`python3 tools/check_legacy_cli_references.py` の `OK` を確認。
- 2026-03-04: `S3-03` を完了。`check_py2{cpp,rs,cs,js,ts,go,java,swift,kotlin,rb,lua,scala,php,nim}_transpile.py` を全件実行して fail=0 を確認し、`PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2*_smoke.py' -v`（298 tests）も `OK` を確認。wrapper撤去後の transpile/smoke 非退行を固定した。
