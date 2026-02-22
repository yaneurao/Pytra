# TASK GROUP: TG-P0-SH

最終更新: 2026-02-22

関連 TODO:
- `docs-jp/todo.md` の `ID: P0-SH-01` 〜 `P0-SH-04`

背景:
- selfhost の変換・ビルド・実行が不安定だと、回帰検出と改善サイクル全体が止まる。

目的:
- selfhost を日次で再現可能な最小経路に固定し、エラー再発時に即座に再検出できる状態を作る。

対象:
- selfhost `.py` 経路の復旧
- `selfhost/py2cpp.out` 最小経路の安定化
- selfhost コンパイルエラーの段階削減
- `tools/prepare_selfhost_source.py` スタブ整理

非対象:
- C++ 以外ターゲットの最適化
- selfhost と無関係な文法追加

受け入れ基準:
- selfhost の入力/生成/実行が再現可能
- 回帰時に再検出手順が残っている
- スタブ依存が段階的に減る

確認コマンド:
- `python3 tools/build_selfhost.py`
- `python3 tools/check_selfhost_cpp_diff.py`

決定ログ:
- 2026-02-22: 初版作成（todo から文脈分離）。
