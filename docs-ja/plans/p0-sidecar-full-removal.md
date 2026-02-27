# P0: Go/Java/Swift/Kotlin sidecar 完全撤去

最終更新: 2026-02-27

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-SIDECAR-REMOVE-01`

背景:
- Go / Java / Swift / Kotlin backend の sidecar 互換経路は撤去済みで、native 単一路線へ統一済み。
- 最終回帰では `runtime_parity_check --targets go,java,swift,kotlin --all-samples` が `case_fail=7`（Go/Kotlin の compile/run failed）で未達。
- ユーザー要望として「この 7 ケースを順に潰す」ことが最優先で明示されたため、Go/Kotlin native 失敗の収束を最上位で実施する。

目的:
- Go / Java / Swift / Kotlin backend を native 単一路線に統一し、sidecar 実装と運用導線を完全に撤去する。

対象:
- `src/py2go.py` / `src/py2java.py` / `src/py2swift.py` / `src/py2kotlin.py`
- `src/hooks/{go,java,swift,kotlin}/emitter/` の sidecar 依存経路
- `tools/check_py2*_transpile.py` / `tools/runtime_parity_check.py` / 関連 test
- `sample/go` / `sample/java` / `sample/swift` / `sample/kotlin`
- `docs-ja/how-to-use.md` / `docs-ja/spec/spec-import.md` / 関連 spec と `docs/` 翻訳

非対象:
- Ruby / PHP backend 追加（別タスク）
- C++ / Rust / C# / JS / TS backend の設計変更
- EAST3 optimizer / CppOptimizer の新規最適化導入

受け入れ基準:
- 4言語 CLI から `--*-backend sidecar` が削除され、sidecar 分岐へ到達不能である。
- `sample/{go,java,swift,kotlin}` に `.js` sidecar が生成されない。
- 4言語の transpile/smoke/parity 回帰が native 単一路線で通る。
- `docs-ja` / `docs` から sidecar 手順・互換モード記述が撤去される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets go,java,swift,kotlin --all-samples --ignore-unstable-stdout`
- `find sample/go sample/java sample/swift sample/kotlin -name '*.js'`

決定ログ:
- 2026-02-27: ユーザー指示により、Go/Java/Swift/Kotlin sidecar 互換経路を完全撤去し、最優先（P0）で実施する方針を確定した。
- 2026-02-27: [ID: `P0-SIDECAR-REMOVE-01-S1-01`] `py2go.py` / `py2java.py` / `py2swift.py` / `py2kotlin.py` から `--*-backend sidecar` 引数・sidecar 分岐・`.js` 出力経路を削除し、native 単一路線へ統一した。
- 2026-02-27: [ID: `P0-SIDECAR-REMOVE-01-S1-02`] sidecar emitter 実装（`src/hooks/{go,java,swift,kotlin}/emitter/*_emitter.py`）を削除し、`hooks/*/emitter/__init__.py` は native 実装へ委譲する互換 API だけを残す構成へ整理した。
- 2026-02-27: [ID: `P0-SIDECAR-REMOVE-01-S2-01`] `test_py2{go,java,swift,kotlin}_smoke.py` の sidecar 前提ケースを native 前提へ置換し、`runtime_parity_check.py` / `check_gsk_native_regression.py` から sidecar 引数を削除。`python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v`、`test_py2java_smoke.py`、`test_py2swift_smoke.py`、`test_py2kotlin_smoke.py`、`test_runtime_parity_check_cli.py` がすべて通過した。
- 2026-02-27: [ID: `P0-SIDECAR-REMOVE-01-S2-02`] `python3 tools/regenerate_samples.py --langs go,java,swift,kotlin --force` を実行し、`summary: total=72 skip=0 regen=72 fail=0` を確認。続けて `find sample/go sample/java sample/swift sample/kotlin -name '*.js' | wc -l` が `0` となることを確認した。
- 2026-02-27: [ID: `P0-SIDECAR-REMOVE-01-S3-01`] `docs-ja/how-to-use.md` / `docs-ja/spec/spec-import.md` / `docs-ja/spec/spec-gsk-native-backend.md` / `docs-ja/spec/spec-java-native-backend.md` の sidecar 記述を「撤去済み・native-only」へ更新した。
- 2026-02-27: [ID: `P0-SIDECAR-REMOVE-01-S3-02`] 英語版 `docs/how-to-use.md` / `docs/spec/spec-import.md` / `docs/spec/spec-gsk-native-backend.md` / `docs/spec/spec-java-native-backend.md` を同期し、日英で sidecar 記述の不整合を解消した。
- 2026-02-27: [ID: `P0-SIDECAR-REMOVE-01-S4-01`] 最終回帰を実行。`check_py2{go,java,swift,kotlin}_transpile.py` はすべて `checked=132 ok=132 fail=0 skipped=6` で通過し、`find sample/go sample/java sample/swift sample/kotlin -name '*.js' | wc -l` は `0` を確認。`runtime_parity_check.py --case-root sample --targets go,java,swift,kotlin --all-samples --ignore-unstable-stdout` は `case_pass=11 case_fail=7 (run_failed=13, toolchain_missing=18)` で失敗し、Go/Kotlin native 既存課題（型不整合・宣言衝突）を確認した。
- 2026-02-27: [ID: `P0-SIDECAR-REMOVE-01-S5-*`] ユーザー指示により、parity 失敗 7 ケース（Go: `10/13/14/15/16/18`, Kotlin: `10/12/13/14/15/16/18`）の逐次解消を最優先に設定した。

## 分解

- [x] [ID: P0-SIDECAR-REMOVE-01-S1-01] `py2go.py` / `py2java.py` / `py2swift.py` / `py2kotlin.py` から `--*-backend sidecar` と sidecar 分岐を削除する。
- [x] [ID: P0-SIDECAR-REMOVE-01-S1-02] sidecar 専用 emitter import / `transpile_to_js` / `write_js_runtime_shims` 依存を撤去し、未使用コードを整理する。
- [x] [ID: P0-SIDECAR-REMOVE-01-S2-01] transpile/smoke/check 導線（`test_py2*` / `check_py2*_transpile.py` / `runtime_parity_check.py`）から sidecar 指定経路を除去する。
- [x] [ID: P0-SIDECAR-REMOVE-01-S2-02] `sample/go` / `sample/java` / `sample/swift` / `sample/kotlin` を再生成し、`.js` sidecar 非生成を回帰条件として固定する。
- [x] [ID: P0-SIDECAR-REMOVE-01-S3-01] `docs-ja/how-to-use.md` / `docs-ja/spec/spec-import.md` / 関連 spec から sidecar 記述を撤去し、native 単一路線へ更新する。
- [x] [ID: P0-SIDECAR-REMOVE-01-S3-02] `docs/` 翻訳同期を反映し、日英で sidecar 記述の不整合を解消する。
- [x] [ID: P0-SIDECAR-REMOVE-01-S4-01] 最終回帰（4言語 transpile + parity + sample 検証）を完了し、完了条件を文脈へ記録する。
- [ ] [ID: P0-SIDECAR-REMOVE-01-S5-01] Go native parity 失敗 6 ケース（`10/13/14/15/16/18`）を順に修正し、`run_failed` を解消する。
- [ ] [ID: P0-SIDECAR-REMOVE-01-S5-02] Kotlin native parity 失敗 7 ケース（`10/12/13/14/15/16/18`）を順に修正し、`run_failed` を解消する。
- [ ] [ID: P0-SIDECAR-REMOVE-01-S5-03] `runtime_parity_check.py --targets go,java,swift,kotlin --all-samples` を再実行し、`case_fail=0` を確認して親 `P0-SIDECAR-REMOVE-01` を完了化する。
