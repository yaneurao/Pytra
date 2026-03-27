<a href="../../en/plans/p0-cpp-relative-import-mixed-symbol-contract.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ relative import mixed symbol contract

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-RELATIVE-IMPORT-MIXED-SYMBOL-01`

背景:
- C++ multi-file lane では sibling relative import の constant/function lane と class/type lane をそれぞれ representative smoke で固定した。
- ただし `from .controller import (BUTTON_A, Pad)` のように、1 つの relative import statement に constant と class/type が同居する contract はまだ代表ケースで固定されていない。
- Pytra-NES のような multi-file project では、同じ sibling module から constant と helper class をまとめて import する書き方が自然に現れる。

目的:
- C++ multi-file build で、1 つの sibling relative import statement から mixed symbol を取り込む lane を representative smoke で固定する。
- imported constant lane と imported class/type lane の組み合わせが current contract のまま build/run success することを証明する。

対象:
- `pytra-cli.py --target cpp --multi-file` における sibling relative import の mixed symbol lane
- 1 つの `ImportFrom` statement から constant と class/type を同時に import する representative smoke
- docs / TODO / regression の同期

非対象:
- wildcard relative import support
- non-C++ backend への横展開
- alias import / nested package / namespace package の再設計
- import lane 全体の意味論変更

受け入れ基準:
- `from .controller import (BUTTON_A, Pad)` を使う representative C++ multi-file smoke が build/run で通ること。
- generated consumer module が imported constant と imported class/type を同じ statement 由来でも正しく render すること。
- 既存の constant-only / class-only sibling relative import smoke を壊さないこと。
- `python3 tools/check_todo_priority.py`、focused C++ regression、`python3 tools/build_selfhost.py`、`git diff --check` が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p 'test_py2cpp_features.py' -k sibling_relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: TODO が空になったため、relative import support の adjacent follow-up を `P0` で起票した。対象は semantics 変更ではなく representative mixed-symbol contract の固定である。
- 2026-03-12: representative smoke `from .controller import (BUTTON_A, Pad)` は current C++ multi-file lane のままで build/run success し、constant lane と class/type lane の組み合わせに追加修正は不要だった。

## 分解

- [x] [ID: P0-CPP-RELATIVE-IMPORT-MIXED-SYMBOL-01-S1-01] plan / TODO に representative mixed-symbol contract を固定する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-MIXED-SYMBOL-01-S2-01] mixed constant + class sibling relative import の representative C++ multi-file smoke を追加し、current lane を確認する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-MIXED-SYMBOL-01-S2-02] mixed symbol lane で residual が見つかった場合のみ emitter / writer / schema を修正する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-MIXED-SYMBOL-01-S3-01] docs / TODO / regression を current contract に同期して task を閉じる。
