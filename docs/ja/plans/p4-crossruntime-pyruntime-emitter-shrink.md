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

- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S1-01] C++ / Rust / C# emitter の `py_runtime` 依存 inventory を取り、typed lane / object bridge / shared type_id seam に分類する。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-01] C++ emitter で object bridge 専用に残す helper と upstream 済み typed lane を再棚卸しし、header shrink 前提の regression を整理する。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-02] Rust / C# emitter の `isinstance` / `issubclass` / mutation lowering を thin seam 前提へ揃える方針を確定する。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S3-01] cross-runtime inventory tool / smoke / source guard の representative lane を決め、header shrink 後の再流入を fail-closed にする。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S4-01] `py_runtime.h` から落とせる surface と、final residual seam の handoff 条件を次段 task へ接続する。

## 決定ログ

- 2026-03-12: この task は `py_runtime.h` 縮小の前提整理だが、直近で優先すべき parser / compiler task を止める性質ではないため `P4` とする。
- 2026-03-12: 先に header を削るのではなく、C++ / Rust / C# emitter の lowering 契約を inventory 化してから shrink handoff へ進む。
