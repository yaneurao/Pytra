# P0: sample/18 `enumerate(lines)` の direct typed unpack 化

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01`

背景:
- 現在の `sample/18` 生成 C++ では `for (object __itobj ... )` + `py_at(__itobj, i)` の中継が残る経路がある。
- `enumerate(lines)` は `tuple<int64, str>` が静的に分かるため、直接 unpack へ落とせる。

目的:
- `enumerate(lines)` を direct typed loop（`const auto& [idx, source]`）へ統一し、`object` 中継を排除する。

対象:
- `src/hooks/cpp/emitter/stmt.py`
- `src/hooks/cpp/emitter/expr.py`（必要時）
- `test/unit/test_east3_cpp_bridge.py`
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/18_mini_language_interpreter.cpp`

非対象:
- enumerate runtime の全型対応拡張（sample/18 優先）
- EAST3 IR 仕様の全面変更

受け入れ基準:
- sample/18 の `tokenize` ループが `object` 反復 + `py_at` を使わない。
- `line_index/source` が loop header で direct unpack される。
- unit/transpile check が非退行で通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

決定ログ:
- 2026-03-01: sample/18 追加最適化として `enumerate(lines)` direct unpack 固定を P0 で起票。
- 2026-03-01: `ForCore` typed enumerate 復元で、typed `list[str]` パラメータ名は `py_enumerate(lines)` を優先し、`object __itobj` + `py_at` 経路へ後退しない条件を固定した。
- 2026-03-01: `test_py2cpp_codegen_issues.py` の sample/18 回帰を `for (const auto& [line_index, source] : py_enumerate(lines))` 期待へ更新し、`object __itobj` と `py_at(__itobj, ...)` 非出力を固定した。
- 2026-03-01: `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`（80件）と `python3 tools/check_py2cpp_transpile.py`（`checked=134 ok=134 fail=0 skipped=6`）で非退行を確認した。

## 分解

- [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01] `enumerate(lines)` を object 中継なしの direct typed unpack へ統一する。
- [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01-S1-01] `For` lower の適用条件（iterable/list/tuple 型既知）を整理し、適用外は fail-closed に固定する。
- [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01-S2-01] `for` header 出力を direct structured binding 優先へ更新する。
- [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01-S2-02] sample/18 回帰を追加し、`object __itobj` + `py_at` 非出力を固定する。
- [x] [ID: P0-CPP-S18-ENUM-DIRECT-TYPED-01-S3-01] transpile/unit/sample 再生成で非退行を確認する。
