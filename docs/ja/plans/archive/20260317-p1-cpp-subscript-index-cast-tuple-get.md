<a href="../../../en/plans/archive/20260317-p1-cpp-subscript-index-cast-tuple-get.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: C++ emitter subscript index cast 省略と tuple 定数 index `std::get<I>` 最適化

最終更新: 2026-03-17

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-CPP-SUBSCRIPT-IDX-OPT-01`

背景:
- C++ emitter は subscript（リスト添字・タプル要素）を出力する際、index 式を原則 `py_to<int64>(...)` でラップして出力する。
- しかし index 式の `resolved_type` がすでに `int64` と確定している場合、この変換は同型 cast（identity cast）であり不要なノイズになる。
- EAST3 `IdentityPyToElisionPass` は EAST3 レベルの `Unbox/CastOrRaise` 縮退を担うが、emitter が subscript index を生成する際にインラインで `py_to<int64>` を付加するパスは EAST3 縮退の対象外となっている。
- 同様に、タプル要素への定数 index アクセス（`t[0]`, `t[1]` 等）は現行 emitter が `py_at(t, 0)` のような汎用 subscript API を使って出力するが、index が compile-time 定数の場合は C++17 `std::get<I>(t)` への直接 emit が可読性・コンパイラ最適化の両面で有利である。

目的:
- emitter の subscript index 生成パスに `resolved_type` チェックを追加し、`int64` が確定している index では `py_to<int64>(...)` ラップを省略する。
- タプル定数 index アクセスを `std::get<I>(tup)` 直接 emit へ切り替え、汎用 `py_at` 経由の dynamic dispatch を縮退する。

対象:
- `src/backends/cpp/emitter/`（subscript index 生成箇所）
- EAST3 で確定型を付与できている tuple subscript 経路
- `tools/unittest/emit/cpp/test_east3_cpp_bridge.py`
- `tools/unittest/emit/cpp/test_py2cpp_codegen_issues.py`

非対象:
- `object`/`Any`/`unknown` 型の subscript index（安全変換を維持）
- タプル以外の subscript での `std::get` 化（list, dict 等は対象外）
- EAST3 `IdentityPyToElisionPass` 自体の拡張（emitter ガードで対応する方針）
- tuple 型推論アルゴリズムの全面改修

受け入れ基準:
- list subscript / dict subscript 等で index `resolved_type` が `int64` と確定している場合、生成 C++ から `py_to<int64>(...)` ラップが消える。
- `object`/`Any`/`unknown` 経路では従来通り `py_to<int64>(...)` を維持し、fail-closed を保つ。
- タプルの定数 index アクセス（`t[0]` 等）が `std::get<0>(t)` として出力される。
- 動的 index（変数 index や `Any/object` 境界）では fallback の `py_at` / `py_to` 経路を維持する。
- `check_py2cpp_transpile` と関連 unit が通り、非退行を確認する。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check/check_py2cpp_transpile.py`
- `python3 tools/build_selfhost.py`

## 分解

- [x] [ID: P1-CPP-SUBSCRIPT-IDX-OPT-01-S1-01] subscript index 生成パスの現状を棚卸しし、`py_to<int64>` が残る箇所と `resolved_type` 確定可否を分類する。
- [x] [ID: P1-CPP-SUBSCRIPT-IDX-OPT-01-S1-02] tuple 定数 index アクセスの現状を棚卸しし、`std::get<I>` 化の安全条件（index が整数 literal / tuple 要素型確定 / `Any` 非含有）を仕様化する。
- [x] [ID: P1-CPP-SUBSCRIPT-IDX-OPT-01-S2-01] emitter subscript index 生成パスに `resolved_type == int64` ガードを追加し、`py_to<int64>` ラップを省略する。
- [x] [ID: P1-CPP-SUBSCRIPT-IDX-OPT-01-S2-02] tuple 定数 index emitter を `std::get<I>` 直接 emit へ切り替え、fallback 経路を維持する。
- [x] [ID: P1-CPP-SUBSCRIPT-IDX-OPT-01-S3-01] unit テストを追加して適用境界（型確定 / `Any`/`object` fallback）を回帰固定し、transpile check で非退行を確認する。

決定ログ:
- 2026-03-17: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01 S2-03 作業中に、subscript index の `py_to<int64>(int64_expr)` が identity cast として残っているケースと tuple 定数 index が `std::get<I>` ではなく汎用 API 経由になっているケースを確認し、独立タスクとして P1 で起票。EAST3 の `IdentityPyToElisionPass` は EAST3 レベルの縮退を担うが、emitter インライン生成パスは別途 resolved_type チェックが必要。
- 2026-03-17: 実装完了。S1-01/S1-02 調査で `_render_subscript_expr` および `render_lvalue` 内の 4 箇所（lines 3855/3857/3864/3877 / 2709/2710）が無条件に `py_to<int64>` を付加していることを確認。S2-01 で `idx_as_int64 = idx if idx_ty == "int64" else f"py_to<int64>({idx})"` ガードを追加。S2-02 は tuple 定数 index の `::std::get<I>` emit が既存実装（line 3884）で正常動作することを確認（変更不要）。S3-01 で境界テスト 6 件追加、既存テスト 14 件更新、check_py2x_transpile（145/145）・build_selfhost ともに通過。cpp バージョン 0.576.0 → 0.577.0。
