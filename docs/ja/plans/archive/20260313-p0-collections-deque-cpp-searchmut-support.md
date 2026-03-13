# P0: `collections.deque.count()` / `remove()` representative C++ support

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-COLLECTIONS-DEQUE-CPP-SEARCHMUT-01`

背景:
- `collections.deque` の representative C++ lane は、constructor、`append` / `appendleft`、`popleft` / `pop`、`extendleft(iterable)`、`reverse()`、`rotate()`、`len` / truthiness まで `::std::deque<T>` surface に揃った。
- `S1-01` で `q.count(...)` / `q.remove(...)` の surface leak を固定し、`S2-01` で `count(value)`、`S2-02` で `remove(value)` を STL algorithm surface に揃えた。残りは representative smoke と closeout のみ。
- `clear()`、`extend()`、`reverse()`、`rotate()` はすでに valid C++ surface に落ちるため、この task は search / mutate gap の `count` / `remove` subset に限定する。

目的:
- representative C++ lane で `collections.deque.count()` / `remove()` を valid な STL algorithm surface に揃える。
- deque representative mutation subset を focused regression と smoke で固定する。

対象:
- `from collections import deque`
- representative method subset: `count(value)`, `remove(value)`
- focused regression / smoke / docs / TODO の同期

非対象:
- `deque` 全 API (`maxlen`, arbitrary insert/remove, iterator invalidation semantics など)
- `remove()` の例外メッセージ完全一致や full Python compatibility 全部
- 全 backend への同時 rollout
- `collections` module 全体の redesign
- C++ runtime に新しい deque object hierarchy を追加すること

受け入れ基準:
- focused regression で `count(value)` / `remove(value)` が STL algorithm surface に揃った状態を固定する。
- representative C++ lane で `count()` は valid な `std::count`-based surface に lower される。
- representative C++ lane で `remove()` は first-hit erase surface に lower される。
- representative build/run smoke で `count` / `remove` の代表 fixture が通る。
- docs / TODO の ja/en mirror に support scope と非対象が反映される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k deque_searchmut`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `git diff --check`

決定ログ:
- 2026-03-13: `clear()`、`extend()`、`reverse()`、`rotate()` はすでに valid C++ に落ちるため、新 task は `count` / `remove` subset のみに限定した。
- 2026-03-13: `S1-01` として `q.count(...)` / `q.remove(...)` の current invalid C++ surface を focused regression / TODO / plan で固定した。
- 2026-03-13: `S2-01` として typed deque owner の `count(value)` を `std::count(begin, end, value)` surface へ lower した。focused regression は `remove()` leak のみへ narrowed した。
- 2026-03-13: `S2-02` として typed deque owner の `remove(value)` を `std::find + erase` surface へ lower し、not-found は `ValueError("deque.remove missing value")` とした。残りは build/run smoke のみ。
- 2026-03-13: `S3-01` として representative fixture の build/run smoke を追加し、`count/remove` bundle の出力 `2 / 2 / 1` を固定した。これで task の受け入れ基準はすべて充足した。

## 分解

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-SEARCHMUT-01] `collections.deque.count()` / `remove()` representative C++ lane を固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-SEARCHMUT-01-S1-01] current invalid C++ surface (`count`, `remove`) を focused regression / TODO / plan で固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-SEARCHMUT-01-S2-01] `count(value)` を valid `std::count`-based surface に lower する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-SEARCHMUT-01-S2-02] `remove(value)` を first-hit erase surface に lower する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-SEARCHMUT-01-S3-01] build/run smoke と support wording を同期して close する。
