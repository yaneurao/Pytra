# P1: `py_runtime.h` の残存 surface を実縮小する

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-CPP-PYRUNTIME-HEADER-SHRINK-01`

背景:
- `P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` で typed lane mutation wrapper と generic `type_id` wrapper の ownership はかなり整理された。
- `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01` により、C++/Rust/C# emitter 側の residual contract も bucket 化され、cross-runtime drift は fail-fast 化された。
- その結果、`src/runtime/cpp/native/core/py_runtime.h` に残っている surface は「本当に残すべき compatibility seam」と「さらに削れる wrapper」を分けて扱える段階に入った。

目的:
- `py_runtime.h` の残存 helper を `object bridge mutation`、`typed collection compatibility`、`shared type_id compatibility` に分類し、削減順を固定する。
- 今後の削減で header 内の overload を bundle 単位で落とせるように、source/tooling/smoke を整える。

対象:
- `src/runtime/cpp/native/core/py_runtime.h`
- `tools/check_cpp_pyruntime_header_surface.py`
- `test/unit/tooling/test_check_cpp_pyruntime_header_surface.py`
- 必要に応じて `tools/check_cpp_pyruntime_contract_inventory.py`
- 必要に応じて `test/unit/backends/cpp/test_cpp_runtime_iterable.py`
- 必要に応じて `test/unit/backends/cpp/test_cpp_runtime_type_id.py`

非対象:
- `py_runtime.h` の物理分割だけで行数を見かけ上減らすこと
- Rust/C#/C++ runtime 全面再設計
- `Any/object` 仕様変更
- cross-runtime emitter contract の再整理そのもの

受け入れ基準:
- `py_runtime.h` の残存 helper が category 単位で inventory 化され、未分類再流入を tooling で落とせる。
- `object bridge mutation` と `typed collection compatibility` と `shared type_id compatibility` の境界が docs/test/source で固定される。
- representative C++ runtime test が通る。
- 少なくとも 1 束以上の residual wrapper が header から削減される。

end state:
- `object_bridge_mutation`: `object&` を受ける mutation helper だけを残し、C++ object bridge seam だと明示されている。
- `typed_collection_compat`: 原則空 bucket とし、generated runtime local typed collection のために不可避な helper だけを例外的に残す。
- `shared_type_id_compat`: `py_is_subtype` / `py_issubclass` / `py_runtime_type_id` / `py_isinstance` の thin compatibility だけを残す。

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
- [x] [ID: P1-CPP-PYRUNTIME-HEADER-SHRINK-01-S1-01] `py_runtime.h` の残存 helper を `object_bridge_mutation` / `typed_collection_compat` / `shared_type_id_compat` に棚卸しし、inventory/tooling を追加する。
- [x] [ID: P1-CPP-PYRUNTIME-HEADER-SHRINK-01-S1-02] `py_runtime.h` の target end state と bundle 単位の削減順を docs/source guard に固定する。
- [x] [ID: P1-CPP-PYRUNTIME-HEADER-SHRINK-01-S2-01] `typed_collection_compat` のうち不要な list/dict wrapper を bundle 単位で削減する。
- [ ] [ID: P1-CPP-PYRUNTIME-HEADER-SHRINK-01-S2-02] `shared_type_id_compat` の thin wrapper を source guard 前提でさらに縮める。
- [ ] [ID: P1-CPP-PYRUNTIME-HEADER-SHRINK-01-S3-01] representative runtime test / docs / archive を更新して閉じる。

決定ログ:
- 2026-03-11: `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01` 完了後の follow-up として起票した。次段階は emitter 側ではなく `py_runtime.h` 本体の残存 surface を実際に削減する。
- 2026-03-11: `S1-01` として `py_runtime.h` の残存 helper を `object_bridge_mutation` / `typed_collection_compat` / `shared_type_id_compat` に棚卸しし、drift guard を追加した。
- 2026-03-11: `S1-02` として `test_cpp_runtime_iterable.py` に header surface source guard を追加し、削減順を `typed_collection_compat` の bundle 削減から始める方針に固定した。
- 2026-03-11: `S2-01` の第1束として source-of-truth で未使用だった `py_set_at(dict<K, V>& ...)` を header / inventory / source guard から削除した。残る `typed_collection_compat` は `py_append(list<T>& ...)` のみ。
- 2026-03-11: `S2-01` の第2束として C++ emitter の local concrete list 判定を value lane へ戻し、generated `json.cpp` の local array append を direct `.append(...)` に再同期したうえで `py_append(list<T>& ...)` を header / inventory / source guard から削除した。object helper である `iter_ops.cpp` は `py_list_append_mut(obj_to_list_ref_or_raise(...))` に留め、`typed_collection_compat` bucket は空になった。
