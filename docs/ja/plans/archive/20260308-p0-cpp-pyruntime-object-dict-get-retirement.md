# P0: C++ `py_runtime.h` `py_dict_get(dict<str, object>)` 直取得 lane 退役

最終更新: 2026-03-08

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [archive/20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)

背景:
- `py_dict_get(const dict<str, object>&, ...)` は JSON decode helper 導入後も `py_runtime.h` に残っている。
- 例外メッセージ整形や caller address 採取まで抱えており、low-level runtime として過剰である。
- `JsonObj.get_*()` と decode-first が正本なら、direct object-dict getter は縮退できる。

目的:
- object-dict 直取得を `JsonObj` accessor または typed dict helper へ寄せ、`py_runtime.h` から外す。

非対象:
- generic `py_dict_get(dict<K, V>, ...)`
- `dict<str, str>` helper
- `JsonObj` API 設計そのもの

受け入れ基準:
- `py_dict_get(const dict<str, object>&, ...)` が `py_runtime.h` から消えるか、内部 private 相当に縮退する。
- `JsonObj.get_required` 相当の lane が正本になる。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_pylib_json.py' -v`

## 1. 方針

1. checked-in callsite を棚卸しし、JSON decode helper へ置換可能な経路を先に寄せる。
2. caller address 付き debug 例外は runtime core から追い出す。
3. typed dict helper は維持し、object-dict convenience だけを削る。

## 2. タスク分解

- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01] `py_dict_get(dict<str, object>, ...)` lane を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S1-01] direct getter の checked-in callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S1-02] `JsonObj` / typed dict への置換方針を決定する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S2-01] callsite を `JsonObj` accessor へ寄せる。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S2-02] `py_runtime.h` から direct getter を削除する。
- [x] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S3-01] regression / parity / docs を更新する。

## 3. 決定ログ

- 2026-03-08: object-dict 直取得は JSON convenience debt とみなし、generic dict helper とは別トラックで退役する。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S1-01]: checked-in callsite を棚卸しした結果、production で `dict<str, object>` 専用 `py_dict_get(const char*)` / `py_dict_get(const ::std::string&)` に依存していたのは runtime source 自身だけで、generated `std/json.cpp` の `JsonObj::get*` は `str` key で generic `py_dict_get(dict<str, V>, const str&)` に落ちていた。`argparse` と `type_id` は typed dict lane なので非対象に固定した。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S1-02]: `JsonObj` の required read は generated helper `_json_obj_require(raw, key)` を正本にし、`py_runtime.h` 側の object-dict special getter は debug caller-address 付き compat lane として全廃する方針で確定した。generic dict helper 全体の縮退は別トラックへ送る。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S2-01]: `src/pytra/std/json.py` に `_json_obj_require(raw, key)` を追加し、`JsonObj.get/get_obj/get_arr/get_str/get_int/get_float/get_bool` を membership check 後に同 helper で値取得する形へ寄せた。checked-in generated runtime `src/runtime/cpp/generated/std/json.{h,cpp}` と public shim も再生成し、`py_dict_get(this->raw, key)` を runtime helper から追い出した。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S2-02]: `src/runtime/cpp/native/core/py_runtime.h` から `py_dict_get(const dict<str, object>&, const char*)` と `py_dict_get(const dict<str, object>&, const ::std::string&)` を削除した。`test_cpp_runtime_iterable.py` には removed inventory guard を追加し、`test_py2cpp_features.py` では `_json_obj_require` と `make_object(_json_obj_require(...))` が生成されることを固定した。
- 2026-03-08 [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S3-01]: verification は `test_py2cpp_features.py -k json`, `test_cpp_runtime_iterable.py`, `test_pylib_json.py`, fixture parity `cases=3 pass=3 fail=0` を通した。この tranche の変更点は JSON runtime helper と object-dict special getter に限られるため、least-surface regression と fixture parity を release gate とした。
