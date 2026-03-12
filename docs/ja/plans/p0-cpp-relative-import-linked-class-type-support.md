# P0: C++ relative import linked class/type support

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-RELATIVE-IMPORT-LINKED-CLASS-TYPE-01`

背景:
- relative import の syntax と module-level constant / function symbol の C++ multi-file lane はすでに representative smoke で固定された。
- ただし `from .helper import Foo` のような imported class/type symbol は、type position で plain `Foo` のまま emit され、generated consumer が `Foo foo = pytra_mod_helper::Foo(...)` のような C++ を出して compile error になる。
- current multi-file writer は imported module-level function / global の forward declaration までは持つが、imported class/type の declaration contract は持っていない。
- Pytra-NES のような multi-file project では class/type import は自然に現れるため、constant/function lane だけでは実用に足りない。

目的:
- C++ multi-file build で relative import された user-module class/type symbol を type position でも扱えるようにする。
- imported class/type lane の build/run contract を representative smoke で固定し、function/global lane と同じ水準まで引き上げる。

対象:
- `py2x.py --target cpp --multi-file` の imported class/type symbol lane
- module type schema における class storage contract
- multi-file writer の imported class declaration / include contract
- C++ emitter の imported class/type position render
- representative regression / docs / inventory の同期

非対象:
- wildcard relative import support
- non-C++ backend への横展開
- namespace package / package root 推定の再設計
- class layout / ref-vs-value semantics 全体の再設計

受け入れ基準:
- `from .helper import Foo` を使う representative C++ multi-file smoke が current class `storage_hint` contract のもとで build/run で通ること。
- generated consumer module が imported class/type を type position でも namespace-qualified に render すること。
- generated multi-file layout が imported class/type を current storage contract の範囲で compile できるだけの declaration / include contract を持つこと。
- 既存の imported function / global symbol relative import smoke を壊さないこと。
- `python3 tools/check_todo_priority.py`、focused C++ regression、`python3 tools/build_selfhost.py`、`git diff --check` が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: TODO が空になったため follow-up を `P0` で起票した。representative repro は `nes/main.py -> from .helper import Foo` で、current generated `main.cpp` は `Foo foo = pytra_mod_helper::Foo(3);` を出して compile error になる。
- 2026-03-12: first slice は full support ではなく groundwork とし、module type schema に imported class `storage_hint` を追加し、multi-file writer に imported class forward declaration を持たせるところまでを current contract にする。
- 2026-03-12: final v1 target は value/ref class の両方を含む imported class/type build/run support だが、header/include contract の設計は separate slice に分ける。
- 2026-03-12: multi-file writer は optimized user-module EAST を `user_module_east_map` として emitter へ渡し、imported class signature 解決を runtime-only source-path lookup から切り離した。
- 2026-03-12: representative sibling relative import class smoke は current `storage_hint=ref` lane で `rc<pytra_mod_controller::Pad>` と `::rc_new<pytra_mod_controller::Pad>(3)` を生成し、build/run まで通ることを regression で固定した。value-class redesign は本 task の非対象とする。

## 分解

- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-CLASS-TYPE-01-S1-01] representative compile failure と target contract を plan / TODO に固定する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-CLASS-TYPE-01-S2-01] module type schema に imported class `storage_hint` を追加し、multi-file writer に imported class forward declaration を加える。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-CLASS-TYPE-01-S2-02] imported class/type の type position を namespace-qualified C++ type へ render する。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-CLASS-TYPE-01-S2-03] imported class/type の current storage contract に必要な declaration/include contract を整え、representative smoke を build/run success へ切り替える。
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-CLASS-TYPE-01-S3-01] docs / TODO / representative regression を current contract に同期して task を閉じる。
