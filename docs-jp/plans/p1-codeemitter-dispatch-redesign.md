# TASK GROUP: TG-P1-CED

最終更新: 2026-02-22

関連 TODO:
- `docs-jp/todo.md` の `ID: P1-CED-*`

背景:
- selfhost で static 束縛前提が強く、共通化時に派生実装へ到達しない経路が発生する。

目的:
- `render_expr` / `emit_stmt` を hook 主体に再設計し、共通化と selfhost 安定を両立する。

対象:
- kind 単位の hook 注入
- CppEmitter の hook 優先 + fallback 2段構成
- fallback の段階削減
- py2cpp/py2rs の共通化候補整理

非対象:
- 一括での全面 rewrite

受け入れ基準:
- hooks 有効時の生成結果が既存と一致
- selfhost diff で `mismatches=0`
- `py2cpp.py` 本体分岐が段階的に短縮

確認コマンド:
- `python3 tools/check_selfhost_cpp_diff.py`
- `python3 tools/check_py2cpp_transpile.py`

決定ログ:
- 2026-02-22: 初版作成。
