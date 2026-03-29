<a href="../../../en/plans/archive/20260311-p4-crossruntime-pyruntime-emitter-align.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P4: C++/Rust/C# emitter の `py_runtime` residual contract を揃える

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01`

背景:
- `P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` により、`py_runtime.h` の typed lane mutation wrapper と generic `type_id` wrapper はかなり縮退した。
- ただし、今後 `py_runtime.h` をさらに薄くするには、C++/Rust/C# emitter 側で残っている `py_runtime` helper 依存を cross-runtime で揃え、`object bridge residual` と `shared type_id contract` を明示的に分離する必要がある。
- 現状でも `src/backends/cpp/emitter/`, `src/backends/rs/emitter/rs_emitter.py`, `src/backends/cs/emitter/cs_emitter.py` には、mutation helper / `type_id` helper / runtime mirror 定義が混在している。

目的:
- `py_runtime.h` 縮小後の end state に合わせて、C++/Rust/C# emitter の residual contract を bucket 化し、drift を fail-fast にする。
- `object bridge residual`、`shared type_id contract`、`cross-runtime bridge residual` の境界を docs / tooling / smoke で固定する。

対象:
- `src/backends/cpp/emitter/*.py`
- `src/backends/rs/emitter/rs_emitter.py`
- `src/backends/cs/emitter/cs_emitter.py`
- 必要に応じて `src/runtime/rs/pytra*/built_in/py_runtime.rs`
- 必要に応じて `src/runtime/cs/pytra*/built_in/py_runtime.cs`
- `tools/*pyruntime*inventory*.py`
- `tools/unittest/tooling/*inventory*.py`
- `tools/unittest/emit/cpp/test_east3_cpp_bridge.py`
- `tools/unittest/emit/rs/test_py2rs_smoke.py`
- `tools/unittest/emit/cs/test_py2cs_smoke.py`

非対象:
- `py_runtime.h` 自体の追加削減
- Rust/C#/C++ runtime の全面再設計
- `Any/object` 境界の仕様変更
- `JsonValue` / nominal ADT 仕様拡張

受け入れ基準:
- C++/Rust/C# emitter の residual `py_runtime` symbol が bucket 単位で inventory 化され、未分類再流入を tooling で落とせる。
- C++ emitter の `object bridge residual` と Rust/C#/C++ の `shared type_id contract` が混ざらない。
- Rust/C# emitter の type predicate / runtime type id lane は canonical helper 名に揃う。
- representative smoke / contract test が通る。

residual bucket の end state:
- `cpp_object_bridge_residual`: C++ emitter の object fallback だけが使える bucket とし、`py_append/extend/pop/clear/reverse/sort/set_at` 以外は入れない。
- `shared_type_id_contract`: `py_runtime_type_id`, `py_isinstance`, `py_is_subtype`, `py_issubclass` だけを許容し、C++/Rust/C# emitter すべてがこの helper 名で揃う状態を正本にする。
- `crossruntime_object_bridge_residual`: C++ 以外の emitter に残る object bridge mutation helper を隔離する bucket とし、現時点では C# の `py_append` / `py_pop` だけを許容する。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_crossruntime_pyruntime_emitter_inventory.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_crossruntime_pyruntime_emitter_inventory.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_east3_cpp_bridge.py'`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s tools/unittest/emit/rs -p 'test_py2rs_smoke.py' -k type_predicate`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s tools/unittest/emit/cs -p 'test_py2cs_smoke.py' -k type_predicate`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/check_transpiler_version_gate.py`
- `python3 tools/run/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

分解:
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01-S1-01] C++/Rust/C# emitter の residual `py_runtime` symbol を bucket 化し、inventory と drift guard を追加する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01-S1-02] `object bridge residual` / `shared type_id contract` / `cross-runtime bridge residual` の end state を docs に固定する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01-S2-01] C++ emitter の residual object-bridge mutation helper 呼び出しを representative lane で整理する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01-S2-02] Rust/C# emitter の `type_id` / type predicate lowering を shared contract 前提に揃える。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01-S3-01] representative smoke / docs / archive を更新して閉じる。

決定ログ:
- 2026-03-11: `P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` 完了後の follow-up として起票した。`py_runtime.h` 自体の削減ではなく、cross-runtime emitter が要求する residual contract の可視化と整列をこの P4 の責務にする。
- 2026-03-11: `S1-01` として `tools/check/check_crossruntime_pyruntime_emitter_inventory.py` と unit test を追加し、emitters の residual `py_runtime` symbol を `cpp_object_bridge_residual` / `shared_type_id_contract` / `crossruntime_object_bridge_residual` に bucket 化した。
- 2026-03-11: `S1-02` として 3 bucket の end state を docs に固定した。C++ object fallback は `cpp_object_bridge_residual` へ、cross-language type predicate / type id helper は `shared_type_id_contract` へ、C# の list bridge 残存は `crossruntime_object_bridge_residual` へ隔離する。
- 2026-03-11: `S2-01` として C++ emitter の object-bridge helper 名を `CppCallEmitter` の canonical map に集約し、`py_append/extend/pop/clear/reverse/sort/set_at` の residual symbol は `call.py` 1 箇所にだけ残る状態へ寄せた。inventory guard もこの end state に更新した。
- 2026-03-11: `S2-02` として Rust/C# emitter の `py_runtime_type_id` / `py_isinstance` / `py_is_subtype` / `py_issubclass` lowering を per-emitter helper seam に集約し、代表的な `isinstance(...)` lane と EAST3 `ObjTypeId/IsInstance/IsSubtype/IsSubclass` lane が同じ shared contract を使う形に揃えた。
- 2026-03-11: `S3-01` として crossruntime inventory、representative C++ bridge、Rust/C# `type_predicate` smoke、selfhost build を再実行し、docs と archive を representative end state に同期した。
