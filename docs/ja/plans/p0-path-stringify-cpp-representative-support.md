# P0: `str(Path(...))` representative C++ stringify support

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01`

背景:
- Pytra-NES の minimal sample [`materials/refs/from-Pytra-NES/path_stringify.py`](../../../materials/refs/from-Pytra-NES/path_stringify.py) は `path = Path(raw); return str(path)` を使う。
- 現状の representative C++ lane では `str(path)` が generic `py_to_string(path)` に lower され、`std::ostringstream << Path` を要求して compile failure になる。
- `Path(raw)` 自体の construction は compile しているため、本質は `Path` 専用 stringify lane が generic fallback に落ちていることにある。

目的:
- representative C++ lane で `str(Path(...))` を正しい stringify path に lower し、Pytra-NES blocker を外す。
- `Path` を generic `ostream << T` fallback に流さない contract を focused regression で固定する。

対象:
- `str(Path(...))` representative C++ lowering
- `Path` 文字列化の helper / method dispatch
- focused regression / docs / TODO の同期

非対象:
- `Path` API 全体の redesign
- all backend 同時 rollout
- arbitrary user-defined class の `str()` policy
- `repr(Path)` や path normalization redesign

受け入れ基準:
- minimal sample `path_stringify.py` の current compile failure が focused regression で固定される。
- representative C++ lane で `str(Path(...))` が `Path` 専用 stringify lane へ lower され、compile smoke が通る。
- generic `py_to_string(T)` fallback に `Path` が戻らないことが regression で固定される。
- current support wording が plan / TODO に同期される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k path_stringify`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -k py_to_string`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: `Path(raw)` construction は current representative lane で compile しているため、本 task は `str(Path(...))` 専用 stringify path に絞る。
- 2026-03-12: v1 は `Path` の representative stringify に限定し、user-defined class の generic `str()` policy は別 task とする。

## 分解

- [ ] [ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01] `str(Path(...))` の representative C++ stringify lane を固定し、Pytra-NES blocker を外す。
- [ ] [ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01-S1-01] minimal sample baseline と current compile failure を focused regression / TODO / plan に固定する。
- [ ] [ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01-S2-01] representative C++ lane で `Path` 専用 stringify lowering を実装する。
- [ ] [ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01-S3-01] docs / support wording / regression を current contract に同期して閉じる。
