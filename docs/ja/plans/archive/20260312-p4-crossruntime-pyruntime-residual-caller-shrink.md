<a href="../../../en/plans/archive/20260312-p4-crossruntime-pyruntime-residual-caller-shrink.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P4 Crossruntime PyRuntime Residual Caller Shrink

最終更新: 2026-03-12

目的:
- `py_runtime.h` をさらに縮める前提として、emitter 以外に残っている `py_runtime` caller を整理する。
- native compiler wrapper、generated C++ runtime、Rust/C# runtime builtins の residual caller を inventory 化し、`object_bridge_compat` と `shared_type_id_contract` の残存理由を限定する。
- header shrink の直前に残すべき caller seam と、先に thin helper へ寄せるべき caller seam を切り分ける。

背景:
- 既存の [p4-crossruntime-pyruntime-emitter-shrink.md](./p4-crossruntime-pyruntime-emitter-shrink.md) は C++ / Rust / C# emitter 側の dependency 整理を扱うが、`py_runtime.h` を実際に塞いでいる residual caller は emitter 以外にも残っている。
- 現在の residual caller は主に native compiler wrapper（`transpile_cli.cpp` / `backend_registry_static.cpp`）、generated C++ runtime（`type_id.cpp` / `json.cpp` / `iter_ops.cpp` など）、Rust/C# runtime builtins に分散している。
- これらは emitter 側整理の後でも `py_runtime.h` の `object_bridge_compat` / `shared_type_id_contract` を残し続けるため、別タスクとして caller 観点で棚卸しする必要がある。
- この作業は header 本体の削除ではなく、cross-runtime の residual caller contract を thin seam へ寄せるための前提整理なので `P4` に置く。

非対象:
- `py_runtime.h` 本体の即時削除や大規模 rewrite。
- emitter 側 residual dependency の再整理。
- 新しい runtime object model や type system の導入。

受け入れ基準:
- native compiler wrapper、generated C++ runtime、Rust/C# runtime builtins に残る `py_runtime.h` caller が plan 内で inventory 化されている。
- residual caller が `object_bridge_compat` と `shared_type_id_contract` に分類され、どこまで thin helper へ寄せるかが明確になっている。
- representative source guard / inventory / smoke の lane が定義され、caller 再流入が fail-closed になる。
- header shrink handoff に必要な residual seam が明文化されている。
- `docs/en/` mirror が日本語版と同じ内容に追従している。

## 子タスク

- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S1-01] native compiler wrapper、generated C++ runtime、Rust/C# runtime builtins の `py_runtime` residual caller inventory を取り、`object_bridge_compat` と `shared_type_id_contract` に分類する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S2-01] native compiler wrapper の `type_id` / object bridge caller を thin helper seam 前提へ寄せ、representative regression を整理する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S2-02] generated C++ runtime の residual caller を再分類し、header shrink 前提で残す caller と再委譲できる caller を切り分ける。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S2-03] Rust/C# runtime builtins の shared seam 依存を inventory 化し、cross-runtime residual contract の最終形を固定する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-RESIDUAL-CALLER-SHRINK-01-S3-01] residual caller inventory tool / source guard / smoke を整備し、`py_runtime.h` shrink handoff 条件を次段 task へ接続する。

## Emitter Handoff Snapshot

- 前段 [20260312-p4-crossruntime-pyruntime-emitter-shrink.md](./archive/20260312-p4-crossruntime-pyruntime-emitter-shrink.md) で emitter 起因の `typed_collection_compat` と `shared_type_id_compat` は空になった。
- この task が引き取る header residual bucket は `object_bridge_mutation` のみで、header surface 正本は [check_cpp_pyruntime_header_surface.py](/workspace/Pytra/tools/check_cpp_pyruntime_header_surface.py) にある。
- したがって本 task の inventory は `object_bridge_mutation` を維持している non-emitter caller に集中し、emitter 再流入の有無は前段 task の inventory tool が引き続き監視する。

## 現在の residual caller inventory（S1-01）

- `native_wrapper_object_bridge_residual`
  - `py_runtime_object_isinstance` @ `src/runtime/cpp/native/compiler/transpile_cli.cpp`
  - `py_runtime_object_isinstance` @ `src/runtime/cpp/native/compiler/backend_registry_static.cpp`
- `generated_cpp_object_bridge_residual`
  - `py_runtime_object_isinstance` @ `src/runtime/cpp/generated/std/json.cpp`
  - `py_append` @ `src/runtime/cpp/generated/built_in/iter_ops.cpp`
- `generated_cpp_shared_type_id_residual`
  - `py_runtime_object_type_id` @ `src/runtime/cpp/generated/built_in/type_id.cpp`
- `cs_runtime_utils_object_bridge_residual`
  - `py_append` @ `src/runtime/cs/pytra/utils/png.cs`
  - `py_append` @ `src/runtime/cs/pytra/utils/gif.cs`
- `rs_runtime_builtin_shared_type_id_residual`
  - `py_runtime_value_type_id` / `py_runtime_value_isinstance` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass`
  - `src/runtime/rs/pytra/built_in/py_runtime.rs`
  - `src/runtime/rs/pytra-core/built_in/py_runtime.rs`
- `cs_runtime_builtin_shared_type_id_residual`
  - `py_runtime_value_type_id` / `py_runtime_value_isinstance` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass`
  - `src/runtime/cs/pytra/built_in/py_runtime.cs`
  - `src/runtime/cs/pytra-core/built_in/py_runtime.cs`

分類:
- `object_bridge_compat`
  - `native_wrapper_object_bridge_residual`
  - `generated_cpp_object_bridge_residual`
  - `cs_runtime_utils_object_bridge_residual`
- `shared_type_id_contract`
  - `generated_cpp_shared_type_id_residual`
  - `rs_runtime_builtin_shared_type_id_residual`
  - `cs_runtime_builtin_shared_type_id_residual`

inventory 正本:
- [check_crossruntime_pyruntime_residual_caller_inventory.py](/workspace/Pytra/tools/check_crossruntime_pyruntime_residual_caller_inventory.py)
- [test_check_crossruntime_pyruntime_residual_caller_inventory.py](/workspace/Pytra/test/unit/tooling/test_check_crossruntime_pyruntime_residual_caller_inventory.py)

generated C++ runtime policy（S2-02）:
- `must remain`
  - `py_runtime_object_isinstance` @ `src/runtime/cpp/generated/std/json.cpp`
  - `py_append` @ `src/runtime/cpp/generated/built_in/iter_ops.cpp`
  - `py_runtime_object_type_id` @ `src/runtime/cpp/generated/built_in/type_id.cpp`
- `re-delegatable before header shrink`
  - なし

Rust/C# runtime builtin policy（S2-03）:
- `must remain`
  - `py_runtime_value_type_id`
  - `py_runtime_value_isinstance`
  - `py_runtime_type_id_is_subtype`
  - `py_runtime_type_id_issubclass`
  - 対象: `src/runtime/{rs,cs}/pytra/built_in/py_runtime.*`
  - 対象: `src/runtime/{rs,cs}/pytra-core/built_in/py_runtime.*`
- `re-delegatable before header shrink`
  - なし
- source guard
  - Rust/C# runtime builtin では上記 4 helper が public の thin seam として存在すること
  - `py_runtime_type_id` / `py_isinstance` / `py_is_subtype` / `py_issubclass` は public surface へ再流入しないこと

Representative smoke lanes（S3-01）:
- native wrapper residual
  - `test/unit/common/test_py2x_entrypoints_contract.py`
  - `py_runtime_object_isinstance` count guard in `transpile_cli.cpp` / `backend_registry_static.cpp`
- generated C++ residual
  - `test/unit/backends/cpp/test_cpp_runtime_iterable.py`
  - `test/unit/backends/cpp/test_cpp_runtime_type_id.py`
- Rust runtime builtin residual
  - `test/unit/backends/rs/test_py2rs_smoke.py`
  - `type_predicate` lowering must stay on runtime builtin thin helpers
- C# residual
  - `test/unit/backends/cs/test_py2cs_smoke.py`
  - `type_predicate` lowering and `pytra.utils.gif` runtime import helper lane stay explicit

## 決定ログ

- 2026-03-12: emitter 側整理だけでは `py_runtime.h` の residual surface を十分に削れないため、native/generated/runtime builtins を対象にした caller 観点の P4 を追加した。
- 2026-03-12: この task は header 削除そのものではなく residual caller contract の棚卸しと thin seam 化が目的なので、header shrink 本体より前段の `P4` に置く。
- 2026-03-12: emitter shrink task からの handoff は `typed_collection_compat = empty`, `shared_type_id_compat = empty`, `object_bridge_mutation = residual caller owned` で固定し、本 task は header surface 上の最後の non-emitter blocker として `object_bridge_mutation` caller inventory を引き取る。
- 2026-03-12: `S1-01` は residual caller を 6 bucket (`native_wrapper_object_bridge_residual`, `generated_cpp_object_bridge_residual`, `generated_cpp_shared_type_id_residual`, `cs_runtime_utils_object_bridge_residual`, `rs_runtime_builtin_shared_type_id_residual`, `cs_runtime_builtin_shared_type_id_residual`) に固定し、category を `object_bridge_compat` と `shared_type_id_contract` の 2 本に限定した。
- 2026-03-12: `S2-01` の first bundle では native compiler wrapper の direct `py_runtime_object_isinstance` を file-local `_object_is_runtime_type(...)` helper へ集約し、wrapper 本体の raw type-check re-entry を 1 callsite/translation-unit に固定した。
- 2026-03-12: `S2-01` は inventory tool に native wrapper residual の representative smoke/source-guard manifest を追加し、`test_py2x_entrypoints_contract.py` の `_object_is_runtime_type(...)` guard を inventory 正本へ接続して完了とする。
- 2026-03-12: `S2-02` では generated C++ residual caller を must-remain と re-delegatable に分け、現時点の `json.cpp` / `iter_ops.cpp` / `type_id.cpp` residual はすべて must-remain として inventory tool に固定した。
- 2026-03-12: `S2-03` では Rust/C# runtime builtin residual を must-remain / re-delegatable に分け、両 runtime tree の public residual contract は `py_runtime_value_type_id` / `py_runtime_value_isinstance` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass` の 4 helper だけに固定した。
- 2026-03-12: `S3-01` では representative smoke lane を inventory tool に登録し、native wrapper / generated C++ / Rust runtime builtin / C# residual caller の test-name drift も fail-closed にした。
