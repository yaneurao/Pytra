<a href="../../../en/plans/archive/20260313-p0-collections-deque-cpp-reverse-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `collections.deque.reverse()` representative C++ support

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-COLLECTIONS-DEQUE-CPP-REVERSE-01`

背景:
- `collections.deque` の representative C++ lane は、constructor、`append` / `appendleft`、`popleft` / `pop`、`extendleft(iterable)`、`len` / truthiness まで `::std::deque<T>` surface に揃った。
- `S1-01` で `q.reverse();` の surface leak を固定し、`S2-01` で `reverse()` は `::std::reverse(begin, end)` に揃った。残りは representative smoke と closeout のみ。
- `clear()` や `extend()` はすでに valid C++ surface に落ちるため、この task は end-to-end で invalid surface が残る `reverse()` に限定する。

目的:
- representative C++ lane で `collections.deque.reverse()` を `::std::reverse(begin, end)` に揃える。
- deque representative subset の mutation surface を focused regression と smoke で固定する。

対象:
- `from collections import deque`
- representative method subset: `reverse()`
- focused regression / smoke / docs / TODO の同期

非対象:
- `deque` 全 API (`rotate`, `maxlen`, arbitrary insert/remove, iterator invalidation semantics など)
- 全 backend への同時 rollout
- `collections` module 全体の redesign
- C++ runtime に新しい deque object hierarchy を追加すること

受け入れ基準:
- focused regression で `reverse()` が `::std::reverse(begin, end)` に揃った状態を固定する。
- representative C++ lane で `reverse()` は `::std::reverse(q.begin(), q.end())` に lower される。
- build/run smoke で representative fixture が通る。
- docs / TODO の ja/en mirror に support scope と非対象が反映される。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k deque_reverse`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`
- `git diff --check`

決定ログ:
- 2026-03-13: `clear()` / `extend()` はすでに valid C++ に落ちるため、新 task は `reverse()` のみに限定した。
- 2026-03-13: `S1-01` として `q.reverse();` の current invalid C++ surface を focused regression / TODO / plan で固定した。
- 2026-03-13: `S2-01` として typed deque owner の `reverse()` を `::std::reverse(begin, end)` へ lower した。残りは build/run smoke のみ。
- 2026-03-13: `S3-01` として representative fixture の build/run smoke を追加し、`deque([1, 2, 3]).reverse()` の出力 `3 / 2 / 1` を固定した。これで task の受け入れ基準はすべて充足した。

## 分解

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REVERSE-01] `collections.deque.reverse()` representative C++ lane を固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REVERSE-01-S1-01] current invalid C++ surface (`q.reverse();`) を focused regression / TODO / plan で固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REVERSE-01-S2-01] `reverse()` を `::std::reverse(begin, end)` に lower する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REVERSE-01-S3-01] build/run smoke と support wording を同期して close する。
