# TASK GROUP: TG-P1-CPP-REDUCE

最終更新: 2026-02-23

関連 TODO:
- `docs-jp/todo.md` の `ID: P1-CPP-REDUCE-01` 〜 `P1-CPP-REDUCE-02`

背景:
- `py2cpp.py` の肥大化により、変更影響範囲が広くレビュー・回帰確認コストが高い。

目的:
- `py2cpp.py` を C++ 固有責務へ段階縮退し、共通処理は共通層へ移す。
- 全言語 selfhost を前提に、`py2cpp.py` を「C++ 向け thin adapter」に近づける。

対象:
- `CodeEmitter` 側へ移管可能なロジック
- CLI 層の責務分離
- `py2cpp.py` 内の汎用 helper（ソート/文字列整形/module 解析補助など）の共通層移管

非対象:
- selfhost 安定性を犠牲にする大規模一括整理

受け入れ基準:
- `py2cpp.py` 行数と分岐数が段階減少
- 主要テストと selfhost 検証が維持
- 汎用処理の新規追加先が `src/pytra/compiler/` 優先に統一され、`py2cpp.py` は C++ 固有コード中心になる

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/build_selfhost.py`

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-23: 全言語 selfhost の長期目標に合わせ、`py2cpp.py` への汎用 helper 追加を抑制して共通層先行抽出へ寄せる方針（`P1-CPP-REDUCE-02`）を追加した。
