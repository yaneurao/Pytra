# P1: `east2_to_east3_lowering.py` を cluster 単位で分割する

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-EAST23-LOWERING-DECOMPOSITION-01`

背景:
- `toolchain.ir.core` と expr/parser facade の分割は進み、`core.py` 側の巨大 monolith はほぼ解消した。
- 一方で `src/toolchain/ir/east2_to_east3_lowering.py` は 1800 行超のままで、`type summary` / `nominal ADT metadata` / `type_id predicate lowering` / `call metadata` / `statement lowering` が 1 file に同居している。
- この状態では nominal ADT や type-expr lane の調整で review 範囲が広くなり、どの helper 群が同じ責務かも見えにくい。

目的:
- `east2_to_east3_lowering.py` を cluster 単位で dedicated module へ分割し、main file は orchestration と representative lowering に寄せる。
- split 後の責務境界を source-contract と representative regression で固定する。

対象:
- `src/toolchain/ir/east2_to_east3_lowering.py`
- `src/toolchain/ir/east2_to_east3_*.py`
- `test/unit/ir/test_east2_to_east3_lowering.py`
- `test/unit/ir/test_east2_to_east3_source_contract.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p1-east23-lowering-decomposition.md` / `docs/en/plans/p1-east23-lowering-decomposition.md`

非対象:
- EAST2/EAST3 の仕様変更
- nominal ADT / JsonValue の language feature 追加
- backend 側の新機能追加

受け入れ基準:
- `east2_to_east3_lowering.py` から `type summary` / `nominal ADT metadata` / `type_id predicate lowering` の少なくとも 3 cluster が dedicated module へ移る。
- main file は `lower_east2_to_east3()` と node-walk / representative lowering orchestration を主責務にする。
- source-contract test が split 後の import surface を固定する。
- representative regression (`test_east2_to_east3_lowering.py`, `test_prepare_selfhost_source.py`, `build_selfhost.py`) が通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east2_to_east3*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

分解:
- [x] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S1-01] `east2_to_east3_lowering.py` の helper を `type_summary` / `type_id_predicate` / `nominal_adt_meta` / `call_metadata` / `stmt_orchestration` に棚卸しし、split boundary を固定する。
- [x] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S1-02] TODO / plan の進捗メモは bundle 単位に圧縮し、helper 単位の列挙を避ける運用を固定する。
- [x] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S2-01] `type summary` / `nominal decl summary` / `json receiver contract` cluster を dedicated module へ分割する。
- [x] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S2-02] `type_id predicate` / `isinstance` / `issubclass` lowering cluster を dedicated module へ分割する。
- [ ] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S2-03] `nominal ADT ctor/projection/match metadata` cluster を dedicated module へ分割する。
- [ ] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S3-01] source-contract と representative regression を split 後の module layout へ追従させる。
- [ ] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S4-01] docs / TODO / archive を更新し、完了後は archive へ移す。

決定ログ:
- 2026-03-11: 初版作成。`core.py` / expr facade 分割の次に残る大型 monolith として `east2_to_east3_lowering.py` を対象に選んだ。
- 2026-03-11: first wave は `type summary` / `nominal ADT metadata` / `type_id predicate lowering` の 3 cluster を優先し、assignment/call/stmt orchestration は main file 側に残す。
- 2026-03-11: この task の進捗メモは bundle 単位の 1 行要約に留め、細かい helper 名は plan の決定ログか commit message に記録する。
- 2026-03-11: `S2-01` の first bundle として `type summary` / `nominal decl summary` / `json receiver contract` を `east2_to_east3_type_summary.py` へ移した。main file 側は `_swap_nominal_adt_decl_summary_table()` を介して table lifecycle を管理し、source-contract には dedicated `test_east2_to_east3_source_contract.py` を追加した。
- 2026-03-11: `S2-02` の second bundle として `type_id predicate` / `isinstance` / `issubclass` lowering を `east2_to_east3_type_id_predicate.py` へ移した。main file 側は `_lower_type_id_call_expr(...)` の import と dispatch 呼び出しに縮め、source-contract には split module の dedicated assert を追加した。
