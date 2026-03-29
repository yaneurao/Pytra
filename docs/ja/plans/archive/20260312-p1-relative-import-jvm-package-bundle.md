<a href="../../../en/plans/archive/20260312-p1-relative-import-jvm-package-bundle.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: relative import JVM package bundle rollout

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01`

背景:
- second-wave rollout 順は `locked_js_ts_smoke_bundle -> native_path_bundle(go/nim/swift) -> jvm_package_bundle(java/kotlin/scala)` に固定済み。
- `go/nim/swift` native-path bundle は representative transpile smoke と fail-closed lane を固定済みで、current coverage では `transpile_smoke_locked` baseline に上がった。
- coverage inventory / second-wave rollout handoff / backend parity docs はまだ archived native-path bundle を next live task として参照しており、JVM package bundle への handoff が stale のまま残っている。

目的:
- `java/kotlin/scala` を next live rollout bundle として固定する。
- native-path bundle を archive semantics に切り替えつつ、JVM package bundle の live handoff を docs / tooling / contract に同期する。

対象:
- live plan / TODO / contract / checker の追加
- archived native-path bundle contract への切り替え
- second-wave rollout handoff / coverage inventory / backend parity docs の更新

非対象:
- Java / Kotlin / Scala backend の full support claim
- long-tail (`lua/php/ruby`) rollout 実装
- relative import semantics 自体の変更

受け入れ基準:
- next live handoff は archived native-path plan ではなくこの plan を参照する。
- `java/kotlin/scala` が `jvm_package_bundle_rollout` lane として contract / checker / docs に固定される。
- `go/nim/swift` は `transpile_smoke_locked` baseline に移り、native-path bundle contract は archive semantics を持つ。
- `lua/php/ruby` は `defer_until_jvm_package_bundle_complete` のまま維持される。

確認コマンド:
- `python3 tools/check/check_relative_import_backend_coverage.py`
- `python3 tools/check/check_relative_import_secondwave_rollout_contract.py`
- `python3 tools/check/check_relative_import_native_path_bundle_contract.py`
- `python3 tools/check/check_relative_import_jvm_package_bundle_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_secondwave_rollout_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_native_path_bundle_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_jvm_package_bundle_contract.py'`
- `PYTHONPATH=src:test/unit:tools/unittest/backends python3 -m unittest discover -s tools/unittest/emit/go -p 'test_py2go_smoke.py' -k relative_import_native_path_bundle -v`
- `PYTHONPATH=src:test/unit:tools/unittest/backends python3 -m unittest discover -s tools/unittest/emit/nim -p 'test_py2nim_smoke.py' -k relative_import_native_path_bundle -v`
- `PYTHONPATH=src:test/unit:tools/unittest/backends python3 -m unittest discover -s tools/unittest/emit/swift -p 'test_py2swift_smoke.py' -k relative_import_native_path_bundle -v`
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`

決定ログ:
- 2026-03-12: native-path bundle は representative smoke を lock した current baseline とみなし、archive semantics に切り替えたうえで JVM package bundle を next live rollout に昇格する。
- 2026-03-12: current non-C++ rollout handoff は `rs/cs/go/js/nim/swift/ts=transpile_smoke_locked`、`java/kotlin/scala=jvm_package_bundle_rollout`、`lua/php/ruby=defer_until_jvm_package_bundle_complete` で固定する。
- 2026-03-12: `P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S1-01` は live plan / TODO / contract / checker / docs handoff を切り替える closeout-first bundle とし、backend smoke の追加は後続 bundle に分ける。
- 2026-03-12: `P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-01` では `java/kotlin/scala` の representative package-style transpile smoke を固定し、wildcard relative import は backend-native emitter で fail-closed にする。
- 2026-03-12: `P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-02` で coverage inventory を current smoke state に同期し、`java/kotlin/scala` は `transpile_smoke_locked` evidence を持ちながらも active `jvm_package_bundle_rollout` として long-tail handoff を保持する、と整理した。
- 2026-03-12: `P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-02` の evidence lane は `java/kotlin/scala=package_project_transpile`、`go/nim/swift=native_emitter_function_body_transpile` として backend parity docs まで固定し、followup long-tail lane は `longtail_relative_import_rollout / defer_until_jvm_package_bundle_complete` に揃えた。
- 2026-03-12: `P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S3-01` では JVM bundle contract checker を current smoke-locked coverage / long-tail handoff snapshot と接続し、focused docs / tests / handoff wording を揃えて parent task を close した。

## 分解

- [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01] `java/kotlin/scala` の JVM package bundle を next live rollout として固定し、native-path closeout 後の handoff を整える。
- [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S1-01] native-path bundle を archive semantics に切り替え、JVM package bundle の live plan / TODO / contract / checker / docs handoff を追加する。
- [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-01] `java/kotlin/scala` の representative transpile smoke / fail-closed regression を追加する。
- [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S2-02] backend parity docs / coverage inventory / handoff wording を current JVM bundle state に同期して close-ready にする。
- [x] [ID: P1-RELATIVE-IMPORT-JVM-PACKAGE-BUNDLE-01-S3-01] focused docs / tests / handoff wording を current smoke-locked state に揃え、JVM package bundle task を閉じる。
