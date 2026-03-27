<a href="../../../en/plans/archive/20260312-p1-relative-import-secondwave-planning.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: relative import second-wave rollout planning

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01`

背景:
- relative import の current verification coverage は `cpp=build_run_locked`, `rs/cs=transpile_smoke_locked`, その他 non-C++ は `not_locked` まで固定済み。
- first-wave `rs/cs` smoke task は archive へ移ったが、coverage inventory / backend parity docs が参照する `second_wave_rollout_planning` にはまだ live plan がない。
- Pytra-NES 型 project layout を他 backend へ広げる前に、second-wave backend 集合・順序・representative scenario・fail-closed baseline を live contract として固定する必要がある。

目的:
- second-wave relative import rollout の canonical live plan を用意する。
- second-wave backend 集合、representative scenario、verification lane、fail-closed baseline を tooling contract と docs handoff に固定する。

対象:
- second-wave rollout planning contract の追加
- coverage inventory / backend parity docs の handoff 更新
- TODO / plan / checker / unit test の追加

非対象:
- second-wave backend 実装そのもの
- relative import semantics の変更
- support claim の更新

受け入れ基準:
- second-wave backend order が live contract / checker / docs に固定されている。
- representative scenario が `parent_module_alias` / `parent_symbol_alias` に固定されている。
- coverage inventory / backend parity docs の handoff が archive 済み first-wave plan ではなく、この live plan を参照する。

確認コマンド:
- `python3 tools/check_relative_import_secondwave_rollout_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_secondwave_rollout_contract.py'`
- `python3 tools/check_relative_import_backend_coverage.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `python3 tools/check_todo_priority.py`
- `git diff --check`

決定ログ:
- 2026-03-12: first-wave `rs/cs` smoke task を archive へ移した直後に、next handoff を切らさないよう second-wave planning を live 化する。
- 2026-03-12: second wave backend は `go/java/js/kotlin/nim/scala/swift/ts`、representative scenario は `parent_module_alias` / `parent_symbol_alias` に固定し、lane は `second_wave_rollout_planning`、fail-closed は `backend_specific_fail_closed` を維持する。
- 2026-03-12: second-wave rollout は backend group bundle として `locked_js_ts_smoke_bundle -> native_path_bundle(go/nim/swift) -> jvm_package_bundle(java/kotlin/scala)` の順に固定する。relative import の current path-root semantics に最も近い native/path-oriented target を next rollout bundle とし、JVM package bundle は follow-up に回す。
- 2026-03-12: `S3-01` では coverage inventory handoff と backend parity docs に bundle order / next bundle / follow-up bundle を同期し、task を close-ready にする。

## 分解

- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01] second-wave relative import rollout の live contract / docs handoff / verification lane を固定する。
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01-S1-01] live plan / TODO と second-wave rollout contract / checker / docs handoff を追加する。
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01-S2-01] second-wave backend ごとの representative smoke / fail-closed 導入順を backend group 単位の bundle に落とす。
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01-S3-01] coverage docs / support wording / archive handoff を second-wave current state に同期して task を閉じる。
