# P6 Backend Parity Long-Tail Rollout

最終更新: 2026-03-12

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
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_parity_matrix_contract.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## 分解

- [ ] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S1-01] long-tail tier の current residual cell と implementation bundle を固定する。
- [ ] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S2-01] `js/ts` bundle の未対応 cell を representative evidence 付きで埋める。
- [ ] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S2-02] `lua/rb/php` bundle の未対応 cell を representative evidence 付きで埋める。
- [ ] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S3-01] long-tail tier の matrix / docs / support wording を current rollout state に同期して閉じる。

## 決定ログ

- 2026-03-12: long-tail tier は `js/ts` と `lua/rb/php` に bundle 分割し、既存 smoke がある lane から先に `supported` へ引き上げる。
- 2026-03-12: unsupported lane は silent fallback ではなく fail-closed のまま保ち、evidence を伴う lane だけ更新する。
