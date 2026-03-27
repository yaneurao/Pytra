<a href="../../../en/plans/archive/20260311-p1-relative-import-closeout.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: relative import の current contract を entrypoint / docs / smoke に揃える

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-CLOSEOUT-01`

背景:
- `P0-RELATIVE-IMPORT-SUPPORT-01` で relative `from-import` 自体は実装済みで、`from .helper import f` / `from ..pkg import y` / `from . import x` / `from .helper import *` は current HEAD で通る。
- しかし support matrix の一部が古いままで、[docs/ja/language/cpp/spec-support.md](/workspace/Pytra/docs/ja/language/cpp/spec-support.md) と英語ミラーでは relative import / wildcard import が未対応扱いのまま残っている。
- さらに `py2x.py` entrypoint 側には relative import の representative regression がなく、Pytra-NES のような実験で「今も未対応ではないか」と誤認しやすい。

目的:
- relative import の current contract を `py2x.py` entrypoint regression と support matrix に反映し、「既に通るもの」と「fail-closed の条件」を明確にする。
- stale な未対応記述を消し、relative import が再び未対応へ戻ったときに regression で落ちるようにする。

対象:
- `test/unit/tooling/test_py2x_cli.py`
- `docs/ja/language/cpp/spec-support.md`
- `docs/en/language/cpp/spec-support.md`
- `docs/ja/todo/index.md`
- `docs/en/todo/index.md`

非対象:
- 新しい import syntax の追加
- Python 非合法構文 `import .m`
- `__package__` / namespace package の完全互換
- wildcard import の新機能追加

受け入れ基準:
- `py2x.py --target cpp` で sibling relative import が通る representative regression が追加されていること。
- `py2x.py --target cpp` で root escape relative import が `kind=unsupported_import_form` で fail-closed する representative regression が追加されていること。
- C++ support matrix の relative import / wildcard import 行が current contract に同期していること。
- docs / test の進捗メモは cluster 単位の 1 行要約に留まっていること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py' -k relative_import`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative`
- `git diff --check`

分解:
- [x] [ID: P1-RELATIVE-IMPORT-CLOSEOUT-01-S1-01] relative import の current contract と stale surface を plan / TODO に固定する。
- [x] [ID: P1-RELATIVE-IMPORT-CLOSEOUT-01-S2-01] `py2x.py` entrypoint の relative import representative regression を追加する。
- [x] [ID: P1-RELATIVE-IMPORT-CLOSEOUT-01-S2-02] C++ support matrix の relative import / wildcard import 記述を current contract に同期する。
- [x] [ID: P1-RELATIVE-IMPORT-CLOSEOUT-01-S3-01] targeted regression / docs / archive を更新して閉じる。

決定ログ:
- 2026-03-11: active TODO が空のため follow-up を起票した。relative import 本体は既に実装済みなので、追加実装ではなく entrypoint regression と stale docs の close-out を先に片付ける。
- 2026-03-11: `py2x.py --target cpp` の representative regression として、sibling relative import success と root-escape fail-closed (`kind=unsupported_import_form`) を `test_py2x_cli.py` に追加した。
- 2026-03-11: C++ support matrix の relative import / wildcard import 行を current contract に合わせ、relative import は `supported`、wildcard import は `partial + unresolved wildcard fail-closed` に揃えた。
- 2026-03-11: targeted regression と support matrix が current contract に揃ったので、この close-out task は archive へ移し、今後は `P0-RELATIVE-IMPORT-SUPPORT-01` の履歴と合わせて参照する。
