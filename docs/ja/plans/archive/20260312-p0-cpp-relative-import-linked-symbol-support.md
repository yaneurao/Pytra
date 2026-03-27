<a href="../../../en/plans/archive/20260312-p0-cpp-relative-import-linked-symbol-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ relative import linked symbol support

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-RELATIVE-IMPORT-LINKED-SYMBOL-01`

背景:
- relative import の syntax 自体は既に support 済みで、`from .controller import (...)` の parenthesized symbol list も parser では受理できる。
- ただし C++ multi-file build では、`from .controller import BUTTON_A` のような imported module-level symbol を plain `Name` のまま emit してしまい、generated `ppu.cpp` が `BUTTON_A was not declared in this scope` で止まる。
- 既存 regression は function alias / module alias の build/run までは固定しているが、module-level constant / global symbol import の representative smoke が抜けている。
- Pytra-NES では `ppu.py -> from .controller import (BUTTON_A, BUTTON_B, ...)` が最初の blocker なので、この lane を先に通す必要がある。

目的:
- C++ multi-file linked build で、relative import された user module symbol を plain expr / bitwise expr から正しく参照できるようにする。
- parser support の有無ではなく、generated C++ が compile / run できる current contract を representative smoke で固定する。

対象:
- `py2x.py --target cpp --multi-file` の relative import symbol build/run lane
- imported user-module symbol の `Name` render
- multi-file writer の imported module-level symbol forward declaration
- representative regression / inventory / docs の同期

非対象:
- wildcard relative import support
- non-C++ backend への横展開
- namespace package / package root 推定の再設計
- module-level mutable global semantics の全面見直し

受け入れ基準:
- `from .controller import (BUTTON_A, BUTTON_B)` を使う representative C++ multi-file smoke が build/run で通ること。
- generated consumer module が imported user-module symbol を namespace-qualified して参照すること。
- generated consumer module が imported user-module function と module-level global の両方を compile できるだけの forward declaration を持つこと。
- 既存の relative import function alias / module alias build-run smoke を壊さないこと。
- `python3 tools/check_todo_priority.py`、focused C++ regression、`python3 tools/build_selfhost.py`、`git diff --check` が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: TODO が空だったため follow-up を `P0` で起票した。blocker は parser ではなく C++ multi-file linked build で、imported module-level constant が namespace-qualified されず compile error になる点にある。
- 2026-03-12: v1 の対象は user module symbol のうち `module-level constant/global + function` に限定し、class/type import や cross-runtime import contract までは広げない。
- 2026-03-12: representative smoke は `ppu.py -> from .controller import (BUTTON_A, BUTTON_B)` とし、`BUTTON_A | BUTTON_B` が generated `ppu.cpp` で `pytra_mod_controller::BUTTON_A | pytra_mod_controller::BUTTON_B` へ render される contract に固定した。
- 2026-03-12: multi-file writer は imported user module の forward declaration に関数だけでなく module-level globals も含める。v1 は `build_module_type_schema()` へ `globals` schema を追加して同期する。
- 2026-03-12: focused C++ relative-import regression と selfhost build を通したので、`S1-01` / `S2-01` / `S2-02` は完了とし、残る `S3-01` は alias regression と docs wording の同期だけに縮んだ。
- 2026-03-12: existing relative-import function alias / module alias regression を壊さずに sibling relative symbol-list import constants smoke が build/run で通ったため、task 全体を完了扱いにして archive へ移す。

## 分解

- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-SYMBOL-01-S1-01] current compile failure と representative smoke contract を plan / TODO / focused regression に固定する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-SYMBOL-01-S2-01] imported user-module symbol の `Name` render を namespace-qualified user symbol へ揃える。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-SYMBOL-01-S2-02] multi-file writer に imported module-level symbol forward declaration を追加する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-SYMBOL-01-S3-01] relative import function alias / module alias regression と docs を current contract に同期して閉じる。
