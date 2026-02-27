# TASK GROUP: TG-P2-ANY-OBJ

最終更新: 2026-02-22

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-ANY-01` 〜 `P2-ANY-07`

背景:
- `Any/object` 境界が曖昧だと、過剰 boxing や型崩れで selfhost・生成コード双方の品質が落ちる。

目的:
- `Any` と `object` の責務境界を明確化し、必要最小限の変換へ整理する。

対象:
- `cpp_type` / 式描画の fallback 最適化
- `dict` 既定値経路の型整理
- `std::any` 通過経路の可視化と削減

非対象:
- 型システム全体の刷新

受け入れ基準:
- `object` への不要フォールバックが減る
- `std::any` 経路が段階削減される
- selfhost 回帰が発生しない

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`

決定ログ:
- 2026-02-22: 初版作成。
