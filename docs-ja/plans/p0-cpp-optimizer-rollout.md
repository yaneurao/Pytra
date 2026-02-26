# P0: C++ backend 後段最適化層（CppOptimizer）導入

最終更新: 2026-02-26

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-CPP-OPT-01`

背景:
- `CppEmitter` は責務縮退を進めているが、C++ backend 固有の最適化判断がなお混在しやすい。
- `spec-cpp-optimizer` で `CppOptimizer` と `CppEmitter` の責務境界を定義済みであり、実装側へ反映する必要がある。
- text 出力後最適化ではなく、構造化 IR 段での最適化へ寄せる方針を採る。

目的:
- `EAST3 -> C++ lowering` 後段に `CppOptimizer` を導入し、`CppEmitter` を「決定的な構文出力器」へ縮退する。

対象:
- `src/hooks/cpp/optimizer/`（新規）
- `src/py2cpp.py` および C++ backend 経路の optimizer 配線
- `src/hooks/cpp/emitter/`（最適化責務の移設対象）
- C++ 回帰テストと sample 計測導線

非対象:
- C++ runtime API 仕様変更
- C++ compiler (`g++/clang++`) の `-O*` 代替
- `.cpp` 文字列に対する正規表現ベース最適化

受け入れ基準:
- `CppOptimizer` が `O0/O1/O2` で制御可能で、pass 単位 on/off と dump/trace を提供する。
- v1 pass（dead temp/no-op cast/const condition/range-for shape）が実装される。
- `CppEmitter` 側の最適化分岐が減少し、責務境界を維持できる。
- C++ の transpile/parity 回帰が基線を維持する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2cpp_*.py'`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --all-samples --ignore-unstable-stdout`

決定ログ:
- 2026-02-26: 初版作成。`spec-cpp-optimizer` の責務境界を実装可能な S1/S2/S3 へ分解した。

## 分解

- [ ] [ID: P0-CPP-OPT-01-S1-01] `src/hooks/cpp/optimizer/` の骨格（optimizer/context/trace/passes）と no-op 配線を追加する。
- [ ] [ID: P0-CPP-OPT-01-S1-02] `py2cpp` 実行経路へ `CppOptimizer` 呼び出しを追加し、`--cpp-opt-level` / `--cpp-opt-pass` / dump オプションを配線する。
- [ ] [ID: P0-CPP-OPT-01-S2-01] `CppDeadTempPass` / `CppNoOpCastPass` を実装し、emitter 内の同等ロジックを移設する。
- [ ] [ID: P0-CPP-OPT-01-S2-02] `CppConstConditionPass` / `CppRangeForShapePass` を導入し、C++ 構文化前の IR 正規化を固定する。
- [ ] [ID: P0-CPP-OPT-01-S2-03] `CppRuntimeFastPathPass` を限定導入し、runtime 契約同値の範囲で最適化する。
- [ ] [ID: P0-CPP-OPT-01-S3-01] `CppEmitter` 側の最適化分岐を削減し、責務境界を `spec-cpp-optimizer` に合わせて整理する。
- [ ] [ID: P0-CPP-OPT-01-S3-02] C++ 回帰（`test_py2cpp_*` / `check_py2cpp_transpile.py` / `runtime_parity_check --targets cpp`）を固定する。
- [ ] [ID: P0-CPP-OPT-01-S3-03] 速度/サイズ/生成差分のベースラインを計測し、導入効果を文脈ファイルへ記録する。
