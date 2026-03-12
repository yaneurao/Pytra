# P5 Backend Parity Secondary Rollout

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01`

目的:
- support matrix の secondary tier (`go`, `java`, `kt`, `scala`, `swift`, `nim`) に残っている未対応 cell を、live rollout task として順次実装する。

背景:
- secondary tier は matrix 上では conservative seed や limited reviewed cell が入っているが、active TODO に実装 queue が無い。
- representative tier 完了後に機械的に移れる実装順を持たないと、matrix は更新されても parity は進まない。

対象:
- secondary tier backend の representative feature cell 実装。
- `transpile_smoke` / `build_run_smoke` / `fail_closed` の evidence 追加。
- secondary tier cell の matrix / docs 同期。

非対象:
- representative tier の残課題。
- long-tail backend の rollout。
- parity matrix schema / taxonomy の変更。

受け入れ基準:
- secondary tier の backend 順と bundle 単位の rollout order が固定されている。
- 各 bundle が backend ごとの smoke / fail-closed evidence を伴う。
- representative tier 完了後に迷わず着手できる state になっている。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_backend_parity_matrix_contract.py`
- `python3 tools/check_backend_parity_secondary_rollout_inventory.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_parity_matrix_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_parity_secondary_rollout_inventory.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## 分解

- [x] [ID: P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01-S1-01] secondary tier の current residual cell と backend order を live rollout bundle として固定する。
- [x] [ID: P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01-S2-01] `go/java/kt` bundle の未対応 cell を representative evidence 付きで埋める。
- [x] [ID: P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01-S2-02] `scala/swift/nim` bundle の未対応 cell を representative evidence 付きで埋める。
- [ ] [ID: P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01-S3-01] secondary tier の matrix / docs / support wording を current rollout state に同期して閉じる。

## 決定ログ

- 2026-03-12: secondary tier は `go/java/kt -> scala/swift/nim` の 2 bundle で扱い、bundle 内では shared fixture と regression を優先して前進量を確保する。
- 2026-03-12: representative tier が未完了の間は待機タスクとし、実装着手順だけを先に固定する。
- 2026-03-13: `S1-01` として `backend_parity_secondary_rollout_inventory.py` / checker / unit test を追加し、secondary residual cell を matrix seed から固定した。bundle order は `go/java/kt` の first bundle と `scala/swift/nim` の second bundle に確定し、`go/java/kt` では tuple/lambda/comprehension/iterator/std 実装 gap、`scala/swift` ではさらに `for_range/range` gap、`nim` では代わりに `virtual_dispatch` gap を持つ current snapshot を handoff manifest に反映した。
- 2026-03-13: `S2-01` として `go/java/kt` bundle を close した。`tuple_assign.py` が要求する `Swap` stmt を `go/java/kotlin` emitter に追加し、secondary representative fixture bundle smoke で `tuple/lambda/comprehension/for_range/try_raise/enumerate/zip/isinstance/json/pathlib/enum/argparse/math/re` を transpile evidence として固定したうえで、matrix は `go/java/kt` の residual cell を `supported/transpile_smoke` へ引き上げた。secondary residual inventory は `go/java/kt` を completed backend として空 bundle marker に縮退し、next bundle を `scala/swift/nim` に進めた。
- 2026-03-13: `S2-02` として `scala/swift/nim` bundle を close した。`scala/swift` の `for_range/range`、`nim` の `virtual_dispatch` と `Swap` lowering を representative transpile smoke で固定し、matrix は secondary tier 全 backend を `supported/transpile_smoke` へ引き上げた。secondary residual inventory は空になり、handoff は `completed_backends = secondary tier 全体`, `next_backend = None`, `remaining_backends = ()` に縮退した。
