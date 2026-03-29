<a href="../../../en/plans/archive/20260309-p0-cpp-pyruntime-optional-predicates-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `py_runtime.h` `optional` predicate sugar 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-OPTIONAL-PREDICATES-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)

背景:
- `py_runtime.h` には `py_is_dict/list/set/str/bool(const ::std::optional<T>&)` が残っている。
- これは `has_value()` を挟むだけの薄い sugar であり、callsite 側で明示分岐できる。
- runtime core の責務を減らす観点では後方互換 sugar に近い。

目的:
- `optional` predicate sugar を退役し、callsite 側の explicit branch を canonical にする。

非対象:
- `py_is_*` の本体
- `py_is_none(optional<T>)`
- type predicate semantics 自体の変更

受け入れ基準:
- `py_runtime.h` から `optional` predicate sugar が消える。
- checked-in callsite は `has_value()` 分岐へ置換される。
- representative regression と fixture parity が維持される。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 tools/unittest/emit/cpp/test_cpp_runtime_iterable.py`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root fixture`

## フェーズ

### Phase 1: 棚卸し
- checked-in callsite を固定する。

### Phase 2: 置換
- representative callsite を `has_value()` branch へ置換する。

### Phase 3: 退役
- sugar を削除し、guard / docs / archive を更新する。

## タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-PREDICATES-01] `optional` predicate sugar を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-PREDICATES-01-S1-01] checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-PREDICATES-01-S1-02] explicit branch rule を決定ログに固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-PREDICATES-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-PREDICATES-01-S2-02] regression / inventory guard を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-PREDICATES-01-S3-01] `py_runtime.h` から sugar を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-OPTIONAL-PREDICATES-01-S3-02] parity / docs / archive を更新して閉じる。

## 決定ログ

- 2026-03-09: 本計画は `optional` predicate sugar のみを扱い、`py_is_none(optional<T>)` は非対象とする。
- 2026-03-09: checked-in current source に `py_is_dict/list/set/str/bool(optional<T>)` の direct callsite は無く、置換フェーズは no-op として扱う。
- 2026-03-09: canonical rule は `if (v.has_value()) { py_is_*(*v) } else { false }` を callsite 側で明示する形とする。
