<a href="../../../en/plans/archive/20260308-p0-cpp-pyruntime-object-dict-default-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `py_runtime.h` `dict<str, object>` 専用 `py_dict_get_default` 縮退

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [archive/20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)

背景:
- `dict<str, object>` 専用 `py_dict_get_default` は `object`, `char*`, `str`, `dict<str, object>`, template default まで広がっている。
- `JsonObj.get_*()` が進むほど、これらは JSON convenience debt になる。

目的:
- object-dict 専用 default access を `JsonObj` decode helper に寄せ、runtime 本体から減らす。

非対象:
- generic `dict<K, V>` primitive
- typed `dict<str, V>` default access

受け入れ基準:
- `dict<str, object>` 専用 `py_dict_get_default` の多くが削除される。
- JSON decode は `JsonObj.get_*` で成立する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_pylib_json.py' -v`

## 1. 方針

1. JSON decode helper へ寄せられるものを優先して削る。
2. `object` default を返す helper を permanent API と見なさない。
3. どうしても残るなら `JsonObj` private/helper 側へ寄せる。

## 2. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01] `dict<str, object>` 専用 `py_dict_get_default` を縮退する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S1-01] object-dict default access の callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S1-02] `JsonObj.get_*` へ寄せる順序を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S2-01] representative callsite を `JsonObj` helper へ移す。
- [x] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S2-02] object-dict default overload を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S3-01] regression / parity / docs を更新する。

## 3. 決定ログ

- 2026-03-08: object-dict default access は generic dict primitive とは別 debt として管理する。
- 2026-03-08: checked-in callsite を棚卸しした結果、current production path で `dict<str, object>` 専用 `py_dict_get_default(...)` を直接使っているのは `CppEmitter._render_dict_get_default_expr()` の objectish lane と `dict_get_bool/str/int/float/list/node` だけだった。`JsonObj` generated helper 自身は `_json_obj_require(...)` と `JsonObj.get_*()` に寄せ始めており、selfhost artifact の direct use は `tgt/id/attr/source_span` など decode-first 未移行領域に限られていた。
- 2026-03-08: 削除順序は `(1) JSON / representative object-dict callsite を `JsonObj.get_*()` または `dict_get_*` へ寄せる -> (2) plain `py_dict_get_default(dict<str, object>, ..., object/char*/str/dict<str, object>)` overload を削る -> (3) 最後に template<class D> generic object-dict default wrapper を dict_get convenience と一緒に別トラックで縮退する` に固定する。本計画では `dict_get_*` と `dict_get_node` 自体は残し、まず direct object-dict default lane だけを落とす。
- 2026-03-08: representative callsite は generated `std/json` の `JsonObj.get_*()` ではすでに `_json_obj_require(...)` へ寄っていたため、runtime 本体側の representative として `dict_get_bool/str/int/float/list` を `find(str(key)) -> it->second` 直実装へ移した。これで `dict<str, object>` 専用の plain `py_dict_get_default(..., object/char*/str/dict<str, object>)` に依存する checked-in production path はなくなった。
- 2026-03-08: `src/runtime/cpp/native/core/py_runtime.h` から `dict<str, object>` 専用 `py_dict_get_default(..., object/char*/str/dict<str, object>)` overload 一式を削除し、template `<class D>` wrapper のみ残した。removed inventory guard は `test_cpp_runtime_iterable.py` に追加し、representative verification は `test_cpp_runtime_iterable.py`、`test_pylib_json.py`、`test_py2cpp_features.py -k json`、fixture parity `cases=3 pass=3 fail=0` を通した。
