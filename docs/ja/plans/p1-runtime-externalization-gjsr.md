# P1: Go/Java/Swift/Ruby runtime 外出し（inline helper 撤去）

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RUNTIME-EXT-01`

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
- 2026-02-28: `S1-01` として inline helper の棚卸しと runtime 正本 API 対応表を作成し、Go/Java は命名差吸収が主課題、Swift/Ruby は runtime 正本不足が主課題であることを固定した。
- 2026-02-28: `S2-01` として Go emitter から `func __pytra_*` inline 定義を撤去し、`src/runtime/go/pytra/py_runtime.go` に互換 helper を集約。`py2go.py` が出力先へ `py_runtime.go` を配置する運用へ切替え、`test_py2go_smoke.py` と `runtime_parity_check --targets go`（`sample/18`）で回帰確認した。

## S1-01 棚卸し結果（2026-02-28）

| 言語 | inline helper 出力箇所 | inline helper 規模 | runtime 正本 | 所見 |
| --- | --- | --- | --- | --- |
| Go | `src/hooks/go/emitter/go_native_emitter.py` `transpile_to_go_native` 内（`func __pytra_*` を直書き） | `32` 定義（`__pytra_truthy/int/float/str/len/get_index/set_index/slice/print/perf_counter` 等） | `src/runtime/go/pytra/py_runtime.go`（`pyBool/pyToInt/pyToFloat/pyToString/pyLen/pyGet/pySet/pySlice/pyPrint/pyPerfCounter` 等） | 意味対応は揃うが命名・シグネチャが不一致。emitter 側 call 名の切替と import 導線追加で外出し可能。 |
| Java | `src/hooks/java/emitter/java_native_emitter.py` `transpile_to_java_native` 内（`private static __pytra_*`） | `10` 定義（`__pytra_noop/int/len/str_isdigit/str_isalpha/str_slice/bytearray/dict_of/list_repeat/truthy`） | `src/runtime/java/pytra/built_in/PyRuntime.java`（`pyToLong/pyLen/pyIsDigit/pyIsAlpha/pySlice/pyBytearray/pyDict/pyList/pyBool` 等） | runtime 正本は充実。inline 側の `__pytra_*` 呼び出しを `PyRuntime.py*` へ集約する接着層が必要。 |
| Swift | `src/hooks/swift/emitter/swift_native_emitter.py` `_emit_runtime_helpers()` | `32` 定義（`__pytra_any_default/int/float/str/len/getIndex/setIndex/slice/print/perf_counter` 等） | `src/runtime/swift/pytra/py_runtime.swift`（`pytraRunEmbeddedNode` のみ） | native runtime API 正本が未整備。外出し前に Swift 用 `py*` API 群を runtime 側へ新設する必要あり。 |
| Ruby | `src/hooks/ruby/emitter/ruby_native_emitter.py` `_emit_runtime_helpers()` | `26` 定義（`__pytra_truthy/int/float/div/str/len/as_list/as_dict/get_index/set_index/slice/print/perf_counter` 等） | `src/runtime/ruby/` 未存在 | runtime 正本が未整備。外出し前に `src/runtime/ruby/pytra/` を新設して API を定義する必要あり。 |

### 対応表（最小必須 API）

| inline helper 意味 | Go runtime 正本 API | Java runtime 正本 API | Swift runtime 正本 | Ruby runtime 正本 |
| --- | --- | --- | --- | --- |
| truthy 判定 | `pyBool` | `pyBool` | `TBD (新設)` | `TBD (新設)` |
| 整数変換 | `pyToInt` / `pyToLong` | `pyToLong` | `TBD (新設)` | `TBD (新設)` |
| 浮動小数変換 | `pyToFloat` | `pyToFloat` | `TBD (新設)` | `TBD (新設)` |
| 文字列化 | `pyToString` | `pyToString` | `TBD (新設)` | `TBD (新設)` |
| 長さ取得 | `pyLen` | `pyLen` | `TBD (新設)` | `TBD (新設)` |
| 添字 read/write | `pyGet` / `pySet` | `pyGet` / `pySet` | `TBD (新設)` | `TBD (新設)` |
| slice | `pySlice` | `pySlice` | `TBD (新設)` | `TBD (新設)` |
| print | `pyPrint` | `pyPrint` | `TBD (新設)` | `TBD (新設)` |
| perf_counter | `pyPerfCounter` | `pyPerfCounter` | `TBD (新設)` | `TBD (新設)` |

## 分解

- [x] [ID: P1-RUNTIME-EXT-01-S1-01] 言語別 helper 出力一覧（inline）と runtime 正本 API の対応表を作成する。
- [x] [ID: P1-RUNTIME-EXT-01-S2-01] Go emitter から helper 本体出力を撤去し、`src/runtime/go/pytra` 側 API 呼び出しへ切替える。
- [ ] [ID: P1-RUNTIME-EXT-01-S2-02] Java emitter から helper 本体出力を撤去し、`src/runtime/java/pytra` 側 API 呼び出しへ切替える。
- [ ] [ID: P1-RUNTIME-EXT-01-S2-03] Swift native 用 runtime 実体を整備し、emitter の helper inline 出力を撤去する。
- [ ] [ID: P1-RUNTIME-EXT-01-S2-04] Ruby runtime 実体を新設し、`require_relative` 等で外部参照する方式へ切替える。
- [ ] [ID: P1-RUNTIME-EXT-01-S3-01] parity/smoke/sample 再生成導線を更新し、回帰確認を完了する。
