# P1: relative import first-wave transpile smoke

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01`

背景:
- relative import の current coverage baseline は `cpp=build_run_locked` まで固定済みで、non-C++ rollout 順も `rs/cs` first wave として整理済み。
- 実装自体は `rs/cs` でも既に通るが、representative backend smoke と coverage inventory が未固定のままだと support-claim なしの verified lane として扱えない。
- Pytra-NES 型の project layout を他 target に広げる前に、first wave backend だけでも canonical transpile smoke を lock する必要がある。

目的:
- `rs/cs` の relative import representative transpile smoke を固定する。
- coverage inventory / backend parity docs / next rollout handoff を `rs/cs=transpile_smoke_locked` 前提に更新する。

対象:
- Rust/C# backend smoke に relative import representative case を追加
- relative import coverage inventory / checker / docs handoff の更新
- second-wave planning への handoff 明記

非対象:
- Rust/C# の build/run support claim 追加
- second-wave backend の実装
- relative import semantics 自体の変更

受け入れ基準:
- `rs` と `cs` に relative import representative transpile smoke がある。
- coverage inventory で `rs/cs=transpile_smoke_locked`、その他 non-C++ は `not_locked` のまま固定される。
- backend parity docs と handoff metadata が new baseline と一致する。

確認コマンド:
- `python3 tools/check_relative_import_backend_coverage.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s test/unit/backends/rs -p 'test_py2rs_smoke.py' -k relative_import`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s test/unit/backends/cs -p 'test_py2cs_smoke.py' -k relative_import`
- `python3 tools/build_selfhost.py`

決定ログ:
- 2026-03-12: TODO 空き後の次段として、archived `P2-RELATIVE-IMPORT-NONCPP-ROLLOUT-01` の first wave を actual smoke lock task として live 化した。
- 2026-03-12: `rs/cs` first-wave smoke は canonical scenario `parent_module_alias` と `parent_symbol_alias` をそのまま transpile し、coverage inventory を `transpile_smoke_locked` へ上げるが full support claim には使わない。

## 分解

- [x] [ID: P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01] `rs/cs` の relative import representative transpile smoke を lock し、coverage inventory / docs handoff を新 baseline に更新する。
- [x] [ID: P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01-S1-01] live plan / TODO を起票し、`rs/cs=transpile_smoke_locked` baseline と verification lane を固定する。
- [x] [ID: P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01-S2-01] `py2rs/py2cs` smoke に representative relative import transpile case を追加する。
- [x] [ID: P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01-S2-02] coverage inventory / backend parity docs / handoff metadata を `rs/cs=transpile_smoke_locked` へ同期する。
- [x] [ID: P1-RELATIVE-IMPORT-FIRSTWAVE-SMOKE-01-S3-01] docs / tests / inventory を current baseline に揃えて close-ready にする。
