<a href="../../../en/plans/archive/20260313-p6-backend-parity-longtail-rollout.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P6 Backend Parity Long-Tail Rollout

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01`

目的:
- long-tail tier (`js`, `ts`, `lua`, `rb`, `php`) の未対応 cell を、matrix/contract とは別の live implementation queue として維持する。

背景:
- long-tail tier は matrix 上では reviewed / fail-closed の conservative state が残っているが、active TODO に実装トラックが無い。
- representative / secondary 実装が終わった後に受け皿が無いと、matrix だけが残って rollout が止まる。

対象:
- long-tail backend の representative feature cell 実装。
- unsupported lane の fail-closed 維持と、supported lane への引き上げ。
- long-tail tier の matrix / docs / support wording 更新。

非対象:
- representative / secondary backend の parity completion。
- JS/TS/Lua/Ruby/PHP の全面 feature parity。
- parity matrix contract の再設計。

受け入れ基準:
- long-tail tier の backend order と implementation bundle が固定されている。
- unsupported lane は fail-closed のまま残し、supported lane だけ evidence 付きで引き上げる方針が明記されている。
- secondary tier 完了後にそのまま受け渡せる live plan になっている。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_backend_parity_matrix_contract.py`
- `python3 tools/check_backend_parity_longtail_rollout_inventory.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_parity_matrix_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_parity_longtail_rollout_inventory.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## 分解

- [x] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S1-01] long-tail tier の current residual cell と implementation bundle を固定する。
- [x] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S2-01] `js/ts` bundle の未対応 cell を representative evidence 付きで埋める。
- [x] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S2-02] `lua/rb/php` bundle の未対応 cell を representative evidence 付きで埋める。
- [x] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S3-01] long-tail tier の matrix / docs / support wording を current rollout state に同期して閉じる。

## 決定ログ

- 2026-03-12: long-tail tier は `js/ts` と `lua/rb/php` に bundle 分割し、既存 smoke がある lane から先に `supported` へ引き上げる。
- 2026-03-12: unsupported lane は silent fallback ではなく fail-closed のまま保ち、evidence を伴う lane だけ更新する。
- 2026-03-13: `S1-01` として `backend_parity_longtail_rollout_inventory.py` / checker / unit test を追加し、long-tail residual cell を matrix seed から固定した。bundle order は `js/ts` の first bundle と `lua/rb/php` の second bundle に確定し、`js` は tuple/lambda/comprehension/control/iter/std、`ts` はそこに `virtual_dispatch`、`lua/php` は軽量 syntax + enumerate + std、`rb` はさらに `for_range/range/zip` を持つ current snapshot を handoff manifest に反映した。
- 2026-03-13: `S2-01` として `js` emitter に `Swap` lowering を追加し、`js/ts` representative smoke で `tuple_destructure` を含む bundle 全体を確認した。matrix は `js` の tuple/lambda/comprehension/control/iter/std と `ts` の同 bundle + `virtual_dispatch` を `supported/transpile_smoke` へ昇格し、long-tail inventory handoff は `completed_backends = ("js", "ts")`, `next_backend = "lua"`, `next_bundle = "lua_rb_php_bundle"` に進めた。
- 2026-03-13: `S2-02` として `lua/rb/php` bundle を close した。`lua/rb/php` emitter に `Swap` lowering を追加し、Lua には lambda rendering と `enum/argparse/re` の runtime alias 補完も入れて representative smoke を通した。matrix は `lua/rb/php` の residual cell を `supported/transpile_smoke` へ引き上げ、long-tail residual inventory は empty、handoff は `completed_backends = ("js", "ts", "lua", "rb", "php")`, `next_backend = None`, `next_bundle = None` に縮退した。
- 2026-03-13: `S3-01` として long-tail tier の matrix table / inventory wording / TODO を close state に同期した。end state は long-tail residual inventory empty、`js/ts/lua/rb/php` の reviewed representative cell が `supported/transpile_smoke` に揃い、active queue からは archive 移管だけが残る。
