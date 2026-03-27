<a href="../../../en/plans/archive/20260312-p1-relative-import-native-path-bundle.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: relative import native-path bundle rollout

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01`

背景:
- `locked_js_ts_smoke_bundle -> native_path_bundle(go/nim/swift) -> jvm_package_bundle(java/kotlin/scala)` という second-wave rollout 順は固定済み。
- coverage inventory / backend parity docs / second-wave rollout handoff は、次の live task として `go/nim/swift` をまとめた native-path bundle へ進める必要がある。
- Pytra-NES 型 layout に最も近い path-oriented backend から representative smoke / fail-closed policy を段階的に固定していくのが次段の焦点になる。

目的:
- `go/nim/swift` を native-path bundle として live handoff に昇格する。
- representative scenario、verification lane、follow-up JVM bundle との境界を docs / tooling / contract に固定する。

対象:
- native-path bundle の live plan / TODO / contract / checker / test 追加
- coverage inventory / second-wave rollout handoff / backend parity docs の handoff 更新
- `go/nim/swift` の representative rollout lane を `native_path_bundle_rollout` に固定

非対象:
- Go/Nim/Swift backend の full support claim
- JVM package bundle の rollout 実装
- relative import semantics 自体の変更

受け入れ基準:
- live handoff は old planning task ではなくこの plan を参照する。
- `go/nim/swift` が `native_path_bundle_rollout` lane として contract / checker / docs に固定される。
- `java/kotlin/scala` は follow-up bundle として `remaining_second_wave_rollout_planning` のまま維持される。

確認コマンド:
- `python3 tools/check_relative_import_backend_coverage.py`
- `python3 tools/check_relative_import_secondwave_rollout_contract.py`
- `python3 tools/check_relative_import_native_path_bundle_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_secondwave_rollout_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_native_path_bundle_contract.py'`
- `python3 tools/check_todo_priority.py`
- `git diff --check`

決定ログ:
- 2026-03-12: completed planning task は archive へ移し、next live handoff は `P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01` に切り替える。
- 2026-03-12: native-path bundle の representative backend は `go/nim/swift`、representative scenario は `parent_module_alias` / `parent_symbol_alias` に固定する。
- 2026-03-12: live verification lane は `native_path_bundle_rollout`、follow-up JVM bundle は `remaining_second_wave_rollout_planning` のまま維持する。
- 2026-03-12: `go/nim/swift` は CLI top-level `print(...)` ではなく function-body `return` lane を native emitter へ直接流す representative smoke で固定し、relative wildcard import は backend-specific fail-closed とする。
- 2026-03-12: coverage inventory では `go/nim/swift` を `transpile_smoke_locked` に上げるが、rollout handoff では active `native_path_bundle_rollout` のまま維持し、JVM bundle を follow-up に明示する。
- 2026-03-12: focused helper split と docs handoff wording を current state に同期し、JVM package bundle へ handoff できる状態で task を archive へ移す。

## 分解

- [x] [ID: P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01] `go/nim/swift` native-path bundle の live handoff と representative rollout contract を固定する。
- [x] [ID: P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01-S1-01] live plan / TODO / contract / checker を追加し、coverage handoff を native-path bundle へ切り替える。
- [x] [ID: P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01-S2-01] `go/nim/swift` native emitter の representative transpile smoke / fail-closed regression を追加する。
- [x] [ID: P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01-S2-02] backend parity docs / coverage inventory を native-path bundle current state に同期し、JVM follow-up handoff を明記する。
- [x] [ID: P1-RELATIVE-IMPORT-NATIVE-PATH-BUNDLE-01-S3-01] focused docs / tests / handoff wording を current state に揃えて task を閉じる。
