<a href="../../ja/plans/archive/20260309-p0-cpp-pyruntime-register-class-bases-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-register-class-bases-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-register-class-bases-retirement.md`

# P0: C++ `py_runtime.h` `py_register_class_type(list<uint32>)` compat 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-REGISTER-BASES-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)

背景:
- `py_runtime.h` には pre-migration 互換として `py_register_class_type(const list<uint32>&)` が残っている。
- current design は単一継承のみで、generated source は単一 base 式を出す。
- compat overload が不要なら runtime core をさらに縮小できる。

目的:
- `py_register_class_type(list<uint32>)` compat overload を退役する。

非対象:
- `py_register_class_type(uint32)`
- class type-id boilerplate 自体の変更
- multiple inheritance の新規サポート

受け入れ基準:
- compat overload の checked-in callsite 有無が固定される。
- 必要なら representative generated source を単一 base 式へ寄せる。
- `py_runtime.h` から compat overload が消える。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_*.py' -k type_id`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## フェーズ

### Phase 1: 棚卸し
- checked-in callsite と generated source 依存を固定する。

### Phase 2: 置換
- 必要な callsite を単一 base 式へ寄せる。

### Phase 3: 退役
- compat overload を削除し、guard / docs / archive を更新する。

## タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-REGISTER-BASES-01] `py_register_class_type(list<uint32>)` compat を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-REGISTER-BASES-01-S1-01] checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-REGISTER-BASES-01-S1-02] 単一 base canonical rule を決定ログに固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-REGISTER-BASES-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-REGISTER-BASES-01-S2-02] regression / inventory guard を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-REGISTER-BASES-01-S3-01] `py_runtime.h` から compat overload を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-REGISTER-BASES-01-S3-02] parity / docs / archive を更新して閉じる。

## 決定ログ

- 2026-03-09: 本計画は pre-migration compat overload のみを対象とし、single inheritance contract は維持する。
- 2026-03-09: checked-in current C++ callsite は `py_register_class_type(uint32)` だけで、`py_register_class_type(const list<uint32>&)` の direct use は `src/runtime/cpp/native/core/py_runtime.h` の定義自身と selfhost の旧 artifact に限られていた。
- 2026-03-09: current design の canonical rule は単一 `uint32 base_type_id` であり、representative current source に置換対象は存在しないため `S2-01` は no-op とする。
- 2026-03-09: `test_cpp_runtime_iterable.py` に `py_register_class_type(const list<uint32>& bases)` の inventory guard を追加し、`src/runtime/cpp/native/core/py_runtime.h` から compat overload を削除した。
