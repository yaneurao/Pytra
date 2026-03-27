<a href="../../../en/plans/archive/20260311-p2-east-core-modularization.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: EAST core.py / test_east_core.py を機能単位で分割する

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-EAST-CORE-MODULARIZATION-01`

背景:
- `src/toolchain/ir/core.py` は selfhost parser の機能追加と helper 分解を重ねた結果、約 1 万行まで肥大化した。
- `test/unit/ir/test_east_core.py` も source guard を 1 ファイルへ集約したため、責務単位の変更でも追跡範囲が広すぎる。
- 直近の P2 では helper 1 個ごとの細かい commit が増え、局所整理は進んだ一方で、ファイル分割と進捗整理が後回しになった。

目的:
- `core.py` と `test_east_core.py` を suffix parser / annotation / builder / source guard の責務単位へ再分割し、今後の compiler 内部改善を cluster 単位で進められる状態にする。

対象:
- `src/toolchain/ir/core.py`
- `src/toolchain/ir/core_expr_*.py`
- `test/unit/ir/test_east_core.py`
- 必要に応じて `test/unit/ir/test_east_*.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p2-east-core-modularization.md` / `docs/en/plans/p2-east-core-modularization.md`

非対象:
- EAST/EAST3 の新仕様追加
- nominal ADT / runtime / backend rollout そのもの
- selfhost parser 以外の frontend 全面刷新

受け入れ基準:
- `core.py` の責務が少なくとも `call` / `attr` / `subscript` / builder / statement parser のような機能単位で分割され、今後の変更が mixin/module 単位で閉じやすくなる。
- `test_east_core.py` の source guard が cluster 単位へ整理され、必要なものは dedicated test module へ移る。
- 進捗メモは TODO では 1 行要約のみ、詳細は本計画の `決定ログ` へ集約される。
- representative regression として `test_east_core.py`、`test_prepare_selfhost_source.py`、`tools/build_selfhost.py` が継続して通る。

確認コマンド:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_todo_priority.py`
- `git diff --check`

分解:
- [x] [ID: P2-EAST-CORE-MODULARIZATION-01-S1-01] `core.py` / `test_east_core.py` の残 cluster を棚卸しし、split 境界を `suffix parser` / `annotation` / `builder` / `source guard` で固定する。
- [x] [ID: P2-EAST-CORE-MODULARIZATION-01-S2-01] `attr/subscript annotation` cluster を dedicated mixin module へ抽出し、`core.py` から state/build-dispatch 群を後退させる。
- [x] [ID: P2-EAST-CORE-MODULARIZATION-01-S2-02] `call/attr/subscript` suffix parser の残 cluster を dedicated module へ寄せ、`core.py` の postfix parser を orchestration 中心へ縮める。
- [x] [ID: P2-EAST-CORE-MODULARIZATION-01-S3-01] `test_east_core.py` の source guard を機能別 test module へ分割し、`core.py` split と 1 対 1 で追える構成にする。
- [x] [ID: P2-EAST-CORE-MODULARIZATION-01-S3-02] TODO/plan の進捗メモを圧縮し、細粒度履歴は `決定ログ` のみへ寄せる。
- [x] [ID: P2-EAST-CORE-MODULARIZATION-01-S4-01] representative regression を再実行して非退行を確認し、完了タスクを archive へ移す。

## S1-01 棚卸し

2026-03-11 時点での主要 cluster は次の通り。

1. `call suffix / call args`
   - 一部は `core_expr_call_args.py` / `core_expr_call_suffix.py` へ移動済み。
   - 残る課題は source guard の粒度統一。
2. `attr/subscript suffix`
   - token/state helper は `core_expr_attr_subscript_suffix.py` へ移動済み。
   - annotation/build-dispatch はまだ `core.py` に残る。
3. `call / attr / subscript annotation`
   - call annotation は `core_expr_call_annotation.py` へ一部抽出済み。
   - attr/subscript annotation は未抽出で、次の本命 cluster。
4. `builder / statement parser`
   - `_sh_make_*` 群と statement parser はまだ `core.py` へ集中している。
5. `source guard`
   - `test_east_core.py` は split 済み module の guard と未 split 部分の guard が同居している。

初手として `attr/subscript annotation` を外す理由:
- 既に `attr/subscript suffix` module があるため、周辺責務が近く、差分を閉じやすい。
- `core.py` 側では build 本体を残して state/build-dispatch だけ先に外せる。
- `test_east_core.py` の guard も `core.py` と新 module の 2 つに整理しやすい。

## 決定ログ

- 2026-03-11: ユーザー指摘により、`core.py` を helper 1 個ずつではなく cluster 単位で分割する方針へ切り替えた。進捗メモも TODO から減らし、本計画へ集約する。
- 2026-03-11: `S1-01` として `core.py` / `test_east_core.py` の残 cluster を棚卸しし、最初の split 対象を `attr/subscript annotation` に固定した。
- 2026-03-11: `S2-01` として `attr/subscript annotation` cluster を `core_expr_attr_subscript_annotation.py` へ抽出した。`core.py` には build 本体と top-level `_sh_*` 依存の強い orchestration を残し、state/build-dispatch helper だけを後退させる境界で切っている。
- 2026-03-11: `P1-IR-CORE-DECOMPOSITION-01` の完了時点で `core.py=214 lines` / `test_east_core.py=44 lines` まで縮小し、`call/attr/subscript` suffix parser、call/attr/subscript annotation、source-contract split、進捗メモ圧縮、representative IR/selfhost regression が本 plan の acceptance criteria を満たした。重複管理を避けるため、本 task は P1 end state により fulfilled として archive へ移す。
