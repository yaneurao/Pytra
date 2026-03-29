<a href="../../../en/plans/archive/20260312-p4-backend-parity-representative-rollout.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P4 Backend Parity Representative Rollout

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01`

目的:
- support matrix で `not_started` / `fail_closed` のまま残っている representative tier (`cpp/rs/cs`) の未対応セルを、feature 実装で埋める live rollout track を復活させる。
- matrix / contract / docs の整備で終わっていた backend parity を、再び実装タスクとして前に進める。

背景:
- parity matrix と rollout tier はすでに archive 側で固定済みだが、active TODO からは「未対応セルを実装で埋める」作業が消えている。
- そのため support matrix は canonical source として存在しても、`not_started` cell を減らす live queue が無い。
- representative tier は `cpp -> rs -> cs` で、最優先の parity rollout wave に相当する。

対象:
- representative tier backend (`cpp`, `rs`, `cs`) の `support_state` が `not_started` / `fail_closed` の cell を実装で減らす作業。
- feature 実装、focused regression、matrix 更新、support wording 更新。

非対象:
- secondary / long-tail backend の実装。
- parity matrix schema や rollout tier contract の再設計。
- C++/Rust/C# すべてを同時に feature-complete にすること。

受け入れ基準:
- representative tier の未対応 cell に対して、実装対象・順序・evidence lane が明記されている。
- 各 slice が `feature -> backend -> evidence` の形で進められる。
- 実装後は matrix / docs / tooling contract を current state に同期する。
- 進捗は archived parity plan ではなく、この live plan に記録される。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_backend_parity_matrix_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_backend_parity_matrix_contract.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## 分解

- [x] [ID: P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S1-01] representative tier の current `not_started` / `fail_closed` cell を inventory 化し、live rollout order を固定する。
- [x] [ID: P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-01] `cpp` の未対応 representative cell を `build_run_smoke` または `transpile_smoke` へ引き上げる。
- [x] [ID: P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-02] `rs` の未対応 representative cell を `transpile_smoke` 以上へ引き上げる。
- [x] [ID: P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-03] `cs` の未対応 representative cell を `transpile_smoke` 以上へ引き上げる。
- [x] [ID: P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S3-01] representative tier の matrix / docs / support wording を current rollout state に同期して閉じる。

## 固定 inventory / rollout order

- 正本: [backend_parity_representative_rollout_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_representative_rollout_inventory.py)
- checker: [check_backend_parity_representative_rollout_inventory.py](/workspace/Pytra/tools/check/check_backend_parity_representative_rollout_inventory.py)
- current residual backend は空で、representative residual inventory は closed
- fixed bundle order:
  - `cpp_locked_baseline`
  - `rs_syntax_iter_bundle`
  - `rs_stdlib_bundle`
  - `cs_syntax_iter_bundle`
  - `cs_stdlib_bundle`
- current next backend は `None` で、残 bundle は closeout sync のみ

## 決定ログ

- 2026-03-12: parity matrix / rollout tier の contract は archive 済みのため、この plan は「未対応セルを実装で埋める live rollout」だけに責務を絞る。
- 2026-03-12: representative tier は `cpp -> rs -> cs` の順に進め、matrix の `support_state` 更新は各実装 slice の完了条件に含める。
- 2026-03-12: `S1-01` として representative residual inventory を tool 化し、現時点の `cpp` residual は空、live rollout の実装対象は `rs -> cs` だけだと固定した。bundle は syntax/iter と stdlib に分け、shared fixture を優先する。
- 2026-03-12: `S2-01` は no-op close とし、`cpp_locked_baseline` bundle と empty residual inventory をもって representative cpp lane は build/run baseline lock 済みと扱う。次 backend はそのまま `rs`。
- 2026-03-12: `S2-02` の first lift として `rs` の `builtin.type.isinstance` を `transpile_smoke` へ引き上げた。evidence は Rust smoke suite の representative fixture transpile と existing type-predicate lowering regressionsで固定する。
- 2026-03-12: `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-02-A1` と `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-03-A1` として `tuple_assign.py` の `Swap` lane と `lambda_basic.py` の closure parameter lane を `rs` / `cs` backend で実装し、matrix residual inventory から `syntax.assign.tuple_destructure` / `syntax.expr.lambda` を除外した。
- 2026-03-12: `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-02-A2` と `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-03-A2` として `comprehension.py` の representative smoke を `rs` / `cs` backend に追加し、`syntax.expr.list_comprehension` を matrix residual inventory から除外した。
- 2026-03-12: `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-02-A3` として `enumerate_basic.py` の representative smoke を `rs` backend に追加し、`builtin.iter.enumerate` を Rust residual inventory から除外した。
- 2026-03-12: `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-03-A4` として `is_instance.py` の representative smoke を `cs` backend に追加し、`builtin.type.isinstance` を C# residual inventory から除外した。
- 2026-03-12: `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-02-A4` として `inheritance_virtual_dispatch_multilang.py` の representative smoke を `rs` backend に追加し、`syntax.oop.virtual_dispatch` を Rust residual inventory から除外した。
- 2026-03-12: `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-02-A5` として `try_raise.py` の representative smoke を `rs` backend に追加し、`syntax.control.try_raise` を Rust residual inventory から除外した。Rust syntax/iter residual は `builtin.iter.zip` だけになった。
- 2026-03-12: `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-02-A6` として `json_extended.py` / `pathlib_extended.py` / `enum_extended.py` / `argparse_extended.py` / `re_extended.py` の representative smoke を `rs` backend に追加し、Rust stdlib residual をすべて `transpile_smoke` へ引き上げた。Rust residual は `builtin.iter.zip` だけになり、live next backend は引き続き `rs` のまま固定する。
- 2026-03-12: `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-02-A7` として `ok_generator_tuple_target.py` の `zip` lane を Rust iterator chain へ実装し、representative smoke を `rs` backend に追加した。これで `builtin.iter.zip` を Rust residual inventory から除外し、representative live next backend を `cs` へ進めた。
- 2026-03-12: `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-03-A5` として `for_range.py` の representative smoke を `cs` backend に追加し、`syntax.control.for_range` / `builtin.iter.range` を C# residual inventory から除外した。
- 2026-03-12: `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-03-A6` として `try_raise.py` の representative smoke を `cs` backend に追加し、`syntax.control.try_raise` を C# residual inventory から除外した。
- 2026-03-12: `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-03-A7` として C# emitter の list/generator comprehension tuple-target zip lane を実装し、`ok_generator_tuple_target.py` の representative smoke を追加して `builtin.iter.zip` を C# residual inventory から除外した。これで `cs_syntax_iter_bundle` は空になり、live next bundle は `cs_stdlib_bundle` に進む。
- 2026-03-12: `P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-03-A8` として `json_extended.py` / `pathlib_extended.py` / `enum_extended.py` / `argparse_extended.py` / `pytra_std_import_math.py` / `re_extended.py` の representative smoke を `cs` backend に追加し、C# stdlib residual をすべて `transpile_smoke` へ引き上げた。これで representative residual inventory は空になり、live next backend は `None` になった。
- 2026-03-12: `S3-01` として representative parity matrix / contract / active TODO wording を final rollout state に同期し、active plan 側の closeout sync を完了した。残りは archive handoff のみ。
