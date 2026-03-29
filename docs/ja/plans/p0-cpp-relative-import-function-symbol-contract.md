<a href="../../en/plans/p0-cpp-relative-import-function-symbol-contract.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ relative import function symbol contract

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-RELATIVE-IMPORT-FUNCTION-SYMBOL-01`

背景:
- C++ multi-file lane では sibling relative import の constant-only、class-only、mixed constant+class、alias constant+class の representative smoke を固定した。
- ただし imported function symbol が constant や class/type と同じ sibling relative import statement に同居する contract はまだ representative case で固定されていない。
- multi-file project では helper factory / constructor wrapper / constant を同じ module からまとめて import する書き方が自然に現れる。

目的:
- C++ multi-file build で imported function symbol を含む sibling relative import contract を representative smoke で固定する。
- imported function origin、constant、class/type、alias local name の組み合わせが current contract のまま build/run success することを証明する。

対象:
- `pytra-cli.py --target cpp --multi-file` における sibling relative import function lane
- function + constant + class/type を含む representative smoke
- alias local name を含む current contract
- docs / TODO / regression の同期

非対象:
- wildcard relative import support
- non-C++ backend への横展開
- import semantics や callable lowering の再設計
- package root / namespace package の再設計

受け入れ基準:
- `from .controller import (BUTTON_A as BUTTON, make_pad as make_pad_fn, Pad as ControllerPad)` を使う representative C++ multi-file smoke が build/run で通ること。
- generated consumer module が imported function / constant / class-type の origin を正しく resolve すること。
- 既存の non-function sibling relative import smoke を壊さないこと。
- `python3 tools/check/check_todo_priority.py`、focused C++ regression、`python3 tools/build_selfhost.py`、`git diff --check` が通ること。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k sibling_relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: TODO が空になったため、relative import support の adjacent follow-up を `P0` で起票した。対象は imported function symbol を含む representative build/run contract 固定である。
- 2026-03-12: representative smoke では generated consumer `.cpp` に sibling module header が既に include されているため、redundant forward declaration block は不要だった。function return type を current consumer emitter context で再解決すると `Pad make_pad(...)` のような壊れた宣言になるため、multi-file writer は user module dependency declaration を header include のみへ寄せる方針で閉じた。

## 分解

- [x] [ID: P0-CPP-RELATIVE-IMPORT-FUNCTION-SYMBOL-01-S1-01] plan / TODO に representative function-symbol contract を固定する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-FUNCTION-SYMBOL-01-S2-01] function + constant + class/type を含む sibling relative import representative smoke を追加し、current lane を確認する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-FUNCTION-SYMBOL-01-S2-02] residual が見つかった場合のみ emitter / writer / schema を修正する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-FUNCTION-SYMBOL-01-S3-01] docs / TODO / regression を current contract に同期して task を閉じる。
