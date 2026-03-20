# P0: C++ relative import alias symbol contract

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-RELATIVE-IMPORT-ALIAS-SYMBOL-01`

背景:
- C++ multi-file lane では sibling relative import の constant-only、class-only、mixed constant+class statement を representative smoke で固定した。
- ただし `from .controller import (BUTTON_A as BUTTON, Pad as ControllerPad)` のような alias import contract はまだ representative case で固定されていない。
- multi-file project では同名回避や role 明示のため `as` alias を使うことがあり、relative import support を practical にするには alias lane も lock しておく必要がある。

目的:
- C++ multi-file build で sibling relative import alias lane を representative smoke で固定する。
- imported symbol の origin は namespace-qualified に解決されつつ、consumer 側では alias local name が使える current contract を build/run success で証明する。

対象:
- `py2x.py --target cpp --multi-file` における sibling relative import alias lane
- constant と class/type を含む alias import representative smoke
- docs / TODO / regression の同期

非対象:
- wildcard relative import support
- non-C++ backend への横展開
- alias import の意味論変更
- package root / namespace package の再設計

受け入れ基準:
- `from .controller import (BUTTON_A as BUTTON, Pad as ControllerPad)` を使う representative C++ multi-file smoke が build/run で通ること。
- generated consumer module が alias local name を受けつつ imported origin を正しく resolve すること。
- 既存の non-alias sibling relative import smoke を壊さないこと。
- `python3 tools/check_todo_priority.py`、focused C++ regression、`python3 tools/build_selfhost.py`、`git diff --check` が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p 'test_py2cpp_features.py' -k sibling_relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: TODO が空になったため、relative import support の adjacent follow-up を `P0` で起票した。対象は alias lane の representative build/run contract 固定である。
- 2026-03-12: representative smoke `from .controller import (BUTTON_A as BUTTON, Pad as ControllerPad)` は current C++ multi-file lane のままで build/run success した。alias local name は generated consumer に残らず imported origin へ正しく resolve される。
- 2026-03-12: close-out 時点で alias lane に追加の emitter / writer / schema 修正は不要であり、task は regression lock と docs sync のみで完了とした。

## 分解

- [x] [ID: P0-CPP-RELATIVE-IMPORT-ALIAS-SYMBOL-01-S1-01] plan / TODO に representative alias contract を固定する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-ALIAS-SYMBOL-01-S2-01] alias 付き mixed symbol sibling relative import の representative C++ multi-file smoke を追加し、current lane を確認する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-ALIAS-SYMBOL-01-S2-02] alias lane で residual が見つかった場合のみ emitter / writer / schema を修正する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-ALIAS-SYMBOL-01-S3-01] docs / TODO / regression を current contract に同期して task を閉じる。
