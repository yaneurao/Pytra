<a href="../../ja/plans/archive/20260309-p0-cpp-pyruntime-typed-list-from-object-retirement.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-typed-list-from-object-retirement.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/archive/20260309-p0-cpp-pyruntime-typed-list-from-object-retirement.md`

# P0: C++ `py_runtime.h` typed-list-from-object helper 縮退

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-TYPEDLISTFROMOBJECT-01`

関連:
- [spec-runtime.md](../spec/spec-runtime.md)
- [spec-dev.md](../spec/spec-dev.md)
- [archive/20260308-p1-jsonvalue-decode-first-contract.md](./archive/20260308-p1-jsonvalue-decode-first-contract.md)
- [archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md](./archive/20260308-p2-jsonvalue-selfhost-decode-alignment.md)

背景:
- `py_runtime.h` には `py_copy_typed_list_from_object`, `py_to_typed_list_from_object`, `obj_to_rc_list`, `obj_to_rc_list_or_raise` が残っている。
- これらは `object -> typed list` の convenience lane であり、JSON / selfhost / runtime helper が raw `object` list をまだ使っていた時期の名残である。
- decode-first / nominal JSON / typed helper の方針では、汎用 helper として常駐させるより callsite を限定して縮退した方がよい。

目的:
- `object` から typed list への変換 helper を棚卸しし、削除できるものは削除、残すものも最小 surface に縮退する。

非対象:
- `make_object(list<T>)`
- `py_to<T>(object)` 本体
- low-level `PyListObj` / `object` carrier の廃止

受け入れ基準:
- `py_copy_typed_list_from_object` / `py_to_typed_list_from_object` / `obj_to_rc_list` / `obj_to_rc_list_or_raise` のうち不要な helper が削除されるか、private 相当まで縮退する。
- JSON / selfhost / runtime helper の representative path が nominal / typed lane で成立する。
- C++ fixture parity が維持される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/common -p 'test_pylib_json.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/link -p 'test_*.py' -v`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`

## 1. 方針

1. 先に checked-in callsite を棚卸しし、JSON / selfhost / runtime helper のどこがまだ `object -> typed list` helper に依存しているかを固定する。
2. generated helper や `JsonArr` nominal API へ寄せられる callsite から置換し、汎用 helper を段階的に縮退する。
3. `py_to<T>(object)` をそのまま薄い wrapper で再輸出するような代替 convenience は増やさない。

## 2. フェーズ

### Phase 1: 棚卸し
- 4 helper の checked-in callsite と到達経路を固定する。

### Phase 2: 置換
- JSON / selfhost / representative runtime helper を typed / nominal lane へ寄せる。

### Phase 3: 縮退
- helper を削除または private 化し、inventory guard と parity を更新する。

## 3. タスク分解

- [ ] [ID: P0-CPP-PYRUNTIME-TYPEDLISTFROMOBJECT-01] typed-list-from-object helper を縮退する。
- [ ] [ID: P0-CPP-PYRUNTIME-TYPEDLISTFROMOBJECT-01-S1-01] `py_copy_typed_list_from_object` / `py_to_typed_list_from_object` / `obj_to_rc_list` / `obj_to_rc_list_or_raise` の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-TYPEDLISTFROMOBJECT-01-S1-02] 削除順序と暫定的に残す helper を決定ログに固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-TYPEDLISTFROMOBJECT-01-S2-01] representative callsite を typed / nominal lane へ置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-TYPEDLISTFROMOBJECT-01-S2-02] regression / inventory guard を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-TYPEDLISTFROMOBJECT-01-S3-01] 不要 helper を削除または private 相当に縮退する。
- [ ] [ID: P0-CPP-PYRUNTIME-TYPEDLISTFROMOBJECT-01-S3-02] parity / docs / archive を更新して閉じる。

## 4. 決定ログ

- 2026-03-09: 本計画は汎用 convenience の縮退を扱い、`object` carrier 本体や `py_to<T>(object)` の core semantics は対象外とする。
- 2026-03-09: checked-in callsite 棚卸しでは `py_to_typed_list_from_object` は `py_to<T>(object)` の list special-case からのみ使われ、`obj_to_rc_list_or_raise` の direct callsite は存在しなかった。`obj_to_rc_list` は `py_to<T>(object)` と `py_object_try_cast<D>` の rc-list branch で使われ、`py_copy_typed_list_from_object` はその core conversion として残す。
- 2026-03-09: 第1 tranche は thin wrapper の `py_to_typed_list_from_object` と `obj_to_rc_list_or_raise` を削除し、`py_copy_typed_list_from_object` / `obj_to_rc_list` は internal core として当面維持する。`JsonArr` raw carrier の解消までは `py_to<T>(object)` の typed list branch 自体は non-goal とする。
