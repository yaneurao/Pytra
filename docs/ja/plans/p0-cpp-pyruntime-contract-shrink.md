# P0: C++ `py_runtime.h` 契約縮小（object bridge / type_id shared contract の整理）

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01`

背景:
- `src/runtime/cpp/native/core/py_runtime.h` は transitive include 整理と typed dict helper 撤去が進み、以前より縮小可能になっている。
- ただし残りの bulk は header 内の単純な無駄ではなく、`object` bridge mutation helper と `type_id` shared contract に集中している。
- `py_append/py_extend/py_pop/py_clear/py_reverse/py_sort/py_set_at` は typed C++ lane ではかなり upstream 済みだが、C++ object fallback・generated runtime・C# runtime mirror がまだ前提にしている。
- `py_runtime_type_id/py_isinstance/py_is_subtype` は generated `type_id` built-in、native compiler wrapper、Rust/C# runtime/emitter が共有契約として参照しており、ownership を整理しないまま header だけ削ると drift を招く。

目的:
- `py_runtime.h` から「typed lane では不要だが shared compatibility の都合で残っている surface」を切り離し、他言語 runtime 実装者が背負う負担を減らす。
- mutation helper を object bridge 専用 surface へ縮める。
- `type_id` shared contract の ownership を generated / shared helper 側へ寄せ、`py_runtime.h` を thin compatibility seam へ縮退させる。

対象:
- `src/runtime/cpp/native/core/py_runtime.h`
- `src/backends/cpp/emitter/call.py`
- `src/backends/cpp/emitter/cpp_emitter.py`
- `src/runtime/cpp/generated/built_in/type_id.cpp`
- `src/runtime/cpp/native/compiler/transpile_cli.cpp`
- `src/runtime/cpp/native/compiler/backend_registry_static.cpp`
- `src/runtime/rs/pytra-core/built_in/py_runtime.rs`
- `src/runtime/cs/pytra-core/built_in/py_runtime.cs`
- `src/backends/rs/emitter/rs_emitter.py`
- `src/backends/cs/emitter/cs_emitter.py`
- `test/unit/backends/cpp/test_cpp_runtime_iterable.py`
- `test/unit/backends/cpp/test_cpp_runtime_type_id.py`
- `test/unit/backends/cpp/test_py2cpp_codegen_issues.py`
- `test/unit/backends/cpp/test_east3_cpp_bridge.py`
- 必要に応じて `test/unit/backends/rs/test_py2rs_smoke.py` / `test/unit/backends/cs/test_py2cs_smoke.py`

非対象:
- `py_runtime.h` の物理分割だけで行数を見かけ上減らすこと。
- `Any/object` 境界そのものの廃止。
- Rust/C#/C++ runtime の `type_id` 契約を一気に pure-Python generated 正本へ全面移行すること。
- nominal ADT や `JsonValue` の仕様拡張。

受け入れ基準:
- `py_runtime.h` の mutation helper は `typed C++ lane` 用 surface ではなく `object bridge / compatibility` 用 surface に縮退している。
- `py_runtime_type_id/py_isinstance/py_is_subtype` の ownership 境界が docs と test で固定され、`py_runtime.h` が shared policy の唯一正本ではなくなる。
- C++ emitter の typed lane で `py_append/py_extend/py_pop/py_clear/py_reverse/py_sort/py_set_at` への不要依存が再流入しない。
- residual caller は `typed_lane_removable` / `object_bridge_required` / `shared_runtime_contract` のいずれかに分類され、未分類の再流入を test/tooling で落とせる。
- `test_cpp_runtime_iterable.py`、`test_cpp_runtime_type_id.py`、`test_east3_cpp_bridge.py`、`test_py2cpp_codegen_issues.py`、必要な Rust/C# smoke、`build_selfhost.py` が通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_type_id.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/rs -p 'test_py2rs_smoke.py' -k type_id`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cs -p 'test_py2cs_smoke.py' -k type_id`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

分解:
- [x] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S1-01] 残る mutation helper / `type_id` caller を `typed_lane_removable` / `object_bridge_required` / `shared_runtime_contract` に棚卸しし、残存理由を固定する。
- [x] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S1-02] `py_runtime.h` の target end state を固定し、`mutation helper` と `type_id` の削減順を docs / source guard へ反映する。
- [x] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S2-01] C++ emitter の typed lane から残っている `py_append/extend/pop/clear/reverse/sort/set_at` 依存を bundle 単位で upstream へ押し戻す。
- [x] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S2-02] `py_runtime.h` の mutation helper を object bridge / compatibility 専用 overload へ縮め、残存 caller を label 付きで固定する。
- [x] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S3-01] `py_runtime_type_id/py_isinstance/py_is_subtype` の shared ownership を整理し、native compiler wrapper / generated `type_id` built-in の参照先を thin helper seam に寄せる。
- [ ] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S3-02] Rust/C#/C++ runtime/emitter の residual `type_id` caller を shared contract 前提へ揃え、未分類の再流入を smoke/contract test で落とす。
- [ ] [ID: P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01-S4-01] `py_runtime.h` 残存 surface の label check / source guard / docs を更新し、archive 可能な状態にする。

決定ログ:
- 2026-03-11: `py_runtime.h` は transitive include 整理と typed dict / typed mutation upstream 後の段階に入り、残タスクの本丸は `mutation helper` と `type_id` shared contract の 2 本柱と整理した。
- 2026-03-11: このタスクでは header の物理分割を目的にせず、他言語 runtime 実装者の負担軽減につながる契約縮小のみを対象にする。
- 2026-03-11: `S1` は実装前提の棚卸しと target end state 固定に限定し、helper 単位の小分けではなく bundle 単位で進める。
- 2026-03-11: `S1-01` として `tools/check_cpp_pyruntime_contract_inventory.py` を追加し、残る `symbol × path` caller を `typed_lane_removable` / `object_bridge_required` / `shared_runtime_contract` の 3 bucket で固定した。native compiler wrapper と generated `json/type_id`、C++ emitter mutation lane の残存理由を未分類再流入なしで監視する。
- 2026-03-11: `S1-02` として `test_cpp_runtime_iterable.py` と `test_check_cpp_pyruntime_contract_inventory.py` を拡張し、mutation helper の end state を `typed=container overload / compat=object overload`、`type_id` の end state を `py_tid_*` delegate + generated `type_id.h` include に固定した。
- 2026-03-11: `S2-01` として C++ emitter / stmt から `py_append/extend/pop/clear/reverse/sort/set_at` wrapper 呼び出しを हटし、user-emitted C++ は `py_list_*_mut(obj_to_list_ref_or_raise(...))` へ直接 lower する形に寄せた。これで `typed_lane_removable` bucket は空になり、残 caller は generated runtime と shared `type_id` contract のみになった。
- 2026-03-11: `S2-02` として `py_runtime.h` から `rc<list<T>>` mutation wrapper を削除し、`py_append` は generated runtime local list compat と object bridge seam のみ、`py_extend/pop/clear/reverse/sort/set_at` は object bridge seam のみ残す形に縮退させた。typed lane は `py_list_*_mut` 直接呼びを正本とし、source guard でもこの end state を固定した。
- 2026-03-11: `S3-01` として `py_runtime_type_id/py_isinstance/py_is_subtype` の thin helper seam を `py_runtime_object_type_id` / `py_runtime_object_isinstance` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass` に切り出し、generated `type_id.cpp` と native compiler wrapper は generic wrapper ではなくこの seam を参照する形へ寄せた。inventory では old wrapper の residual から generated/native caller を外した。
