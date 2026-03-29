<a href="../../../en/plans/archive/20260312-p2-relative-import-backend-coverage.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: relative import backend coverage contract

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-RELATIVE-IMPORT-BACKEND-COVERAGE-01`

背景:
- relative import 自体は frontend / import graph / CLI contract で既に supported になり、C++ は multi-file build/run smoke まで固定済み。
- ただし、この「どこまで lock 済みか」は backend 間で明文化されておらず、non-C++ backend が unsupported なのか unverified なのかが TODO / docs 上で見えにくい。
- Pytra-NES 型 project layout を次に他 backend へ広げるには、まず current coverage を support claim と混同しない形で inventory 化しておく必要がある。

目的:
- relative import の current verification coverage を backend 別に固定し、C++ だけが build/run lock 済みであること、他 backend は未検証 lane であることを明示する。
- 後続の non-C++ rollout task が attach できる baseline checker / docs handoff を整える。

対象:
- backend 別 relative import coverage inventory の正本追加
- checker / unit test の追加
- TODO / plan への staged rollout 順の記録

非対象:
- Rust / C# / 他 backend の relative import 実装追加
- support matrix 上で supported claim を増やすこと
- relative import semantics の再設計

受け入れ基準:
- canonical inventory が `cpp, rs, cs, go, java, js, kotlin, lua, nim, php, ruby, scala, swift, ts` を網羅する。
- `cpp` だけが `build_run_locked`、他 backend は `not_locked` として固定される。
- checker / unit test で coverage drift が fail-closed になる。

確認コマンド:
- `python3 tools/check/check_relative_import_backend_coverage.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`

決定ログ:
- 2026-03-12: relative import の immediate blocker は C++ multi-file runtime smoke で解消したので、次段は non-C++ rollout そのものではなく current coverage inventory を先に固定する。
- 2026-03-12: support matrix 側では relative import を support claim としては拡大せず、`cpp=build_run_locked` / `non-C++=not_locked` の verification coverage handoff として公開する。

## 分解

- [x] [ID: P2-RELATIVE-IMPORT-BACKEND-COVERAGE-01-S1-01] live plan / TODO と representative backend coverage taxonomy を固定する。
- [x] [ID: P2-RELATIVE-IMPORT-BACKEND-COVERAGE-01-S2-01] backend coverage inventory / checker / unit test を追加する。
- [x] [ID: P2-RELATIVE-IMPORT-BACKEND-COVERAGE-01-S2-02] docs / support-matrix handoff wording を current coverage baseline に同期した。
