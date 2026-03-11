# P4 Crossruntime PyRuntime Emitter Residual Reduction

最終更新: 2026-03-12

目的:
- `py_runtime.h` をさらに縮める前提として、C++ / Rust / C# emitter 側に残る residual contract を bundle 単位で減らす。
- archived inventory を live task として復帰し、次に削る bucket と順番を source of truth に固定する。
- final header shrink 前に、typed lane へ戻せる caller と intentional residual seam を再分類する。

背景:
- archived plan では `py_runtime.h` 縮小前の emitter residual inventory と representative guard までは固定済みだが、live task が無く、次にどの bucket を削るかが TODO から読めない。
- current inventory tool は residual bucket / reduction order / representative smoke までは持っているが、active bundle metadata が無い。
- C++ / Rust / C# emitter 側の修正が伴うため、header surface 側だけを見ても縮小作業の順番が決まらない。

非対象:
- `py_runtime.h` 本体の即時大規模削除。
- Rust / C# runtime の全面刷新。
- new object model や type_id system の再設計。

受け入れ基準:
- live TODO から current residual bundle と reduction order が読める。
- inventory tool が current residual buckets と active bundle metadata を fail-closed に固定する。
- `crossruntime_mutation_helper_residual` / `cpp_emitter_object_bridge_residual` / `rs_emitter_shared_type_id_residual` / `cs_emitter_shared_type_id_residual` / `cpp_emitter_shared_type_id_residual` の順で reduction bundle を進められる。
- `docs/en/` mirror が日本語版と同じ bundle order / acceptance criteria を持つ。

## 子タスク

- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-RESIDUAL-REDUCTION-01-S1-01] live plan / TODO / inventory tool に current residual bucket, reduction order, active bundle metadata を戻す。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-RESIDUAL-REDUCTION-01-S2-01] `crossruntime_mutation_helper_residual` を減らし、C# bytearray must-remain seam だけへ縮める。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-RESIDUAL-REDUCTION-01-S2-02] `cpp_emitter_object_bridge_residual` を減らし、removable caller を typed lane へ戻す。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-RESIDUAL-REDUCTION-01-S3-01] Rust / C# shared type_id residual を thin seam 前提で削減する。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-RESIDUAL-REDUCTION-01-S3-02] final C++ shared type_id residual を再監査し、intentional contract だけにする。

## Current Residual Buckets

- `crossruntime_mutation_helper_residual`
  - goal: C# bytearray must-remain seam だけに絞る
- `cpp_emitter_object_bridge_residual`
  - goal: removable caller を typed lane に戻し、object bridge wrapper を minimal seam に縮める
- `rs_emitter_shared_type_id_residual`
  - goal: Rust shared type-id seam を thin helper 専用へ縮める
- `cs_emitter_shared_type_id_residual`
  - goal: C# shared type-id seam を thin helper 専用へ縮める
- `cpp_emitter_shared_type_id_residual`
  - goal: final intentional C++ shared type-id contract を再評価する

## Reduction Order

1. `crossruntime_mutation_helper_residual`
2. `cpp_emitter_object_bridge_residual`
3. `rs_emitter_shared_type_id_residual`
4. `cs_emitter_shared_type_id_residual`
5. `cpp_emitter_shared_type_id_residual`

## Representative Guard

- inventory 正本: [check_crossruntime_pyruntime_emitter_inventory.py](/workspace/Pytra/tools/check_crossruntime_pyruntime_emitter_inventory.py)
- unit guard: [test_check_crossruntime_pyruntime_emitter_inventory.py](/workspace/Pytra/test/unit/tooling/test_check_crossruntime_pyruntime_emitter_inventory.py)
- representative smoke:
  - C++: [test_east3_cpp_bridge.py](/workspace/Pytra/test/unit/backends/cpp/test_east3_cpp_bridge.py)
  - Rust: [test_py2rs_smoke.py](/workspace/Pytra/test/unit/backends/rs/test_py2rs_smoke.py)
  - C#: [test_py2cs_smoke.py](/workspace/Pytra/test/unit/backends/cs/test_py2cs_smoke.py)

## 決定ログ

- 2026-03-12: archived `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01` で fixed した inventory / representative smoke / reduction order を live `P4` として復帰し、次の shrink bundle を TODO から読める状態に戻した。
- 2026-03-12: `S1-01` では current residual bucket, reduction order, active bundle metadata を inventory tool と unit test に固定し、bundle status は開始前まで `planned` に揃える。
- 2026-03-12: `S2-01` では C# mutation residual を `bytearray` 専用に縮め、`bytes.pop()/append()` は emitter fail-closed にした。残す helper は `bytearray` の `py_append/py_pop` と index/slice compat helper だけとする。
- 2026-03-12: `S2-02` を開始し、C++ object bridge residual のうち `call.py` に残っていた wrapper-name label (`\"py_append\"` など) を plain operation label (`\"append\"` など) へ切り替えた。bucket は actual object helper caller だけを数える。
