# P1: `east2_to_east3_lowering.py` の残 cluster を第二波で分割する

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-EAST23-LOWERING-ORCHESTRATION-01`

背景:
- first wave で `type summary` / `type_id predicate lowering` / `nominal ADT metadata` は dedicated module へ移り、main file は 833 行まで縮んだ。
- それでも `src/toolchain/ir/east2_to_east3_lowering.py` には `call metadata/json decode fastpath`、`Assign/For/ForRange` lowering、`Attribute/Match/ForCore` lowering と node dispatch が残っている。
- ここが 1 file に残ると、JsonValue / nominal ADT / typed boundary 変更の review 範囲が依然として広く、main file end state も曖昧なままになる。

目的:
- `east2_to_east3_lowering.py` の残 cluster を dedicated module へ寄せ、main file を orchestration / dispatch / lifecycle 中心へ整理する。
- second-wave split 後の責務境界を source-contract と representative regression で固定する。

対象:
- `src/toolchain/ir/east2_to_east3_lowering.py`
- `src/toolchain/ir/east2_to_east3_*.py`
- `test/unit/ir/test_east2_to_east3_lowering.py`
- `test/unit/ir/test_east2_to_east3_source_contract.py`
- `test/unit/ir/test_east2_to_east3_split_regressions.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p1-east23-lowering-orchestration-split.md` / `docs/en/plans/p1-east23-lowering-orchestration-split.md`

非対象:
- EAST2/EAST3 の仕様変更
- nominal ADT / JsonValue の language feature 追加
- backend 側の新機能追加

受け入れ基準:
- `call metadata/json decode fastpath` cluster が dedicated module へ移る。
- `stmt lowering` または `dispatch/orchestration` の少なくとも 1 cluster が dedicated module へ移る。
- main file は `lower_east2_to_east3()`、dispatch mode / legacy bridge lifecycle、node dispatch orchestration を主責務にする。
- source-contract と representative regression (`test_east2_to_east3*.py`, `test_prepare_selfhost_source.py`, `build_selfhost.py`) が通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east2_to_east3*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

分解:
- [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-01] 残 cluster を `call_metadata` / `stmt_lowering` / `dispatch_orchestration` に棚卸しし、split 順を固定する。
- [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-02] 進捗メモは bundle 単位に圧縮し、main file の end state を `dispatch + lifecycle` 中心に固定する。
- [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-01] `call metadata` / `json decode fastpath` cluster を dedicated module へ分割する。
- [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-02] `Assign` / `For` / `ForRange` lowering cluster を dedicated module へ分割する。
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-03] `Attribute` / `Match` / `ForCore` loweringと node dispatch orchestration を dedicated module へ分割する。
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S3-01] source-contract と representative regression を second-wave split layout へ追従させる。
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S4-01] docs / TODO / archive を更新して閉じる。

決定ログ:
- 2026-03-11: first-wave split 完了後の残り 833 行を棚卸しし、`call metadata/json decode`, `stmt lowering`, `dispatch/orchestration` の 3 cluster に整理した。
- 2026-03-11: second wave の先頭は `call metadata/json decode fastpath` を優先する。JsonValue contract と object bridge fallback が同居しており、main file の複雑さに対する削減効果が最も高いため。
- 2026-03-11: 進捗メモは cluster/bundle 単位の 1 行に留め、helper 単位の履歴は決定ログか commit message にのみ残す。
- 2026-03-11: `S2-01` として `_infer_json_semantic_tag` / `_build_json_decode_meta` / `_lower_representative_json_decode_call` / `_decorate_call_metadata` を `east2_to_east3_call_metadata.py` へ切り出した。source-contract には dedicated module ownership assert を追加し、split regression には representative `json.value.as_obj` lane を追加した。
- 2026-03-11: `S2-02` として assign target planning と `_lower_assignment_like_stmt` / `_lower_for_stmt` / `_lower_forrange_stmt` / `_lower_forcore_stmt` を `east2_to_east3_stmt_lowering.py` へ切り出した。source-contract には stmt-module ownership assert を追加し、split regression には `Box + StaticRangeForPlan` の representative lane を追加した。
