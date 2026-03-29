<a href="../../ja/plans/archive/20260309-p0-cpp-pyruntime-getattr-charptr-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-getattr-charptr-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-getattr-charptr-retirement.md`

# P0: C++ `py_runtime.h` `getattr(..., const char*)` sugar 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-GETATTR-CHARPTR-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)

背景:
- `py_runtime.h` には `getattr(const object&, const char*, ...)` が残っている。
- これは `str` overload への単純委譲であり、runtime core に置く必然性が薄い。
- callsite が `str("...")` を明示すれば表現できる。

目的:
- `getattr(..., const char*)` sugar を退役し、`str` key を canonical にする。

非対象:
- `getattr(const object&, const str&, ...)`
- `type_id` / `isinstance`
- dynamic attribute semantics 自体の変更

受け入れ基準:
- `py_runtime.h` から `getattr(..., const char*, ...)` が消える。
- checked-in callsite は `str(...)` key へ置換される。
- representative C++ regression と fixture parity が維持される。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 tools/unittest/emit/cpp/test_cpp_runtime_iterable.py`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root fixture`

## フェーズ

### Phase 1: 棚卸し
- checked-in callsite を固定する。

### Phase 2: 置換
- representative callsite を `str(...)` key へ置換する。

### Phase 3: 退役
- helper を削除し、guard / docs / archive を更新する。

## タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-GETATTR-CHARPTR-01] `getattr(..., const char*)` sugar を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-GETATTR-CHARPTR-01-S1-01] checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-GETATTR-CHARPTR-01-S1-02] `str(...)` key canonical rule を決定ログに固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-GETATTR-CHARPTR-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-GETATTR-CHARPTR-01-S2-02] regression / inventory guard を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-GETATTR-CHARPTR-01-S3-01] `py_runtime.h` から sugar を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-GETATTR-CHARPTR-01-S3-02] parity / docs / archive を更新して閉じる。

## 決定ログ

- 2026-03-09: 本計画は `getattr(..., const char*)` sugar だけを扱い、attribute lookup semantics 自体は非対象とする。
- 2026-03-09: checked-in C++ callsite は `src/runtime/cpp/generated/built_in/type_id.cpp` の `getattr(value, "PYTRA_TYPE_ID", ...)` 1 件だけで、他の literal-key `getattr` は Python/host code 側に限られていた。
- 2026-03-09: C++ checked-in code の canonical key rule は `str("...")` とし、`const char*` literal を runtime helper へ渡さない。
- 2026-03-09: representative callsite は `src/runtime/cpp/generated/built_in/type_id.cpp` の `_try_runtime_tagged_type_id` を `getattr(value, str("PYTRA_TYPE_ID"), ::std::nullopt)` に置換し、SoT の `src/pytra/built_in/type_id.py` も `str("PYTRA_TYPE_ID")` へ同期した。
- 2026-03-09: `test_cpp_runtime_iterable.py` に `getattr(const object&, const char*, ...)` signature の inventory guard と generated `type_id.cpp` の `str("PYTRA_TYPE_ID")` assertion を追加した。
- 2026-03-09: `src/runtime/cpp/native/core/py_runtime.h` から `getattr(const object&, const char*, ...)` sugar を削除し、verification は `test_cpp_runtime_iterable.py`, fixture parity `cases=3 pass=3 fail=0`, `check_todo_priority.py`, `git diff --check` を通した。
