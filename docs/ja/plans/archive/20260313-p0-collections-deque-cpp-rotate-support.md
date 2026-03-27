<a href="../../../en/plans/archive/20260313-p0-collections-deque-cpp-rotate-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `collections.deque.rotate()` representative C++ support

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-COLLECTIONS-DEQUE-CPP-ROTATE-01`

背景:
- `collections.deque` の representative C++ lane は、constructor、`append` / `appendleft`、`popleft` / `pop`、`extendleft(iterable)`、`reverse()`、`len` / truthiness まで `::std::deque<T>` surface に揃った。
- `S1-01` で `q.rotate(...)` の surface leak を固定し、`S2-01` で `rotate()` / `rotate(n)` は valid な `::std::rotate(...)` bundle に揃った。残りは representative smoke と closeout のみ。
- `clear()`、`extend()`、`reverse()` はすでに valid C++ surface に落ちるため、この task は invalid surface が残る `rotate` subset に限定する。

目的:
- representative C++ lane で `collections.deque.rotate()` / `rotate(n)` を valid な `::std::rotate(...)` bundle に揃える。
- deque representative mutation subset を focused regression と smoke で固定する。

対象:
- `from collections import deque`
- representative method subset: `rotate()`, `rotate(positive int)`, `rotate(negative int)`
- focused regression / smoke / docs / TODO の同期

非対象:
- `deque` 全 API (`maxlen`, arbitrary insert/remove, iterator invalidation semantics など)
- 非整数 step や runtime 型不明 step の完全対応
- 全 backend への同時 rollout
- `collections` module 全体の redesign
- C++ runtime に新しい deque object hierarchy を追加すること

受け入れ基準:
- focused regression で `rotate()` / `rotate(n)` が valid な `::std::rotate(...)` bundle に揃った状態を固定する。
- representative C++ lane で `rotate()` / `rotate(n)` は valid な `::std::rotate(...)` bundle に lower される。
- representative build/run smoke で positive / negative / default rotate の代表 fixture が通る。
- docs / TODO の ja/en mirror に support scope と非対象が反映される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k deque_rotate`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `git diff --check`

決定ログ:
- 2026-03-13: `clear()`、`extend()`、`reverse()` はすでに valid C++ に落ちるため、新 task は `rotate` subset のみに限定した。
- 2026-03-13: `S1-01` として `q.rotate()`, `q.rotate(1)`, `q.rotate(-1)` の current invalid C++ surface を focused regression / TODO / plan で固定した。
- 2026-03-13: `S2-01` として typed deque owner の `rotate()` / `rotate(n)` を normalized step + `::std::rotate(...)` bundle へ lower した。残りは build/run smoke のみ。
- 2026-03-13: `S3-01` として representative fixture の build/run smoke を追加し、default / positive / negative rotate の出力 `3 / 3 / 2` を固定した。これで task の受け入れ基準はすべて充足した。

## 分解

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ROTATE-01] `collections.deque.rotate()` representative C++ lane を固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ROTATE-01-S1-01] current invalid C++ surface (`rotate()`, `rotate(1)`, `rotate(-1)`) を focused regression / TODO / plan で固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ROTATE-01-S2-01] `rotate()` / `rotate(n)` を valid `::std::rotate(...)` bundle に lower する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ROTATE-01-S3-01] build/run smoke と support wording を同期して close する。
