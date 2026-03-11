# P0: `py_runtime.h` の最終 residual surface を削減する

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-PYRUNTIME-FINAL-SHRINK-01`

背景:
- 以前の header shrink と cross-runtime residual caller 整理により、`src/runtime/cpp/native/core/py_runtime.h` の残存 surface はかなり小さくなった。
- 現在 header に残っている代表 residual は `object_bridge_mutation` 9 本と thin `type_id` helper 4 本だけで、transitive include や typed collection compatibility のような大きい blocker は既に解消済みである。
- ただし residual caller が native compiler wrapper、generated C++ runtime、Rust/C# runtime builtins にまだ残っているため、header 単体の掃除ではなく「caller 契約を切り替えてから削る」段階に入っている。
- `tools/check_cpp_pyruntime_header_surface.py` はまだ archived follow-up を handoff 先として参照しており、active な最終 shrink task と同期していない。

目的:
- `py_runtime.h` の残りを final shrink 対象として active task に戻し、current residual inventory / target end state / bundle order を docs と tooling で固定する。
- `object_bridge_mutation` helper を caller owned seam からさらに upstream へ押し戻し、header 内の object wrapper を削減する。
- thin `type_id` helper の ownership を shared caller 契約に揃え、header に残す最終 surface を最小化する。

対象:
- `src/runtime/cpp/native/core/py_runtime.h`
- `tools/check_cpp_pyruntime_header_surface.py`
- `test/unit/tooling/test_check_cpp_pyruntime_header_surface.py`
- 必要に応じて `tools/check_cpp_pyruntime_contract_inventory.py`
- 必要に応じて `src/runtime/cpp/native/compiler/*.cpp`
- 必要に応じて `src/runtime/cpp/generated/**/*.cpp`
- 必要に応じて `src/backends/{cpp,rs,cs}/**/*.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/*.md` / `docs/en/plans/*.md`

非対象:
- `py_runtime.h` の物理分割だけで行数を見かけ上減らすこと
- `Any/object` 仕様変更
- Rust/C#/C++ runtime の全面再設計
- relative import や nominal ADT など import/runtime 以外の機能追加

受け入れ基準:
- `tools/check_cpp_pyruntime_header_surface.py` が active plan / task を参照し、current residual inventory と bundle order を fail-closed で固定している。
- `object_bridge_mutation` helper の caller が bundle 単位で upstream 化され、少なくとも 1 束以上 header から削減される。
- `shared_type_id` thin helper の ownership が native/generated/Rust/C# caller 側で整理され、header に generic alias を戻さないことが source guard で固定される。
- representative C++ runtime test と tooling test が通る。
- docs/ja と docs/en の TODO / plan / decision log が同じ end state を指している。

target end state:
- `object_bridge_mutation`
  - `py_append/py_set_at/py_extend/py_pop/py_clear/py_reverse/py_sort` の object wrapper は header から削除されるか、最小限の object-only seam に限定される。
- `shared_type_id_thin_helpers`
  - `py_runtime_type_id_is_subtype`
  - `py_runtime_type_id_issubclass`
  - `py_runtime_object_type_id`
  - `py_runtime_object_isinstance`
  - これ以外の generic alias は header に戻さない。
- `typed_collection_compat`
  - 空 bucket のまま維持する。

bundle order:
1. `S1-01`: current residual inventory / active handoff / bundle order を tooling と docs で固定する。
2. `S2-01`: `object_bridge_mutation` caller を bundle 単位で upstream 化し、header wrapper を削減する。
3. `S2-02`: native/generated/shared caller を thin `type_id` seam に揃え、header alias の残りを見直す。
4. `S3-01`: representative runtime/source guard/docs/archive を更新して閉じる。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_cpp_pyruntime_header_surface.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_cpp_pyruntime_header_surface.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_type_id.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

分解:
- [x] [ID: P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S1-01] `py_runtime.h` の current residual inventory / target end state / bundle order を active plan 前提で docs/tooling/test に固定する。
- [x] [ID: P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S2-01] `object_bridge_mutation` caller を 5-10 個単位の bundle で upstream 化し、header wrapper を bundle 単位で削減する。
- [x] [ID: P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S2-02] native/generated/Rust/C# caller を thin `type_id` helper 前提に揃え、header に generic alias を戻さない形へ固定する。
- [x] [ID: P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S3-01] representative runtime test / source guard / docs / archive を更新して task を閉じる。

決定ログ:
- 2026-03-12: TODO が空になったため、以前から user 要望が強かった `py_runtime.h` の final shrink を新しい最上位 `P0` として起票した。
- 2026-03-12: この task は archived residual-caller shrink を前提にしつつ、active な header surface guard を現在の goal に繋ぎ直す follow-up とする。最初の束では active handoff と bundle order の固定だけに絞る。
- 2026-03-12: `S1-01` として `check_cpp_pyruntime_header_surface.py` の handoff を archived `P4` から active `P0` へ切り替え、target end state と bundle order を tooling/test で fail-closed に固定した。
- 2026-03-12: `S2-01` の first bundle として、C++ tracked source で未使用だった `py_set_at/py_extend/py_pop/py_clear/py_reverse/py_sort` の object wrapper 8 本を header から削除した。残る object-bridge mutation seam は generated C++ runtime が still caller の `py_append(object&)` だけとする。
- 2026-03-12: `S2-01` の second bundle として、`src/runtime/cpp/generated/built_in/iter_ops.cpp` の `py_enumerate_object` を `py_list_append_mut(obj_to_list_ref_or_raise(...))` へ upstream 化した。tracked C++ source では `py_append(object&)` の direct caller を持たない状態になった。
- 2026-03-12: `S2-02` の first bundle として、`check_cpp_pyruntime_contract_inventory.py` を current thin helper 名へ同期した。shared residual bucket は `py_runtime_value_type_id` / `py_runtime_value_isinstance` / `py_runtime_object_isinstance` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass` を native/generated/C++ emitter/Rust/C# emitter+runtime 横断で固定し、generic alias 名は inventory から外した。
- 2026-03-12: `S2-02` の second bundle として、`check_cpp_pyruntime_header_surface.py` に legacy generic alias signature guard を追加した。`static inline uint32 py_runtime_type_id(` / `static inline bool py_isinstance(` / `static inline bool py_is_subtype(` / `static inline bool py_issubclass(` が `py_runtime.h` に戻った時点で fail-closed にする。
- 2026-03-12: `S3-01` として representative runtime/tooling guard、current thin helper inventory、legacy alias drift guard を current end state に揃えた。`object_bridge_mutation` は `py_append(object&)` のみ、shared thin helper は `py_runtime_value_* / py_runtime_object_* / py_runtime_type_id_is_*` に収束したため、task を archive へ移管する。
