# P4 Crossruntime PyRuntime Emitter Shrink

最終更新: 2026-03-12

目的:
- `py_runtime.h` をさらに縮める前提として、C++ / Rust / C# emitter 側に残っている `py_runtime` 依存を整理する。
- typed lane と object bridge lane を emitter 側で明確に分離し、C++ header から削除できる surface を増やす。
- `type_id` / `isinstance` / `issubclass` の cross-runtime 契約を thin seam へ揃え、shared contract の残存理由を限定する。

背景:
- 現在の [py_runtime.h](/workspace/Pytra/src/runtime/cpp/native/core/py_runtime.h) は 1310 行まで縮小しているが、まだ `object_bridge_compat` と `shared_type_id_contract` が残っている。
- C++ emitter は typed lane の大半を upstream 済みだが、object fallback と compatibility seam が残っている。
- Rust / C# emitter も `isinstance` / `issubclass` / mutation helper で C++ runtime contract を前提にした lowering が残っており、`py_runtime.h` 側だけでは安全に削れない。
- この整理は `py_runtime.h` 単体の掃除ではなく、cross-runtime emitter contract の付け替えであるため、後段 `P4` として分離する。

非対象:
- `py_runtime.h` 本体の即時削除や大規模 rewrite。
- Rust / C# runtime 全面刷新。
- 新しい object system や ADT 設計の導入。

受け入れ基準:
- C++ / Rust / C# emitter について、`py_runtime.h` shrink に関係する residual contract が plan 内で inventory 化されている。
- typed lane から外せる helper と、object bridge 専用として残す helper が emitter 観点で明確に分類されている。
- `isinstance` / `issubclass` / `type_id` の lowering contract について、cross-runtime 共通の thin seam と backend 固有 residual が切り分けられている。
- 代表 lane の regression / inventory / source guard 方針が決まっている。
- `docs/en/` mirror が日本語版と同じ計画内容に追従している。

## 子タスク

- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S1-01] C++ / Rust / C# emitter の `py_runtime` 依存 inventory を取り、typed lane / object bridge / shared type_id seam に分類する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-01] C++ emitter で object bridge 専用に残す helper と upstream 済み typed lane を再棚卸しし、header shrink 前提の regression を整理する。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-02] Rust / C# emitter の `isinstance` / `issubclass` / mutation lowering を thin seam 前提へ揃える方針を確定する。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S3-01] cross-runtime inventory tool / smoke / source guard の representative lane を決め、header shrink 後の再流入を fail-closed にする。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S4-01] `py_runtime.h` から落とせる surface と、final residual seam の handoff 条件を次段 task へ接続する。

## 現在の residual inventory（2026-03-12）

- `cpp_emitter_object_bridge_residual`
  - `py_runtime_object_type_id` @ `src/backends/cpp/emitter/cpp_emitter.py`
  - `py_runtime_object_isinstance` @ `src/backends/cpp/emitter/runtime_expr.py`
  - `py_runtime_object_isinstance` @ `src/backends/cpp/emitter/stmt.py`
  - `py_append/extend/pop/clear/reverse/sort/set_at` @ `src/backends/cpp/emitter/call.py`
- `cpp_emitter_shared_type_id_residual`
  - `py_runtime_type_id_is_subtype`
  - `py_runtime_type_id_issubclass`
  - どちらも `src/backends/cpp/emitter/runtime_expr.py`
- `rs_emitter_shared_type_id_residual`
  - `py_runtime_value_type_id`
  - `py_runtime_value_isinstance`
  - `py_runtime_type_id_is_subtype`
  - `py_runtime_type_id_issubclass`
  - すべて `src/backends/rs/emitter/rs_emitter.py`
- `cs_emitter_shared_type_id_residual`
  - `py_runtime_value_type_id`
  - `py_runtime_value_isinstance`
  - `py_runtime_type_id_is_subtype`
  - `py_runtime_type_id_issubclass`
  - すべて `src/backends/cs/emitter/cs_emitter.py`
- `crossruntime_mutation_helper_residual`
  - `py_append`
  - `py_pop`
  - どちらも `src/backends/cs/emitter/cs_emitter.py`

代表 guard:
- inventory 正本: [check_crossruntime_pyruntime_emitter_inventory.py](/workspace/Pytra/tools/check_crossruntime_pyruntime_emitter_inventory.py)
- unit guard: [test_check_crossruntime_pyruntime_emitter_inventory.py](/workspace/Pytra/test/unit/tooling/test_check_crossruntime_pyruntime_emitter_inventory.py)

## C++ Re-Audit Snapshot（S2-01）

- upstream 済み typed lane:
  - `cpp_emitter.py` の list mutation は `py_list_append_mut` / `py_list_extend_mut` / `py_list_pop_mut` / `py_list_clear_mut` / `py_list_reverse_mut` / `py_list_sort_mut` に直接 lower される。
  - `stmt.py` の list subscript assignment は `py_list_set_at_mut` に直接 lower される。
- object bridge 専用 residual:
  - `call.py` の `py_append` / `py_extend` / `py_pop` / `py_clear` / `py_reverse` / `py_sort` / `py_set_at` は wrapper 名の inventory としてのみ残し、object bridge の文脈名に限定する。
- representative regression:
  - tooling guard で `py_list_*_mut` が typed lane (`cpp_emitter.py` / `stmt.py`) に存在することを固定する。
  - tooling guard で wrapper 名が `call.py` 以外へ漏れないことを固定する。

## 決定ログ

- 2026-03-12: この task は `py_runtime.h` 縮小の前提整理だが、直近で優先すべき parser / compiler task を止める性質ではないため `P4` とする。
- 2026-03-12: 先に header を削るのではなく、C++ / Rust / C# emitter の lowering 契約を inventory 化してから shrink handoff へ進む。
- 2026-03-12: `S1-01` は既存 inventory tool を follow-up task の正本として採用し、現時点の residual を 5 bucket (`cpp_emitter_object_bridge_residual`, `cpp_emitter_shared_type_id_residual`, `rs_emitter_shared_type_id_residual`, `cs_emitter_shared_type_id_residual`, `crossruntime_mutation_helper_residual`) へ固定して完了扱いにした。
- 2026-03-12: `S2-01` の first bundle として、C++ emitter では wrapper 再流入禁止を `cpp_emitter.py` / `runtime_expr.py` / `stmt.py` に限定して tool guard 化し、representative regression は `typed list append/set_at -> py_list_*_mut(rc_list_ref(...))` と `pyobj Any list -> obj_to_list_ref_or_raise(..., "py_append" | "py_set_at")` の対で固定した。
- 2026-03-12: `S2-01` では C++ emitter の typed lane direct helper (`py_list_*_mut`) と object bridge wrapper (`py_append` 系) を別 inventory として固定し、wrapper 名が `call.py` 以外へ漏れたら fail-closed にした。
