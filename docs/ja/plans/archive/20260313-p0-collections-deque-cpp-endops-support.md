<a href="../../../en/plans/archive/20260313-p0-collections-deque-cpp-endops-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `collections.deque` appendleft / pop representative C++ support

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-COLLECTIONS-DEQUE-CPP-ENDOPS-01`

背景:
- `collections.deque` の representative C++ lane は、直前 task で `deque()` / `bool(q)` / `len(q)` / `append` / `popleft` まで `::std::deque<T>` lowering に揃った。
- ただし両端 queue operation の対になる `appendleft` / `pop` のうち、`appendleft` は `push_front` へ揃ったが、`pop` はまだ Python surface をそのまま C++ に漏らしている。
- current baseline では `appendleft` が `q.push_front(...)` に lower される一方、`pop` は `q.pop()` として出力され、`::std::deque<T>` に対する valid C++ になっていない。
- `clear()` はすでに `q.clear();` として valid C++ なので、この task は invalid surface が残る end-op gap だけに絞る。

目的:
- representative C++ lane で `collections.deque` の end-op subset を `::std::deque<T>` に揃える。
- 前 task と合わせて、queue/deque の最小実用 subset を `cpp` backend の current support contract として固定する。

対象:
- `from collections import deque`
- representative method subset: `appendleft`, `pop`
- typed / untyped 代入先に対する `pop()` の return surface
- focused regression / smoke / docs / TODO の同期

非対象:
- `deque` 全 API (`extendleft`, `rotate`, `maxlen`, iterator invalidation semantics など)
- 全 backend への同時 rollout
- `collections` module 全体の redesign
- C++ runtime に `PyDequeObj` のような新 object hierarchy を追加すること

受け入れ基準:
- focused regression で current invalid C++ surface が `pop` だけに narrowed された状態を固定する。
- representative C++ lane で `appendleft` は `push_front` に lower される。
- representative C++ lane で `pop` は `back + pop_back` 相当の lambda に lower される。
- typed / untyped どちらの `pop()` 受け側でも valid C++ surface を維持する。
- build/run smoke で representative fixture が通る。
- docs / TODO の ja/en mirror に support scope と非対象が反映される。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k deque`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`
- `git diff --check`

決定ログ:
- 2026-03-13: `appendleft` / `pop` は `deque` representative lane の残り invalid surface なので、新しい P0 として分離した。
- 2026-03-13: `clear()` は `std::deque` に対してそのまま valid C++ のため、この task から除外した。
- 2026-03-13: `S1-01` として `q.appendleft(1);` と `q.pop()` の surface leak を focused regression で固定した。`push_front` / `pop_back` へはまだ lower しない baseline として扱う。
- 2026-03-13: `S2-01` として `appendleft` は `push_front` へ lower 済みになったため、focused regression は `pop` leak だけを残す current state に更新した。
- 2026-03-13: `S2-02` として module-scope の typed deque でも `pop` fastpath が拾えるようにし、`back + pop_back` lambda へ揃えた。残りは build/run smoke のみ。
- 2026-03-13: `S3-01` として representative fixture の build/run smoke を追加し、typed/untyped `pop()` を含む end-op bundle の出力 `1 / 2` を固定した。これで task の受け入れ基準はすべて充足した。

## 分解

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ENDOPS-01] `collections.deque` の `appendleft` / `pop` representative C++ lane を固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ENDOPS-01-S1-01] current invalid C++ surface (`appendleft`, `pop`) を focused regression / TODO / plan で固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ENDOPS-01-S2-01] `appendleft` を `push_front` へ lower する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ENDOPS-01-S2-02] `pop` を `back + pop_back` lambda に lower し、typed / untyped return surface を揃える。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-ENDOPS-01-S3-01] build/run smoke と support wording を同期して close する。
