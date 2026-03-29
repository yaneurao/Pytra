<a href="../../../en/plans/archive/20260313-p0-pytra-nes-cpp-mini-repro-contract.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: Pytra-NES representative C++ mini repro contract

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PYTRA-NES-CPP-MINI-REPRO-01`

背景:
- Pytra-NES チームから、最初に当たる blocker として `from .controller import (...)` の括弧付き sibling relative import と、`timestamps: deque[float] = field(init=False, repr=False)` を含む class 定義が共有されている。
- これらの surface は個別にはすでに C++ representative lane で smoke / regression があるが、「同じ multi-file package 内で同時に使う」 representative contract はまだ固定されていない。
- 実運用側では、relative import / dataclass field metadata / `collections.deque` lowering の 3 本が一緒に触れるため、個別 regression だけでは再発を防ぎにくい。

目的:
- Pytra-NES の representative な最小 package を 1 本定義し、C++ multi-file lane で transpile / build / run まで固定する。
- `controller.py` / `pad_state.py` / `ppu.py` のような sibling package 構成で、括弧付き relative import、`dataclass`、`deque[float]` field、`deque.append/popleft/len` が一緒に使えることを lock する。
- `field(...)` が generated C++ に漏れないこと、`deque[float]` が `::std::deque<float64>` に lower されることを representative smoke に含める。

対象:
- `tools/unittest/emit/cpp/test_py2cpp_features.py`
- 必要なら C++ emitter / runtime の representative drift guard
- TODO / plan / support docs

非対象:
- non-C++ backend への同時展開
- NES エミュレータ全体の fixture 化
- `dataclass` 全互換や `deque` 全 API の網羅

受け入れ基準:
- `controller.py` / `pad_state.py` / `ppu.py` の 3 module package が C++ multi-file lane で transpile / build / run まで通る。
- generated `pad_state.h` に `::std::deque<float64> timestamps;` が出る。
- generated `ppu.cpp` に sibling include、`append -> push_back`、`popleft -> front()+pop_front()`、`len(...) -> .size()` の lowering guard が残る。
- generated output に `field(` が漏れない。
- representative runtime output が固定される。

確認コマンド:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src:/workspace/Pytra/tools/unittest/backends python3 tools/unittest/emit/cpp/test_py2cpp_features.py -k pytra_nes`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`

分解:
- [x] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01] Pytra-NES の representative な multi-file package（括弧付き sibling relative import + `dataclass` + `deque[float]` field + `deque` method）を C++ representative lane で build/run まで固定する。
- [x] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01-S1-01] representative package smoke を追加し、`from .controller import (...)` と `timestamps: deque[float] = field(init=False, repr=False)` を併用する C++ multi-file build/run baseline を固定した。
- [x] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01-S2-01] smoke で露出した generated include / class layout / method lowering の drift を source guard 化し、Pytra-NES representative lane の regression を fail-fast にする。
- [x] [ID: P0-PYTRA-NES-CPP-MINI-REPRO-01-S3-01] TODO / plan / support docs を representative Pytra-NES mini repro contract に同期し、close する。

決定ログ:
- 2026-03-13: Pytra-NES 側の現物コード片に合わせ、representative contract は `controller.py` / `pad_state.py` / `ppu.py` の 3 module package で固定する。個別 feature regression の再利用ではなく、「一緒に使う」こと自体を smoke 化する。
- 2026-03-13: `S2-01` では generated source guard を compile/run smoke の中へ畳み込み、`controller.h` / `pad_state.h` include、`::std::deque<float64>` field、`append -> push_back(float64(...))`、`popleft -> front()+pop_front()`、`len(...) -> (deque).size()` を drift guard として固定した。旧 `py_list_append_mut(...)` / `obj_to_list_ref_or_raise(...)` / raw `.popleft()` 呼び出しは再発させない。
- 2026-03-13: `S3-01` では C++ support docs の `collections.deque[T]` representative wording を Pytra-NES multi-file package smoke に同期し、この task 自体を archive へ移す close-out とした。
