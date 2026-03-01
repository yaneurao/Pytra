# P0: sample/18 benchmark ソース構築の typed list 化（`object + py_append` 縮退）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S18-BENCH-TYPED-LIST-01`

背景:
- sample/18 の `build_benchmark_source` / `run_demo` / `run_benchmark` では `object` list と `py_append` が残り、可読性と実行効率を下げている。
- ここは `list[str]` が成立するため、typed list へ寄せられる。

目的:
- benchmark ソース構築を typed list（`list<str>`）中心へ移行し、`object` boxing と append helper 依存を削減する。

対象:
- `src/hooks/cpp/emitter/*`（list 初期化/append/return 型整合）
- `test/unit/test_east3_cpp_bridge.py`
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/18_mini_language_interpreter.cpp`

非対象:
- benchmark シナリオのロジック変更
- 他 sample の全面一括最適化

受け入れ基準:
- sample/18 の `build_benchmark_source` で `object lines = make_object(list<object>{})` が出力されない。
- `run_demo`/`run_benchmark` 側も `list[str]` 整合で接続され、追加の `object` 再変換がない。
- transpile/unit/parity で非退行を確認する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 18_mini_language_interpreter --ignore-unstable-stdout`

決定ログ:
- 2026-03-01: sample/18 追加最適化として benchmark ソース構築の typed list 化を P0 で起票。
- 2026-03-01: `list[str]` value-model トラッキング（関数 return / AnnAssign local / call coercion）を追加し、`build_benchmark_source`/`run_demo`/`run_benchmark` の `object + py_append + py_to_str_list_from_object` を除去した。`test_east3_cpp_bridge`（90件）・`test_py2cpp_codegen_issues`（83件）・`check_py2cpp_transpile`（134/134）・sample/18 parity（cpp）を通過。

## 分解

- [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01] `build_benchmark_source` と下流呼び出しを typed list へ寄せ、`object + py_append` を縮退する。
- [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01-S1-01] `build_benchmark_source` から `tokenize`/`parse_program` までの型境界を棚卸しし、`list[str]` 維持条件を固定する。
- [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01-S2-01] emitter を更新し、list 初期化/append/return を typed 経路で出力する。
- [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01-S2-02] sample/18 回帰を追加し、`object lines` と `py_append(lines, ...)` の再発を防止する。
- [x] [ID: P0-CPP-S18-BENCH-TYPED-LIST-01-S3-01] transpile/unit/parity を再実行し、非退行を確認する。
