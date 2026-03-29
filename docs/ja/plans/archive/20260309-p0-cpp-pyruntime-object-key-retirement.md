<a href="../../../en/plans/archive/20260309-p0-cpp-pyruntime-object-key-retirement.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ `py_runtime.h` `dict<str, V>` への `object` key compat 退役

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-OBJECT-KEY-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [archive/20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)

背景:
- [py_runtime.h](../../src/runtime/cpp/native/core/py_runtime.h) には `py_dict_get(const dict<str, V>&, const object& key)` が残っている。
- この helper は `object` key を `str(key)` へ落として辞書参照する compat lane であり、decode-first 方針と逆向きである。
- 現在の compiler/runtime 方針では、`object` をそのまま built-in / collection helper に渡さず、先に decode してから使うのが正本である。
- したがって `dict<str, V>` の key も `str` に decode 済みであるべきで、`object` key compat は縮退候補である。

目的:
- `py_dict_get(dict<str, V>, object)` の checked-in callsite を棚卸しし、`str` key へ明示 decode した上で参照する形へ置換する。
- helper 自体を `py_runtime.h` から削除する。

対象:
- `src/runtime/cpp/native/core/py_runtime.h` の `py_dict_get(..., const object&)`
- emitter / generated runtime / selfhost artifact の checked-in callsite

非対象:
- `dict<str, V>` の `char*` / `str` / `std::string` key overload
- `object` value 側の decode helper

受け入れ基準:
- `py_dict_get(..., object)` の checked-in callsite が棚卸しされている。
- representative callsite が `str` key 前提へ置換されている。
- helper が削除され、inventory guard で再侵入を止めている。

確認コマンド:
- `PYTHONPATH=src python3 tools/unittest/emit/cpp/test_cpp_runtime_iterable.py`
- `PYTHONPATH=src python3 tools/unittest/emit/cpp/test_py2cpp_codegen_issues.py`
- `PYTHONPATH=src python3 tools/unittest/emit/cpp/test_pylib_json.py`
- `python3 tools/check/runtime_parity_check.py --targets cpp --case-root fixture`

## フェーズ

### Phase 1: 棚卸し

- `rg 'py_dict_get\\(.*object'` 等で checked-in callsite を特定する。
- `JsonObj` 経路と generic emitter 経路を分離して記録する。

### Phase 2: callsite 置換

- key を `str` に decode 済みの local に受けるか、`str(...)` を明示した call へ置換する。
- representative codegen expectation を更新する。

### Phase 3: helper 削除

- `py_runtime.h` から `object` key overload を削除する。
- inventory guard / parity / docs を更新する。

## タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-KEY-01] `dict<str, V>` への `object` key compat を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-KEY-01-S1-01] `py_dict_get(..., object)` の checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-KEY-01-S1-02] `str` key への置換方針を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-KEY-01-S2-01] representative callsite を置換する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-KEY-01-S2-02] helper を削除し inventory guard を更新する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-KEY-01-S3-01] parity / docs / archive を同期する。

## 決定ログ

- 2026-03-09: 起票時点で `dict<str, V>` key の current canonical lane は `char*` / `str` / `std::string` であり、`object` key overload だけを compat lane とみなす。今回は key 側だけを対象にし、value decode や `dict_get_default` の generic fallback は別タスクへ分離する。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-OBJECT-KEY-01-S1-01]: current source の checked-in callsite を洗うと、`src/runtime/cpp/generated/std/argparse.cpp` は `str tok` をそのまま使っており、C++ emitter も `dict[str, V]` では `_coerce_dict_key_expr(...)` により `py_to_string(...)` か verified `str` へ寄せていた。`py_dict_get(dict<str, V>, object)` の直接利用は `src/runtime/cpp/native/core/py_runtime.h` 自身だけで、compat lane は未使用と確定した。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-OBJECT-KEY-01-S1-02]: `dict[str, V]` key の canonical lane は `char*` / `str` / `std::string` のまま維持し、非 verified key は emitter 側で必ず `py_to_string(...)` へ落とす方針に固定した。runtime 側で `object -> str` を吸う convenience は持たない。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-OBJECT-KEY-01-S2-01]: representative replacement は emitter regression で固定した。`test_coerce_dict_key_expr_coerces_object_key_to_py_to_string` を追加し、`dict[str, V]` に `object` key が来ても callsite で `py_to_string(k)` へ正規化されることを確認した。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-OBJECT-KEY-01-S2-02]: `src/runtime/cpp/native/core/py_runtime.h` から `template <class V> py_dict_get(const dict<str, V>&, const object&)` を削除し、`test_cpp_runtime_iterable.py` に inventory guard を追加した。current source で helper 直接 callsite が無いことを前提に削除している。
- 2026-03-09 [ID: P0-CPP-PYRUNTIME-OBJECT-KEY-01-S3-01]: verification は `test_east3_cpp_bridge.py`、`test_cpp_runtime_iterable.py`、fixture parity `cases=3 pass=3 fail=0` を通した。full sample parity は本 tranche の受け入れ基準では要求せず、fixture gate を正本にした。
