# P0: homogeneous tuple ellipsis support

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-HOMOGENEOUS-TUPLE-ELLIPSIS-SUPPORT-01`

背景:
- Pytra-NES の representative case で `LENGTH_TABLE: tuple[int, ...] = (...)` のような homogeneous variadic tuple が現れている。
- 現状の C++ backend は `tuple[int, ...]` を fixed tuple と同じ lane で扱い、`::std::tuple<int64, ...>` のような不正な C++ 型を emit してしまう。
- `tuple[T, ...]` は fixed-arity tuple (`tuple[int, str]`) と意味が違い、型系と backend lowering で別 category として扱う必要がある。
- ただし v1 では full immutable-tuple semantics 全体を実装するのではなく、`homogeneous immutable sequence` として実用上通る representative lane を先に固定するのが現実的である。

目的:
- `tuple[T, ...]` を Pytra の入力型として正式に受理し、fixed tuple と区別できるようにする。
- v1 では `tuple[T, ...]` を mutation 禁止の homogeneous immutable sequence として扱い、representative constant / local / arg / return lane を主要 backend で通す。
- 未対応 backend や未対応 lane は fail-closed にして、不正コード生成を止める。

対象:
- type parser / type normalization における `tuple[T, ...]` 認識
- EAST / EAST3 / type summary の category 区別
- C++ backend の current invalid `::std::tuple<..., ...>` emission 修正
- representative backend における homogeneous variadic tuple lowering
- fail-closed contract / regression / docs

非対象:
- fixed tuple (`tuple[int, str]`) の再設計
- tuple full equality / hashing / slicing / concatenation の complete Python parity
- arbitrary nested tuple optimization の先回り実装
- tuple/list 共通 API の全面統一

受け入れ基準:
- `tuple[int, ...]` を含む representative fixture が frontend で受理されること。
- C++ backend が `::std::tuple<int64, ...>` のような不正型を emit しないこと。
- representative v1 lane（定数、ローカル変数、関数引数、戻り値、read-only index access）が target policy に従って emit できること。
- 未対応 backend / lane は silent fallback せず fail-closed で止まること。
- `python3 tools/check_todo_priority.py`、focused unit tests、`python3 tools/build_selfhost.py`、`git diff --check` が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k tuple`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: `tuple[T, ...]` は fixed tuple と同じ lane では扱わず、v1 では `homogeneous immutable sequence` category として切り出す方針にした。理由は current C++ emit が invalid `::std::tuple<..., ...>` になるためである。
- 2026-03-12: v1 は representative lane を先に固定し、未対応 backend / lane は fail-closed を優先する。全 backend で list と完全同一表現にするかは後段で再評価する。
- 2026-03-12: current parser は `tuple[int, ...]` を reject せず、`GenericType(base=\"tuple\", args=[NamedType(\"int64\"), NamedType(\"...\")])` として受理している。この baseline と current C++ invalid emit `::std::tuple<int64, ...>` を regression で固定してから category 分離へ進む。

## 分解

- [x] [ID: P0-HOMOGENEOUS-TUPLE-ELLIPSIS-SUPPORT-01-S1-01] type parser / normalization / representative failure を plan と regression で固定する。
- [ ] [ID: P0-HOMOGENEOUS-TUPLE-ELLIPSIS-SUPPORT-01-S2-01] `tuple[T, ...]` を fixed tuple と別 category として EAST / type summary に載せる。
- [ ] [ID: P0-HOMOGENEOUS-TUPLE-ELLIPSIS-SUPPORT-01-S2-02] C++ backend の invalid `::std::tuple<..., ...>` emission を止め、representative v1 lane を read-only immutable sequence として lower する。
- [ ] [ID: P0-HOMOGENEOUS-TUPLE-ELLIPSIS-SUPPORT-01-S3-01] representative backend policy を整理し、未対応 lane / backend を fail-closed で固定する。
- [ ] [ID: P0-HOMOGENEOUS-TUPLE-ELLIPSIS-SUPPORT-01-S3-02] docs / TODO / regression / inventory を current contract に同期して task を閉じる。
