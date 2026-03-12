# P5: C++ `py_runtime.h` residual thin seam shrink

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01`

背景:
- `src/runtime/cpp/native/core/py_runtime.h` はすでに大きく縮小され、typed collection compatibility と generic `type_id` compatibility は header surface inventory 上は空になっている。
- ただし current header には、object bridge mutation の `py_append(object& ...)` と、shared `type_id` thin seam (`py_runtime_value_type_id`, `py_runtime_value_isinstance`, `py_runtime_object_type_id`, `py_runtime_object_isinstance`, `py_runtime_type_id_is_subtype`, `py_runtime_type_id_issubclass`) が残っている。
- これらは header 単体の掃除ではなく、C++ / Rust / C# emitter と各 runtime 側の shared contract をどう縮退させるかを先に決めないと削れない。
- そのため、この task は immediate shrink ではなく、cross-runtime handoff と最終削減順を `P5` で固定するための後段計画である。

目的:
- `py_runtime.h` に残る thin seam を「intentional residual」と「将来 backend local へ押し戻せる seam」に分ける。
- object bridge mutation seam と shared `type_id` seam の縮退順を決め、将来の header shrink task が bundle 単位で進められるようにする。
- C++ / Rust / C# emitter と runtime の representative contract を明文化し、silent re-expansion を防ぐ。

対象:
- `py_runtime.h` の残 thin seam inventory
- C++ emitter の object bridge / shared `type_id` caller 棚卸し
- Rust / C# emitter と runtime の shared `type_id` seam 棚卸し
- `py_append(object&)` の object-only seam 最小化方針
- thin seam final removal の handoff docs / tooling / regression 整理

非対象:
- この task 自体で `py_runtime.h` から seam を実装削除すること
- nominal ADT / type-predicate full redesign
- Rust/C# runtime の大規模 ABI 再設計
- `deque` や別種 collection support の新規実装

受け入れ基準:
- `py_runtime.h` に残る seam が object-bridge mutation と shared `type_id` thin seam に分類され、縮退順が docs/tooling に固定されていること。
- C++ / Rust / C# emitter の residual caller が bucket 単位で整理されていること。
- final shrink に進む前提条件と blocker が明文化されていること。
- `python3 tools/check_todo_priority.py` と `git diff --check` が通ること。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_cpp_pyruntime_header_surface.py`
- `python3 tools/check_cpp_pyruntime_contract_inventory.py`
- `python3 tools/check_crossruntime_pyruntime_emitter_inventory.py`
- `python3 tools/check_cpp_pyruntime_residual_thin_seam_contract.py`
- `python3 tools/check_cpp_pyruntime_residual_thin_seam_handoff_contract.py`
- `git diff --check`

決定ログ:
- 2026-03-12: `py_runtime.h` の immediate cleanup はほぼ終わっており、残りは header 単体ではなく cross-runtime 契約の整理が前提なので `P5` に置く。
- 2026-03-12: 代表 residual は `py_append(object&)` と shared `type_id` thin seam で、typed compatibility bucket はすでに空という前提を baseline にする。
- 2026-03-12: 将来の縮退順は `object bridge mutation seam` と `shared type_id seam` を分けて考え、C++ / Rust / C# emitter+runtime contract を bundle 単位で減らす方針にする。
- 2026-03-12: `check_cpp_pyruntime_header_surface.py` と `check_crossruntime_pyruntime_emitter_inventory.py` の follow-up / handoff 参照は archived `P0/P4` ではなく active な `P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01` に揃え、この task 自体が current residual baseline を source-guard する正本とする。
- 2026-03-12: source-wide contract inventory では `py_append/py_pop` の C# bytearray compat と `gif/png` utility runtime だけを `object_bridge_required` へ分離し、shared runtime contract は `type_id` thin seam と native compiler `py_runtime_object_isinstance` のみを保持する。
- 2026-03-12: shared `type_id` thin seam の分類は `check_crossruntime_pyruntime_emitter_inventory.py` の `P5-...-S2-02` guard で固定し、C++ では `py_runtime_value_type_id` だけを future-reducible、Rust/C# は全 residual caller を must-remain-until-runtime-task とする。
- 2026-03-12: final handoff criteria は `check_cpp_pyruntime_residual_thin_seam_handoff_contract.py` に集約し、header surface / source-wide contract / crossruntime emitter inventory の 3 guard と bundle order を `P5` の archive 前提条件として固定する。

## 分解

- [x] [ID: P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S1-01] current header surface と cross-runtime residual caller の baseline を docs / tooling / inventory で固定する。
- [x] [ID: P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S2-01] object bridge mutation seam の caller ownership と backend-local へ押し戻せる lane を分類する。
- [x] [ID: P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S2-02] shared `type_id` thin seam の C++ / Rust / C# residual contract を分類し、must-remain と future-reducible を切り分ける。
- [x] [ID: P5-CPP-PYRUNTIME-RESIDUAL-THIN-SEAM-SHRINK-01-S3-01] final shrink handoff 条件、bundle order、representative regression を docs / tooling / archive へ同期する。
