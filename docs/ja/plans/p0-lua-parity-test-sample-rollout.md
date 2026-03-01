# P0: Lua parity 完走（test/fixture + sample）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-LUA-PARITY-ALL-01`
- 依存: `ID: P0-LUA-SAMPLE01-RUNTIME-01`（sample/01 の runtime 欠落解消）

背景:
- ユーザー要求として「`test/` と `sample/` の Lua parity 一致確認」が最優先で必要。
- 現状の Lua parity は過去に `toolchain_missing` 環境での確認が混在し、実行環境あり前提の完走記録が不足している。
- さらに `sample/lua/01` は runtime マッピング欠落（`perf_counter`/`png`）が残っており、`sample` 全件 parity の blocker になり得る。

目的:
- Lua backend について、fixture（`test/fixtures`）と sample（`sample/py`）の parity を実行環境ありで完走し、一致を固定する。
- stdout 一致に加えて、画像出力ケースの artifact サイズ一致も継続的に検証する。

対象:
- `tools/runtime_parity_check.py`
- `test/unit/test_runtime_parity_check_cli.py`（必要時）
- `test/unit/test_py2lua_smoke.py`
- `src/hooks/lua/emitter/lua_native_emitter.py`（parity 不一致時の修正）
- `src/runtime/lua/*`（必要時）
- `sample/lua/*.lua`（再生成確認）

非対象:
- Lua backend の性能最適化
- Lua 構文の可読性改善（別タスクで扱う）
- 他言語 backend の parity 改善

受け入れ基準:
- `check_py2lua_transpile.py` が成功する。
- fixture parity（`test/` 起点）が Lua で実行可能な対象セットで全 pass する。
- sample parity（`sample/py` 18件）が `--targets lua --all-samples` で全 pass する。
- 画像出力ケースで artifact サイズ不一致（`artifact_size_mismatch`）が 0 件である。
- 結果を plan の決定ログへ記録し、再発検知の導線（unit/CLI）を固定する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2lua_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua*.py' -v`
- `python3 tools/runtime_parity_check.py --case-root fixture --targets lua --ignore-unstable-stdout`
- `python3 tools/runtime_parity_check.py --case-root sample --targets lua --all-samples --ignore-unstable-stdout`
- `python3 tools/regenerate_samples.py --langs lua --force`

分解:
- [ ] [ID: P0-LUA-PARITY-ALL-01-S1-01] Lua parity 対象範囲（fixture 対象ケース / sample 全18件）を確定し、実行手順を固定する。
- [ ] [ID: P0-LUA-PARITY-ALL-01-S1-02] 依存タスク `P0-LUA-SAMPLE01-RUNTIME-01` の未解決項目を解消し、sample parity blocker を除去する。
- [ ] [ID: P0-LUA-PARITY-ALL-01-S2-01] `runtime_parity_check --case-root fixture --targets lua` を実行し、不一致を修正して全 pass にする。
- [ ] [ID: P0-LUA-PARITY-ALL-01-S2-02] `runtime_parity_check --case-root sample --targets lua --all-samples` を実行し、不一致を修正して全 pass にする。
- [ ] [ID: P0-LUA-PARITY-ALL-01-S2-03] 画像ケースの artifact サイズ一致（`artifact_size_mismatch=0`）を確認し、必要な runtime/emitter 修正を完了する。
- [ ] [ID: P0-LUA-PARITY-ALL-01-S3-01] parity 実行結果を決定ログへ記録し、unit/CLI 回帰（必要時）を追加して再発検知を固定する。

決定ログ:
- 2026-03-01: ユーザー指示により、Lua parity を `test/`（fixture）と `sample/` の双方で一致確認するタスクを P0 として起票した。
