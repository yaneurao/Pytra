# P1: relative import second-wave transpile smoke

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01`

背景:
- relative import の current coverage baseline は `cpp=build_run_locked`、`rs/cs=transpile_smoke_locked` まで固定済み。
- second wave backend (`go/java/js/kotlin/nim/scala/swift/ts`) は rollout order だけ決まっており、representative transpile smoke はまだ lock されていない。
- Pytra-NES のような package layout を non-C++ へ広げるには、まず single-output transpile が安定している backend から smoke を増やす必要がある。

目的:
- `js/ts` を second-wave の representative backend として live contract に固定する。
- representative relative import transpile smoke を追加し、coverage inventory / backend parity docs の baseline を更新する。

対象:
- second-wave representative smoke contract (`js/ts`) の追加
- JS / TS backend smoke suite への relative import representative case 追加
- coverage inventory / checker / backend parity docs / handoff metadata の更新

非対象:
- `go/java/kotlin/nim/scala/swift` の smoke 追加
- build/run support claim の追加
- relative import semantics 自体の変更

受け入れ基準:
- `js` と `ts` に representative relative import transpile smoke がある。
- coverage inventory で `js/ts=transpile_smoke_locked`、残る second-wave / long-tail backend は `not_locked` のまま固定される。
- backend parity docs と handoff metadata が `js/ts` baseline へ同期する。

確認コマンド:
- `python3 tools/check_relative_import_secondwave_smoke_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_secondwave_smoke_contract.py'`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s test/unit/backends/js -p 'test_py2js_smoke.py' -k relative_import`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s test/unit/backends/ts -p 'test_py2ts_smoke.py' -k relative_import`
- `python3 tools/check_relative_import_backend_coverage.py`
- `python3 tools/build_selfhost.py`

決定ログ:
- 2026-03-12: TODO が空になったので、relative import の next live task として second-wave representative smoke を起票した。
- 2026-03-12: second-wave の最初の representative backend は `js/ts` に固定する。実際に `parent_module_alias` / `parent_symbol_alias` が単体 transpile できることを確認済みで、single-output smoke を lock しやすい。
- 2026-03-12: second-wave smoke contract は `relative_import_secondwave_smoke_contract.py` / checker / tooling test を正本とし、`S1-01` はその live contract の formal close として扱う。
- 2026-03-12: `py2js` smoke は shared helper 経由で second-wave contract に追従させ、scenario ごとの expected needle を共通化する。
- 2026-03-12: `py2ts` smoke も同じ shared helper へ揃え、`js/ts` の representative transpile smoke shape を一致させる。

## 分解

- [ ] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01] `js/ts` の relative import representative transpile smoke を lock し、coverage inventory / docs handoff を次 baseline に更新する。
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S1-01] live plan / TODO と `js/ts` second-wave smoke contract を固定する。
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S2-01] `py2js` smoke に representative relative import transpile case を追加する。
- [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S2-02] `py2ts` smoke に representative relative import transpile case を追加する。
- [ ] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S3-01] coverage inventory / backend parity docs / handoff metadata を `js/ts` baseline へ同期して close-ready にする。
