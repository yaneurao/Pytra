<a href="../../../en/plans/archive/20260308-p0-cpp-pyruntime-dict-get-maybe-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `py_runtime.h` `py_dict_get_maybe` 退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)

背景:
- `py_dict_get_maybe` は Python の `dict.get(key)` 省略形を C++ runtime convenience として広く持っている。
- decode-first 方針では `JsonObj.get_optional` 系か typed `dict.get` lowering を正本にしたい。
- `optional<dict<...>>` や `dict<str, object>` ごとの overload 増殖は `py_runtime.h` を不必要に太らせる。

目的:
- `py_dict_get_maybe` を runtime core の汎用 convenience から外し、JSON / typed dict 側へ寄せる。

非対象:
- explicit default 付き `py_dict_get_default`
- generic dict primitive そのもの

受け入れ基準:
- `py_dict_get_maybe` 系 overload が大幅に減る。
- JSON / selfhost loader は `JsonObj` helper または explicit default へ移行する。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/link -p 'test_*.py' -v`

## 1. 方針

1. `maybe` semantics が本当に必要な callsite を固定する。
2. JSON は `JsonObj.get_*`、typed dict は explicit default / exception へ寄せる。
3. generic dict primitive を壊さず convenience だけを落とす。

## 2. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01] `py_dict_get_maybe` convenience を縮退する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S1-01] `py_dict_get_maybe` callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S1-02] `JsonObj` / explicit default への移行方針を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S2-01] representative callsite を置換する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S2-02] `py_dict_get_maybe` overload を削減する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S3-01] guard / docs / parity を更新する。

## 3. 決定ログ

- 2026-03-08: `maybe` convenience は typed dict primitive ではなく decode helper の都合で残っている debt として扱う。
- 2026-03-08: checked-in production callsite は見つからず、残っているのは `CppEmitter` の `DictGetMaybe` lowering と `test_east3_cpp_bridge.py` の expectation だけだった。typed `dict.get(key)` は runtime convenience ではなく、C++ 側で `contains/at + optional` の式展開へ寄せる。
- 2026-03-08: `CppEmitter` の `DictGetMaybe` は `([&]() -> optional<T> { auto&& __dict = ...; auto __key = ...; return contains ? optional<T>(at) : nullopt; }())` へ置換し、`py_runtime.h` から `py_dict_get_maybe` block 全体を削除した。inventory guard は generic / `optional<dict<...>>` overload の再侵入を `NotIn` で固定する。
