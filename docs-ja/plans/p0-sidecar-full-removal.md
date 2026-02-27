# P0: Go/Java/Swift/Kotlin sidecar 完全撤去

最終更新: 2026-02-27

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-SIDECAR-REMOVE-01`

背景:
- Go / Java / Swift / Kotlin backend は native 既定へ移行済みだが、CLI 上は `--*-backend sidecar` 互換経路が残っている。
- 現状は「既定で使わないが残っている」状態であり、分岐維持コストと仕様の曖昧さを継続的に生む。
- ユーザー要望として sidecar の完全撤去が明示されたため、互換経路を実装・ドキュメント・回帰導線から除去する。

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

## 分解

- [ ] [ID: P0-SIDECAR-REMOVE-01-S1-01] `py2go.py` / `py2java.py` / `py2swift.py` / `py2kotlin.py` から `--*-backend sidecar` と sidecar 分岐を削除する。
- [ ] [ID: P0-SIDECAR-REMOVE-01-S1-02] sidecar 専用 emitter import / `transpile_to_js` / `write_js_runtime_shims` 依存を撤去し、未使用コードを整理する。
- [ ] [ID: P0-SIDECAR-REMOVE-01-S2-01] transpile/smoke/check 導線（`test_py2*` / `check_py2*_transpile.py` / `runtime_parity_check.py`）から sidecar 指定経路を除去する。
- [ ] [ID: P0-SIDECAR-REMOVE-01-S2-02] `sample/go` / `sample/java` / `sample/swift` / `sample/kotlin` を再生成し、`.js` sidecar 非生成を回帰条件として固定する。
- [ ] [ID: P0-SIDECAR-REMOVE-01-S3-01] `docs-ja/how-to-use.md` / `docs-ja/spec/spec-import.md` / 関連 spec から sidecar 記述を撤去し、native 単一路線へ更新する。
- [ ] [ID: P0-SIDECAR-REMOVE-01-S3-02] `docs/` 翻訳同期を反映し、日英で sidecar 記述の不整合を解消する。
- [ ] [ID: P0-SIDECAR-REMOVE-01-S4-01] 最終回帰（4言語 transpile + parity + sample 検証）を完了し、完了条件を文脈へ記録する。
