<a href="../../../en/plans/archive/20260312-p1-relative-import-longtail-bundle.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: relative import long-tail bundle rollout

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/archive/20260312.md` の `ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01`

背景:
- second-wave rollout の archive 後、`lua/php/ruby` が relative import の残 long-tail backend として残った。
- representative relative import project については backend-native emitter が明示的に reject する current contract を先に固定し、coverage inventory では `fail_closed_locked + backend_native_fail_closed` baseline を持つ形にした。
- current live handoff は long-tail support rollout へ進み、この archived bundle は fail-closed baseline / follow-up handoff の履歴として残す。

目的:
- `lua/php/ruby` の archived long-tail fail-closed baseline を representative contract として固定する。
- backend coverage / second-wave handoff / backend parity docs から次の support rollout へ渡せる archived bundle handoff を残す。

対象:
- representative fail-closed regression と archived bundle contract の固定
- backend coverage / second-wave handoff / backend parity docs の long-tail baseline 同期
- active follow-up を `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01` へ渡す handoff 固定

非対象:
- Lua / PHP / Ruby backend の relative import support 実装
- relative import semantics 自体の変更
- support claim の追加

受け入れ基準:
- archived bundle contract は `lua/php/ruby` を `fail_closed_locked + backend_native_fail_closed` baseline として固定する。
- backend parity docs / coverage inventory は archived long-tail baseline と active support rollout handoff を同時に記録する。
- archived bundle contract checker と関連 unit test が通る。

確認コマンド:
- `python3 tools/check/check_relative_import_backend_coverage.py`
- `python3 tools/check/check_relative_import_longtail_bundle_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_longtail_bundle_contract.py'`
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`

決定ログ:
- 2026-03-12: `lua/php/ruby` は representative relative import project を backend-native emitter が明示的に reject する current contract を先に固定し、`fail_closed_locked + backend_native_fail_closed` baseline を archived bundle として残す。
- 2026-03-12: active follow-up は `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01` / `longtail_relative_import_support_rollout` に切り替え、archived bundle は current baseline と handoff の履歴だけを持つ。

## 分解

- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01] `lua/php/ruby` long-tail bundle の live handoff と representative contract を固定した。
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S1-01] live plan / TODO / contract / checker を追加し、coverage / second-wave handoff / backend parity docs を long-tail bundle へ切り替えた。
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S2-01] `lua/php/ruby` の representative fail-closed regression を追加し、current non-support contract を固定した。
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S2-02] representative transpile smoke を widen する代わりに、fail-closed canonical end state を明文化して close-ready にした。
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S3-01] docs / tests / handoff wording を current long-tail state に揃えて task を閉じた。
