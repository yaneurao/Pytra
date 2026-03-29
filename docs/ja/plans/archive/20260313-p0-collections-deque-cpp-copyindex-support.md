<a href="../../../en/plans/archive/20260313-p0-collections-deque-cpp-copyindex-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `collections.deque.copy()` / `index()` representative C++ support

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-COLLECTIONS-DEQUE-CPP-COPYINDEX-01`

背景:
- `collections.deque` の representative C++ lane は、constructor、`append` / `appendleft`、`popleft` / `pop`、`extendleft(iterable)`、`reverse()`、`rotate()`、`count()`、`remove()`、`len` / truthiness まで `::std::deque<T>` surface に揃った。
- ただし `copy()` と `index(value)` はまだ `q.copy()` / `q.index(...)` としてそのまま漏れており、`std::deque` に対する valid C++ になっていない。
- `clear()`、`extend()`、`reverse()`、`rotate()`、`count()`、`remove()` はすでに valid C++ surface に落ちるため、この task は expression / lookup gap の `copy` / `index` subset に限定する。

目的:
- representative C++ lane で `collections.deque.copy()` / `index()` を valid な C++ surface に揃える。
- deque representative subset を focused regression と smoke で固定する。

対象:
- `from collections import deque`
- representative method subset: `copy()`, `index(value)`
- focused regression / smoke / docs / TODO の同期

非対象:
- `deque` 全 API (`maxlen`, arbitrary insert/remove, iterator invalidation semantics など)
- `index()` の slice/start/stop overload 全部
- 全 backend への同時 rollout
- `collections` module 全体の redesign
- C++ runtime に新しい deque object hierarchy を追加すること

受け入れ基準:
- focused regression で current invalid C++ surface (`q.copy()`, `q.index(...)`) を固定する。
- representative C++ lane で `copy()` は valid な copy-construction surface に lower される。
- representative C++ lane で `index(value)` は valid な search / distance surface に lower される。
- representative build/run smoke で `copy/index` の代表 fixture が通る。
- docs / TODO の ja/en mirror に support scope と非対象が反映される。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k deque_copyindex`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`
- `git diff --check`

決定ログ:
- 2026-03-13: `clear()`、`extend()`、`reverse()`、`rotate()`、`count()`、`remove()` はすでに valid C++ に落ちるため、新 task は `copy` / `index` subset のみに限定した。

## 分解

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-COPYINDEX-01] `collections.deque.copy()` / `index()` representative C++ lane を固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-COPYINDEX-01-S1-01] current invalid C++ surface (`copy`, `index`) を focused regression / TODO / plan で固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-COPYINDEX-01-S2-01] `copy()` を valid な deque copy-construction surface に lower する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-COPYINDEX-01-S2-02] `index(value)` を search / distance surface に lower する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-COPYINDEX-01-S3-01] build/run smoke と support wording を同期して close する。

- 2026-03-13: `copy()` は single-evaluation lambda 内での explicit `::std::deque<T>(src)` copy-construction に lower し、`index(value)` は `std::find + iterator差分 + ValueError("deque.index missing value")` に統一した。
- 2026-03-13: representative build/run smoke は `r: deque[int] = q.copy()` の typed lane で `3 / 2 / 0` を固定した。plain local inference (`r = q.copy()`) は別 task へ分離する。
