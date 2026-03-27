<a href="../../en/plans/p0-cpp-s13-grid-init-iife-reduction.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: sample/13 C++ grid 初期化 IIFE 縮退

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S13-GRID-IIFE-REDUCE-01`

背景:
- `sample/cpp/13_maze_generation_steps.cpp` では、2 次元 `grid` 初期化で
  `([&]() { ... return tmp; })()` 形式の IIFE が生成され、コード量と可読性を悪化させている。
- この経路は「固定回数で空配列へ append するだけ」のパターンが多く、
  ループ主体の通常初期化へ縮退できる余地がある。

目的:
- IIFE を必要としない `grid` 初期化パターンを特定し、通常の文列（宣言 + ループ + append）へ縮退する。
- sample/13 の可読性を改善し、不要ラムダ生成を抑制する。

対象:
- `src/hooks/cpp/emitter/stmt.py`
- `src/hooks/cpp/emitter/collection_expr.py`
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/13_maze_generation_steps.cpp`（再生成確認）

非対象:
- 全初期化式の式木再設計
- EAST3 全体のノード仕様変更
- 他 backend への同時展開

受け入れ基準:
- sample/13 の `grid` 初期化で不要 IIFE が再出力されない。
- 意味保持した通常文列の初期化へ縮退し、生成コードが短縮される。
- 既存 transpile/unit テストが通り、挙動退行がない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --stems 13_maze_generation_steps --force`

決定ログ:
- 2026-03-02: ユーザー指示により、sample/13 の `grid` 初期化 IIFE 縮退を P0 として起票。
- 2026-03-02: 現行出力が `list<list<int64>>(cell_h, list<int64>(cell_w, 1))` であり、`[&]() -> list<list<int64>> { ... }()` IIFE が再出力されていないことを確認した。
- 2026-03-02: `python3 tools/regenerate_samples.py --langs cpp --stems 13_maze_generation_steps --force` / `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` / `python3 tools/check_py2cpp_transpile.py` を実行し、すべて通過を確認した。

## 分解

- [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S1-01] sample/13 の IIFE 初期化断片を棚卸しし、縮退可能条件を固定する。
- [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S1-02] 「縮退可能 / IIFE維持」の境界条件を仕様化する（fail-closed）。
- [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S2-01] CppEmitter の初期化出力を更新し、縮退可能パターンで通常文列へ変換する。
- [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S2-02] fallback 経路を維持し、縮退不可ケースは現行 IIFE 出力に戻す。
- [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S3-01] unit テストを追加し、IIFE 再発と誤縮退を回帰検知可能にする。
- [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S3-02] `sample/cpp/13` 再生成と transpile チェックで非退行を確認する。
