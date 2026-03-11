# P1: `east2_to_east3_lowering.py` の main file 残 cluster を second wave で分割する

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-EAST23-LOWERING-ORCHESTRATION-01`

背景:
- `P1-EAST23-LOWERING-DECOMPOSITION-01` により `type_summary` / `type_id_predicate` / `nominal_adt_meta` は dedicated module へ移り、`east2_to_east3_lowering.py` は 833 行まで縮んだ。
- ただし main file にはまだ `call metadata` / `json decode fastpath`、`assignment/for` 系 lowering、`match/attribute/forcore` lowering、`_lower_node` dispatch と boundary helper が同居している。
- このままだと nominal ADT / type-expr / decode-first の小変更でも review 範囲が広く、main file を façade と呼べる状態にはまだ遠い。

目的:
- `east2_to_east3_lowering.py` の second wave として、main file に残る cluster を dedicated module へ移し、main file を `lower_east2_to_east3()` と lifecycle/orchestration 中心へ寄せる。
- source-contract と representative regression を second-wave layout に追従させ、次の改善が dedicated module 単位で進められる状態を作る。

対象:
- `src/toolchain/ir/east2_to_east3_lowering.py`
- `src/toolchain/ir/east2_to_east3_*.py`
- `test/unit/ir/test_east2_to_east3_lowering.py`
- `test/unit/ir/test_east2_to_east3_source_contract.py`
- `test/unit/selfhost/test_prepare_selfhost_source.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p1-east23-lowering-orchestration-split.md` / `docs/en/plans/p1-east23-lowering-orchestration-split.md`

非対象:
- EAST2/EAST3 の仕様変更
- nominal ADT / JsonValue の language feature 拡張
- backend 側の feature 追加

受け入れ基準:
- `call metadata` / `json decode fastpath` cluster が dedicated module へ移る。
- `assignment/for` 系 lowering と `match/attribute/forcore` 系 lowering が bundle 単位で dedicated module へ移る。
- `east2_to_east3_lowering.py` の主責務が `lower_east2_to_east3()`、node walk orchestration、table lifecycle まで縮む。
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
- [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-01] 残 cluster を `call_metadata` / `stmt_lowering` / `node_dispatch` / `boundary_helpers` に棚卸しし、split 順を固定する。
- [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-02] 進捗メモを bundle 単位に圧縮し、main file の end state を `orchestration + lifecycle` に固定する。
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-01] `call metadata` / `json decode fastpath` cluster を dedicated module へ分割する。
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-02] `assignment/for` 系の representative statement lowering cluster を dedicated module へ分割する。
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-03] `match/attribute/forcore` と node dispatch orchestration を dedicated module へ分割する。
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S3-01] source-contract と representative regression を second-wave layout へ追従させる。
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S4-01] docs / TODO / archive を更新して閉じる。

決定ログ:
- 2026-03-11: first wave 完了時点で main file の残 cluster は `call metadata + object fastpath`、`assignment/for lowering`、`match/attribute/forcore lowering`、`_lower_node + lifecycle helper` の 4 群に整理できた。
- 2026-03-11: second wave では `call metadata` を最初に切り、次に statement lowering、最後に node dispatch/orchestration を bundle 単位で外す。1 helper = 1 commit の粒度には戻さない。
