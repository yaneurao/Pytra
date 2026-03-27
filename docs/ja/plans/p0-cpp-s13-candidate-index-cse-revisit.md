<a href="../../en/plans/p0-cpp-s13-candidate-index-cse-revisit.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: sample/13 `candidates` 選択式 CSE/hoist 再実施

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S13-CANDIDATE-CSE-02`

背景:
- sample/13 の `candidates` 選択では、index 計算式と要素取得の中間結果を
  共有できる箇所があり、再計算や一時式の冗長化が発生しやすい。
- 既存対応はあるが、改善項目 #6 として「明示タスク化して P0 で管理する」ことが必要。

目的:
- `candidates` 選択ロジックの index 計算と要素取得を CSE/hoist で整理し、
  sample/13 の C++ 出力可読性とホットパス効率を安定化する。

対象:
- `src/hooks/cpp/emitter/expr.py`
- `src/hooks/cpp/emitter/stmt.py`
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/13_maze_generation_steps.cpp`（再生成確認）

非対象:
- EAST3 全体の汎用 CSE pass 導入
- sample/13 以外への一括展開
- runtime API 変更

受け入れ基準:
- sample/13 の `candidates` 選択で index 計算の重複が縮退する。
- 要素取得が単一路（hoist 後の1回評価）として出力される。
- transpile/unit チェックが通り、挙動退行がない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --stems 13_maze_generation_steps --force`

決定ログ:
- 2026-03-02: ユーザー指示「6.もP0としてTODOに積む」に基づき、sample/13 改善項目 #6 を再実施タスクとして起票。
- 2026-03-02: `Assign(Name = Subscript(...))` で owner が `Name` かつ複雑 index の場合に `auto __idx_* = ...;` を先行生成し、`candidates[__idx_*]` へ縮退する emitter 経路を追加した（`src/hooks/cpp/emitter/stmt.py`）。
- 2026-03-02: `test_py2cpp_codegen_issues.py` の sample/13 回帰を更新し、`__idx_*` hoist 出力を固定した。
- 2026-03-02: `python3 tools/regenerate_samples.py --langs cpp --stems 13_maze_generation_steps --force` / `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v` / `python3 tools/check_py2cpp_transpile.py` を実行し、すべて通過を確認した。

## 分解

- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S1-01] sample/13 の `candidates` 選択で重複している index/要素取得断片を棚卸しする。
- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S1-02] 適用境界（型既知・副作用なし・fail-closed）を仕様化する。
- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S2-01] CppEmitter で index 計算と要素取得の hoist 出力を実装する。
- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S2-02] 適用不可ケースの fallback を固定し、意味保持を担保する。
- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S3-01] unit テストを追加し、重複式再発を検知可能にする。
- [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S3-02] `sample/cpp/13` 再生成と transpile チェックで非退行を確認する。
