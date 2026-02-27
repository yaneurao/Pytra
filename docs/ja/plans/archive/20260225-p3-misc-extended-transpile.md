# TASK GROUP: TG-P3-MISC-EXT

最終更新: 2026-02-25

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P3-MISC-02`

背景:
- 既存の `test/misc/*.py` 100 件は処理済みだが、追加で 400 件が増えているため、同条件で `py2cpp.py` 変換可否を再確立する必要がある。
- `test/misc` はソース差分回帰素材でもあり、タスク実行時に `test/misc/*.py` 自体の改変はしない。

対象:
- `test/misc/101_*.py` 〜 `test/misc/500_*.py` 相当の追加 400 件

非対象:
- `test/misc` の生成物（`.cpp`）の品質最適化。
- 全言語変換。

受け入れ基準:
- 対象 400 件それぞれについて `python3 src/py2cpp.py test/misc/<file>.py /tmp/<base>.cpp` が成功する。
- 失敗ケースは `docs/ja/plans/p3-misc-extended-transpile.md` の決定ログへ逐次記録し、同一原因はまとめて解消する。

制約:
- `test/misc/*.py` の内容をこのタスクのために編集しない。
- 変換不能の修正は `py2cpp.py` / parser / `CodeEmitter` / 共通基盤側で対応する。
- 各 `S*` タスク完了ごとに対象ファイルの変換成功ログとコマンドを追記する。

決定ログ:
- （追加時点では未着手。完了時に順次追記）
