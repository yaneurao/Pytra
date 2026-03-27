<a href="../../en/plans/p0-cpp-s13-tuple-construction-slimming.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: sample/13 C++ tuple 構築の冗長ラップ削減

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01`

背景:
- `sample/cpp/13_maze_generation_steps.cpp` では、
  `::std::tuple<...>(::std::make_tuple(...))` の二重ラップが残っている。
- この形は意味的には冗長で、`::std::make_tuple(...)` または `emplace_back(...)` へ縮退できる。
- 出力可読性と行長の悪化要因になっている。

目的:
- tuple 値を生成する C++ 出力で二重ラップを削減し、最短で等価な表現へ統一する。
- sample/13 の `candidates.append(...)` / `stack.append(...)` など頻出箇所を対象にする。

対象:
- `src/hooks/cpp/emitter/collection_expr.py`
- `src/hooks/cpp/emitter/stmt.py`
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/13_maze_generation_steps.cpp`（再生成確認）

非対象:
- tuple unpack の構造化束縛化（別タスク）
- EAST3 の型推論アルゴリズム変更
- 他 backend の tuple 表現変更

受け入れ基準:
- `::std::tuple<T...>(::std::make_tuple(...))` が再出力されない。
- 等価な最短表現（`::std::make_tuple(...)` または `emplace_back(...)`）へ統一される。
- `check_py2cpp_transpile.py` と関連 unit テストが通る。
- `sample/cpp/13` 再生成で対象断片の冗長ラップ削減を確認できる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --stems 13_maze_generation_steps --force`

決定ログ:
- 2026-03-02: ユーザー指示により、sample/13 の tuple 二重ラップ削減を P0 として起票。
- 2026-03-02: `list<tuple[...]>.append(...)` で引数が `::std::make_tuple(...)` の場合は追加 cast を省略し、`::std::tuple<...>(::std::make_tuple(...))` 二重ラップを回避する経路を `src/hooks/cpp/emitter/call.py` へ追加した。
- 2026-03-02: `test_py2cpp_codegen_issues.py` の sample/13 回帰に `tuple(make_tuple)` 非出力断片を追加し、再発検知を固定した。
- 2026-03-02: `python3 tools/regenerate_samples.py --langs cpp --stems 13_maze_generation_steps --force` / `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` / `python3 tools/check_py2cpp_transpile.py` を実行し、すべて通過を確認した。

## 分解

- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S1-01] sample/13 の tuple 二重ラップ発生箇所を棚卸しし、適用境界を固定する。
- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S1-02] `make_tuple` 直接化と `append/emplace` の適用優先ルールを定義する。
- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S2-01] CppEmitter の tuple 構築出力を更新し、二重ラップを除去する。
- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S2-02] `append` 系で `emplace_back` 可能な経路を追加し、余分な一時構築を削減する。
- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S2-03] 適用不可ケースの fallback を固定し、現行意味を維持する。
- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S3-01] unit テストを追加し、二重ラップ再発を検知可能にする。
- [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S3-02] `sample/cpp/13` 再生成と transpile チェックで非退行を確認する。
