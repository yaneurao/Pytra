<a href="../../../en/plans/archive/20260313-p0-collections-deque-cpp-iterable-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `collections.deque` iterable constructor / extendleft representative C++ support

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-COLLECTIONS-DEQUE-CPP-ITERABLE-01`

背景:
- `collections.deque` の representative C++ lane は、zero-arg constructor、`append` / `appendleft`、`popleft` / `pop`、`len` / truthiness まで揃った。
- これで `deque([1, 2])` は range ctor、`extendleft([3, 4])` は `push_front` loop bundle へ揃い、残りは representative smoke と closeout だけになった。
- `extend([...])` はすでに `insert(end, begin, end)` へ lower されるため、この task は invalid C++ surface が残る constructor / left-extend bundle に絞る。

目的:
- representative C++ lane で iterable-based `collections.deque` surface を `::std::deque<T>` に揃える。
- 直前までの end-op/task と合わせて、実用上必要な `deque` subset を file-level regression と smoke で固定する。

対象:
- single-arg `deque(iterable)` constructor
- `extendleft(iterable)` representative lowering
- focused regression / smoke / docs / TODO の同期

非対象:
- `deque` 全 API (`rotate`, `maxlen`, arbitrary insert/remove, iterator invalidation semantics など)
- 全 backend への同時 rollout
- `collections` module 全体の redesign
- C++ runtime に新しい deque object hierarchy を追加すること

受け入れ基準:
- focused regression で iterable-based `deque` surface が `::std::deque<T>` / `push_front` bundle に揃った状態を固定する。
- representative C++ lane で `deque(iterable)` は valid `::std::deque<T>` constructor surface に lower される。
- representative C++ lane で `extendleft(iterable)` は valid C++ loop / `push_front` bundle に lower される。
- build/run smoke で representative fixture が通る。
- docs / TODO の ja/en mirror に support scope と非対象が反映される。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k deque_iterable`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`
- `git diff --check`

決定ログ:
- 2026-03-13: iterable-based `deque` surface のうち、`extend` はすでに valid C++ に落ちるため、新 task は `deque(iterable)` と `extendleft(iterable)` に限定した。
- 2026-03-13: `S1-01` として `q = deque(list<int64>{...});` と `q.extendleft(...)` の current invalid C++ surface を focused regression で固定した。
- 2026-03-13: `S2-01` として `deque(iterable)` を typed `::std::deque<T>(begin, end)` range ctor へ lower した。focused regression は残る `extendleft` leak だけへ narrowed した。
- 2026-03-13: `S2-02` として `extendleft(iterable)` を snapshot + `push_front` loop bundle へ lower した。typed `deque` owner の iterable surface は representative C++ lane で `std::deque` に揃った。
- 2026-03-13: `S3-01` として representative fixture の build/run smoke を追加し、`deque([1, 2]) + extendleft([3, 4])` の出力 `4 / 3 / 1 / 2` を固定した。これで task の受け入れ基準はすべて充足した。

## 分解

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ITERABLE-01] `collections.deque` iterable constructor / `extendleft` representative C++ lane を固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ITERABLE-01-S1-01] current invalid C++ surface (`deque(iterable)`, `extendleft(iterable)`) を focused regression / TODO / plan で固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ITERABLE-01-S2-01] `deque(iterable)` を valid `::std::deque<T>` constructor surface に lower する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ITERABLE-01-S2-02] `extendleft(iterable)` を `push_front` loop bundle に lower する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ITERABLE-01-S3-01] build/run smoke と support wording を同期して close する。
