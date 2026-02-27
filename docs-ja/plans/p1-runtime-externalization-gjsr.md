# P1: Go/Java/Swift/Ruby runtime 外出し（inline helper 撤去）

最終更新: 2026-02-27

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P1-RUNTIME-EXT-01`

背景:
- `sample/go`, `sample/java`, `sample/swift`, `sample/ruby` の生成コード先頭に `__pytra_truthy` など runtime helper 本体が inline 展開されている。
- inline 展開は「単一生成ファイルで実行できる」利点がある一方、生成コード肥大化・runtime 実装の重複・runtime 差し替え難化を招く。
- Go/Java には `src/runtime/<lang>/pytra` 配下に runtime 実体があるが、現行 native emitter と実行導線が接続されていない。
- Swift は `src/runtime/swift/pytra/py_runtime.swift` が sidecar 時代の Node helper 実装であり、native 用 runtime API の正本が未整備。
- Ruby は runtime helper を生成物へ埋め込む設計で開始しており、外部 runtime ファイルをまだ持たない。

目的:
- Go/Java/Swift/Ruby の native 生成コードから inline helper 定義を撤去し、runtime を別ファイル参照に統一する。
- runtime 実装の正本を `src/runtime/<lang>/pytra/` 配下へ集約し、生成コードは API 呼び出しのみにする。

対象:
- `src/hooks/go/emitter/go_native_emitter.py`
- `src/hooks/java/emitter/java_native_emitter.py`
- `src/hooks/swift/emitter/swift_native_emitter.py`
- `src/hooks/ruby/emitter/ruby_native_emitter.py`
- `src/runtime/go/pytra/*`, `src/runtime/java/pytra/*`, `src/runtime/swift/pytra/*`, `src/runtime/ruby/pytra/*`
- `tools/runtime_parity_check.py`, `tools/regenerate_samples.py`, `test/unit/test_py2{go,java,swift,rb}_smoke.py`

非対象:
- C++/Rust/C#/JS/TS backend の runtime 方式変更
- runtime API の意味仕様そのものの全面再設計
- 全言語 selfhost 完全化（別タスク）

受け入れ基準:
- `py2go` / `py2java` / `py2swift` / `py2rb` の生成コードに `__pytra_truthy` など helper 本体が inline 出力されない。
- 各言語のビルド/実行導線は runtime ファイルを外部参照して通る（import/link/include のいずれか）。
- `runtime_parity_check` の対象ケースで既存 pass 範囲に対して非退行を確認できる。
- `sample/{go,java,swift,ruby}` 再生成後も実行導線が破綻しない。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2go_smoke.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2java_smoke.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2swift_smoke.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets go,java,swift,ruby --all-samples --ignore-unstable-stdout`
- `python3 tools/regenerate_samples.py --langs go,java,swift,ruby --force`

決定ログ:
- 2026-02-27: ユーザー要望により「Go/Java/Swift/Ruby の inline runtime helper を埋め込まない」方針を `P1-RUNTIME-EXT-01` として起票した。

## 分解

- [ ] [ID: P1-RUNTIME-EXT-01-S1-01] 言語別 helper 出力一覧（inline）と runtime 正本 API の対応表を作成する。
- [ ] [ID: P1-RUNTIME-EXT-01-S2-01] Go emitter から helper 本体出力を撤去し、`src/runtime/go/pytra` 側 API 呼び出しへ切替える。
- [ ] [ID: P1-RUNTIME-EXT-01-S2-02] Java emitter から helper 本体出力を撤去し、`src/runtime/java/pytra` 側 API 呼び出しへ切替える。
- [ ] [ID: P1-RUNTIME-EXT-01-S2-03] Swift native 用 runtime 実体を整備し、emitter の helper inline 出力を撤去する。
- [ ] [ID: P1-RUNTIME-EXT-01-S2-04] Ruby runtime 実体を新設し、`require_relative` 等で外部参照する方式へ切替える。
- [ ] [ID: P1-RUNTIME-EXT-01-S3-01] parity/smoke/sample 再生成導線を更新し、回帰確認を完了する。
