<a href="../../../en/plans/archive/20260312-p0-collections-deque-cpp-representative-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `collections.deque[T]` representative C++ support

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-COLLECTIONS-DEQUE-CPP-REPRESENTATIVE-01`

背景:
- Pytra-NES では `timestamps: deque[float] = field(init=False, repr=False)` のような dataclass field が実際に使われている。
- `field(...)` 自体の leak は既に解消済みだったが、baseline では C++ emitter が `deque[float64]` を raw type のまま出していた。
- Pytra の current user need は pure Python `collections.deque` の全面互換ではなく、Pytra-NES を進めるための representative C++ lane の固定である。

目的:
- `collections.deque[T]` を representative C++ lane で扱えるようにし、Pytra-NES の dataclass field / mutable queue use case を unblock する。
- `field(...)` task と切り分けて、今回は `deque[T]` 型 / ctor / member lane を current support contract として固定する。

対象:
- `from collections import deque`
- `deque[T]` type annotation の C++ type lowering
- representative dataclass field lane と zero-arg ctor lane
- focused regression / docs / TODO の同期

非対象:
- 全 backend への同時 rollout
- Python `deque` 完全互換（`maxlen` / rotate / rich API 全部）
- `collections` 全体の redesign
- runtime reflection 的な dataclass support

受け入れ基準:
- representative C++ regression で `deque[T]` raw type leak の baseline が固定される。
- `deque[T]` が representative C++ lane で `::std::deque<T>` に lower され、focused compile smoke が通る。
- plan / TODO の ja/en ミラーに Pytra-NES blocker と scope が記録される。
- 後続 bundle が `type lowering` と `zero-arg ctor/member lane` を順に進められる粒度になっている。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k deque`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core_parser_behavior_classes.py' -k deque`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: `dataclasses.field(...)` の静的 metadata 化は完了しているため、この task は `field` ではなく `deque[T]` type lowering / representative runtime lane に限定する。
- 2026-03-12: v1 は C++ representative lane のみを対象にし、non-C++ backend rollout は後段へ回す。
- 2026-03-12: baseline は `test_deque_annotation_current_baseline_still_leaks_raw_cpp_type` で固定し、current C++ emitter が `deque[float64]` を raw type のまま出していることを representative failure とする。
- 2026-03-12: `S2-01` では runtime alias を増やさず、C++ type lowering は `::std::deque<T>` 直 lowering とし、`py_types.h` / header builder に `<deque>` include を足す最小 bundle で通す。
- 2026-03-12: `S2-02` では plain class の general ctor policy には触れず、Pytra-NES blocker に直結する dataclass field lane に限定して `init=False` の zero-arg ctor と `default_factory=deque` の compile smoke を固定する。
- 2026-03-12: `S3-01` では C++ support wording を `partial` とし、`deque[T]` の representative contract は type lowering と dataclass field lane に限定、full `deque` API 互換は非対象として明記する。

## 分解

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REPRESENTATIVE-01] `collections.deque[T]` の representative C++ lane を固定し、Pytra-NES blocker を外す。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REPRESENTATIVE-01-S1-01] current baseline failure と representative scope を focused regression / TODO / plan で固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REPRESENTATIVE-01-S2-01] `deque[T]` の C++ type lowering を representative lane で固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REPRESENTATIVE-01-S2-02] zero-arg ctor / dataclass field member lane を representative C++ emission に揃える。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-REPRESENTATIVE-01-S3-01] docs / regression / support wording を current contract に同期して閉じる。
