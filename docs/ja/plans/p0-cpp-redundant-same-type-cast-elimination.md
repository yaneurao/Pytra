# P0: C++ 同型 cast 除去と型推論前倒し（最優先）

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-SAMECAST-01`

背景:
- `sample/18` の C++ 生成コードに `str(ch).isdigit()` のような同型変換が残存し、可読性と最適化余地を悪化させている。
- 問題は `isdigit` 個別ではなく、`str` を含む同型 cast 全般で発生している。
- 現状は fail-closed のため defensive cast を多用しているが、型既知経路でも同じ経路を通るため冗長化している。

目的:
- C++ backend の cast 規約を「同型なら無変換」へ統一し、型既知経路では不要な `str(...)` / `py_to_*` を出力しない。
- あわせて型推論を前段で強化し、後段 emitter が `Any/object` へ落とさずに済む経路を増やす。

対象:
- `src/hooks/cpp/emitter/cpp_emitter.py`
- `src/hooks/cpp/emitter/expr.py`
- `src/hooks/cpp/emitter/type_bridge.py`
- `src/hooks/cpp/emitter/builtin_runtime.py`
- 必要なら `src/pytra/compiler/east_parts/core.py`（EAST3 型付与）
- `test/unit/test_py2cpp_smoke.py` / `test/unit/test_east3_cpp_bridge.py`
- `sample/cpp/18_mini_language_interpreter.cpp`

非対象:
- C++ backend 全体の大規模リライト
- EAST3 optimizer の新規最適化群追加（本件は cast 規約と型推論に限定）
- 他言語 backend への同時水平展開

受け入れ基準:
- `sample/18` の `isdigit/isalpha` 周辺で型既知 `str` に対する `str(...)` が消える。
- 型既知経路で同型 `py_to_string` / `py_to<int64>` / `py_to<float64>` が新規発生しない回帰テストを追加する。
- `check_py2cpp_transpile` と関連 unit/smoke が通る。
- `sample/cpp` 再生成後に `sample/18` の compile/run が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 18_mini_language_interpreter --ignore-unstable-stdout`

決定ログ:
- 2026-02-28: ユーザー指示により、`isdigit` 個別対応ではなく「str を含む同型 cast 全体の除去」を P0 で実施する方針を確定した。

## 分解

- [ ] [ID: P0-CPP-SAMECAST-01-S1-01] 同型 cast 除去規約（source/target が同型かつ非 Any/object/unknown の場合は無変換）を C++ emitter 共通方針として固定する。
- [ ] [ID: P0-CPP-SAMECAST-01-S1-02] `get_expr_type()` の `Subscript` 推論を拡張し、`Subscript(str, int) -> str` を確定できるようにする。
- [ ] [ID: P0-CPP-SAMECAST-01-S1-03] `StrCharClassOp` を含む文字列系 lowering を修正し、型既知 `str` では `str(...)` を挿入しない。
- [ ] [ID: P0-CPP-SAMECAST-01-S2-01] `apply_cast` / `Unbox` / builtin runtime 変換経路に同型 no-op 判定を導入し、`py_to_*` の冗長連鎖を抑止する。
- [ ] [ID: P0-CPP-SAMECAST-01-S2-02] 同型 cast 非出力の回帰テスト（fixture + `sample/18` 断片検証）を追加する。
- [ ] [ID: P0-CPP-SAMECAST-01-S3-01] `sample/cpp` を再生成し、`sample/18` の compile/run/parity を再確認して結果を文脈へ記録する。
