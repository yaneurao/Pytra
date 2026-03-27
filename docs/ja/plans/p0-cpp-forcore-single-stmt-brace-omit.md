<a href="../../en/plans/p0-cpp-forcore-single-stmt-brace-omit.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `ForCore` 単文ループで不要な波括弧を省略する

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-FORCORE-BRACE-OMIT-01`

背景:
- 現行 C++ emitter は `ForCore` 出力で、本文が単文でも波括弧 `{}` を維持するケースがある。
- `sample/cpp/18_mini_language_interpreter.cpp` の `build_benchmark_source` でも、単文 `lines.append(...)` ループが `{}` 付きで出力される。
- `For`/`ForRange` には単文時 brace 省略判定がある一方、`ForCore` は既定判定に含まれていない。

目的:
- `ForCore` でも既存 `For`/`ForRange` と同等の省略条件を適用し、単文ループの不要な `{}` を削減する。
- 可読性向上のみを狙い、意味（実行結果・スコープ・最適化結果）は変えない。

対象:
- `src/hooks/cpp/emitter/cpp_emitter.py`（brace 省略既定判定）
- `src/hooks/cpp/emitter/stmt.py`（`ForCore` 出力経路）
- `test/unit/test_py2cpp_codegen_issues.py`（回帰）
- `sample/cpp/18_mini_language_interpreter.cpp`（再生成差分確認）

非対象:
- `If` / `For` / `ForRange` の既存 brace 方針変更
- 他 backend（Rust/Go/Scala など）の brace 方針変更
- EAST3 optimizer / lowering の仕様変更

受け入れ基準:
- `ForCore` 単文ループで省略可能条件を満たす場合、`for (...) stmt;` 形式で出力される。
- 複文・tuple unpack・capture rewrite など既存の安全条件では従来どおり `{}` を維持する。
- `check_py2cpp_transpile.py` と該当 unit テストが通る。
- `sample/cpp/18_mini_language_interpreter.cpp` の単文ループ（`lines.append(...)`）で `{}` 省略が確認できる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --stems 18_mini_language_interpreter --force`

決定ログ:
- 2026-03-02: ユーザー指示により、`ForCore` 単文ループの `{}` 省略を `CppEmitter` 側で扱う方針で `P0` 起票。
- 2026-03-02: 省略条件は fail-closed とし、`StaticRangeForPlan + NameTarget + orelseなし + 単文` に限定する方針で確定。
- 2026-03-02: `CppEmitter._default_stmt_omit_braces` に `ForCore` 分岐を追加し、上記条件を満たすときのみ brace 省略を有効化。
- 2026-03-02: `test_forcore_static_range_single_stmt_omits_braces` を追加し、`sample/cpp/18` 再生成と `check_py2cpp_transpile` を通過。

## 分解

- [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S1-01] `ForCore` の brace 省略条件（単文・安全条件・除外条件）を確定する。
- [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S2-01] `CppEmitter` の既定 brace 判定に `ForCore` を追加し、出力経路へ適用する。
- [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S3-01] unit テストを追加/更新し、`ForCore` 省略回帰を固定する。
- [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S3-02] `sample/cpp/18` 再生成と transpile チェックで非退行を確認する。
