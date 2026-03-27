<a href="../../../en/plans/archive/20260313-p0-collections-deque-cpp-expr-method-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `collections.deque` expression / method representative C++ support

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-COLLECTIONS-DEQUE-CPP-EXPR-METHOD-01`

背景:
- `deque[T]` の type annotation と dataclass field lane は representative C++ contract として既に固定済みで、Pytra-NES の `timestamps: deque[float] = field(init=False, repr=False)` 自体は unblock 済み。
- ただし plain expression / method lane はまだ Python surface をそのまま C++ へ漏らしている。
- current baseline では `deque()` が `q = deque();`、`append` が `q.append(1);`、`popleft` が `q.popleft();`、truthiness が `py_to<bool>(q)`、`len` が `py_len(q)` として出ており、`::std::deque<T>` に対する valid C++ になっていない。
- Pytra-NES の次の実用 blocker は queue operation であり、`deque` API 全面互換ではなく representative subset を先に固定するのが妥当。

目的:
- representative C++ lane で `collections.deque` の expression / method surface を有効な `::std::deque<T>` lowering に揃える。
- Pytra-NES で使いがちな queue operation の first-pass subset を current support contract に固定する。

対象:
- `from collections import deque`
- zero-arg `deque()` expression
- representative method subset: `append`, `popleft`
- representative utility subset: `len(deque)`, truthiness
- focused regression / docs / TODO の同期

非対象:
- `deque` 全 API (`appendleft`, `extend`, `rotate`, `maxlen`, iterator invalidation semantics など)
- 全 backend への同時 rollout
- `collections` module 全体の redesign
- C++ runtime に `PyDequeObj` のような新 object hierarchy を追加すること

受け入れ基準:
- baseline regression で current invalid C++ surface (`deque()`, `.append`, `.popleft`, `py_to<bool>(deque)`, `py_len(deque)`) を固定する。
- representative C++ lane で `deque()` が `::std::deque<T>{}` に lower される。
- representative C++ lane で `append` は `push_back`、`popleft` は `front + pop_front` 相当へ lower される。
- representative C++ lane で `len(deque)` と truthiness が valid C++ (`.size()`, `!empty()`) に lower される。
- build/run smoke で representative fixture が通る。
- docs / TODO の ja/en ミラーに support scope と非対象が反映される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k deque`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-13: `dataclasses.field(...)` と `deque[T]` annotation lane は close 済みのため、新 task は queue operation の representative subset に限定する。
- 2026-03-13: first-pass subset は Pytra-NES の queue need に合わせて `deque()`, `append`, `popleft`, `len`, truthiness の 5 要素に絞る。`appendleft` 以降は後段に回す。
- 2026-03-13: baseline は compile failure を直接固定せず、C++ source に Python surface が漏れていることを regression で固定する。compiler error text 依存を避けるため。
- 2026-03-13: `S1-01` として `q = deque();`, `q.append(1);`, `q.popleft();`, `py_to<bool>(q)`, `py_len(q)` を focused regression で固定した。
- 2026-03-13: `S2-01` として `deque()` を `::std::deque<T>{}`、`bool(q)` を `!q.empty()`、`len(q)` を `q.size()` へ upstream した。残る Python surface leak は `append` / `popleft` に限定された。
- 2026-03-13: `popleft()` は既存の attr-call lowering ですでに `front + pop_front` lambda に落ちていたため、`S2-01` の regression 更新後の残件は `append` のみになった。
- 2026-03-13: `S2-02` として typed `deque[T]` の `append` を `push_back` へ upstream した。representative lowering は `deque()` / `bool(q)` / `len(q)` / `append` / `popleft` の 5 要素で揃い、残りは build/run smoke と support wording だけになった。
- 2026-03-13: `S3-01` として representative fixture の build/run smoke を追加し、`False / 0 / 1` の出力を固定した。これで task の受け入れ基準はすべて充足した。

## 分解

- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-EXPR-METHOD-01] `collections.deque` representative C++ expression / method lane を固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-EXPR-METHOD-01-S1-01] current invalid C++ surface を focused regression / TODO / plan で固定する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-EXPR-METHOD-01-S2-01] `deque()` expression と `len/truthiness` を representative C++ lowering に揃える。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-EXPR-METHOD-01-S2-02] `append` method subset を representative C++ lowering に揃え、`popleft` representative lane の regression を維持する。
- [x] [ID: P0-COLLECTIONS-DEQUE-CPP-EXPR-METHOD-01-S3-01] build/run smoke と support wording を同期して close する。
