<a href="../../../en/plans/archive/20260311-p4-crossruntime-pyruntime-final-thincompat-removal.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P4: `py_runtime.h` の final thin compat を cross-runtime で撤去する

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01`

背景:
- `P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` と `P1-CPP-PYRUNTIME-HEADER-SHRINK-01` により、C++ header 側の高レベル compat surface はかなり整理された。
- `P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01` では、C++/Rust/C# emitter 側の blocker と shared `type_id` naming を揃え、generic helper 依存を inventory 化した。
- それでも `src/runtime/cpp/native/core/py_runtime.h` には template `py_runtime_type_id` / `py_isinstance` が残っており、checked-in caller も `src/runtime/cpp/generated/std/json.cpp` に残っている。
- Rust/C# 側でも emitter は thin helper naming に揃っている一方、runtime mirror には generic alias (`py_runtime_type_id`, `py_isinstance`, `py_is_subtype`, `py_issubclass`) が public surface として残っている。

目的:
- `py_runtime.h` の final thin compat 2 本を削除できる状態まで、C++ generated caller と Rust/C# runtime alias surface を整理する。
- C++/Rust/C# で「何が blocker で、何が移行専用 alias か」を bucket 化し、未分類再流入を tooling で落とす。

対象:
- `src/runtime/cpp/native/core/py_runtime.h`
- `src/runtime/cpp/generated/std/json.cpp`
- `src/runtime/rs/pytra/built_in/py_runtime.rs`
- `src/runtime/rs/pytra-core/built_in/py_runtime.rs`
- `src/runtime/cs/pytra/built_in/py_runtime.cs`
- `src/runtime/cs/pytra-core/built_in/py_runtime.cs`
- 必要に応じて `src/backends/cpp/emitter/runtime_expr.py`
- 必要に応じて `src/backends/rs/emitter/rs_emitter.py`
- 必要に応じて `src/backends/cs/emitter/cs_emitter.py`
- `tools/check/check_crossruntime_pyruntime_final_thincompat_inventory.py`
- `tools/unittest/tooling/test_check_crossruntime_pyruntime_final_thincompat_inventory.py`
- 必要に応じて representative runtime / smoke tests

非対象:
- `py_runtime.h` の物理分割だけで行数を減らすこと
- `type_id` 仕様そのものの再設計
- `Any/object` 境界の言語仕様変更
- Rust/C#/C++ runtime 全面再生成や全面 rewrite

受け入れ基準:
- final thin compat residual が bucket 単位で inventory 化され、未分類再流入を tooling で検出できる。
- C++ checked-in caller から generic `py_isinstance` / `py_runtime_type_id` が消える。
- Rust/C# runtime の generic alias surface が public compat として増殖しないよう、end state が docs / tests / tooling で固定される。
- representative C++/Rust/C# regression が通る。
- `py_runtime.h` から template `py_isinstance` / `py_runtime_type_id` を削除する最終 slice まで分解順が固定される。

end state:
- `cpp_header_final_thincompat_defs`: 一時的に `py_runtime.h` に残す generic template 定義。最終的には空 bucket。
- `cpp_generated_final_thincompat_blocker`: checked-in generated/native C++ caller に残る generic helper usage。最終的には空 bucket。
- `rs_runtime_generic_alias_surface`: Rust runtime 内の generic alias。thin helper へ委譲する private/internal alias だけを許容し、public compat surface の増殖は禁止。
- `cs_runtime_generic_alias_surface`: C# runtime 内の generic alias。thin helper へ委譲する private/internal alias だけを許容し、public compat surface の増殖は禁止。

bundle 順:
1. `cpp_generated_final_thincompat_blocker` を空にする。
2. `rs_runtime_generic_alias_surface` を internal/private seam に縮める。
3. `cs_runtime_generic_alias_surface` を internal/private seam に縮める。
4. 最後に `cpp_header_final_thincompat_defs` を削除する。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_crossruntime_pyruntime_final_thincompat_inventory.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_crossruntime_pyruntime_final_thincompat_inventory.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_cpp_runtime_type_id.py'`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s tools/unittest/emit/rs -p 'test_py2rs_smoke.py' -k type_predicate`
- `PYTHONPATH=src:test/unit python3 -m unittest discover -s tools/unittest/emit/cs -p 'test_py2cs_smoke.py' -k type_predicate`
- `python3 tools/build_selfhost.py`
- `git diff --check`

分解:
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01] `py_runtime.h` の final thin compat 2 本を cross-runtime で撤去する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S1-01] final thin compat residual を `cpp_header_final_thincompat_defs` / `cpp_generated_final_thincompat_blocker` / `rs_runtime_generic_alias_surface` / `cs_runtime_generic_alias_surface` に棚卸しし、inventory/test を追加する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S1-02] target end state と bundle 単位の削減順を docs/source guard に固定する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S2-01] checked-in C++ generated/native caller を thin helper (`py_runtime_object_isinstance` など) へ寄せ、`cpp_generated_final_thincompat_blocker` を空にする。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S2-02] Rust/C# runtime alias surface を internal/private seam へ縮め、generic alias の public 増殖を止める。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01-S3-01] `py_runtime.h` から template `py_runtime_type_id` / `py_isinstance` を削除し、representative regression / docs / archive を更新する。

決定ログ:
- 2026-03-11: TODO が空になったため、新しい低優先度 follow-up として起票した。直前までに emitter-side blocker 自体はかなり整理済みなので、次段階は「generic helper 定義と checked-in caller を消せる状態にする」ことを目的にする。
- 2026-03-11: `S1-01` として `tools/check/check_crossruntime_pyruntime_final_thincompat_inventory.py` と unit test を追加し、`py_runtime.h` の final template 2 本、generated `std/json.cpp` の generic `py_isinstance` blocker、Rust/C# runtime mirror の generic alias surface を bucket 化した。
- 2026-03-11: `S1-02` として bundle 順を `cpp generated blocker -> Rust alias surface -> C# alias surface -> header defs` に固定した。inventory/tooling には `empty_before_header_removal` / `internal_or_private_only_before_header_removal` / `remove_last_after_crossruntime_alignment` の target end state も埋め込み、header removal を必ず最後にする contract を source guard 化した。inventory は exact residual 固定ではなく「許可 bucket の部分集合」を見るため、後続 bundle が先に residual を減らしても未分類再流入だけを落とせる。
- 2026-03-11: `S2-01` として checked-in C++ blocker だった `src/runtime/cpp/generated/std/json.cpp` を `py_runtime_object_isinstance` へ寄せ、JSON escape の `\b` / `\f` regressions も同時に修正した。inventory の `cpp_generated_final_thincompat_blocker` は空 bucket に更新した。
- 2026-03-11: `S2-02` として Rust/C# runtime mirror の `py_runtime_type_id` / `py_is_subtype` / `py_issubclass` / `py_isinstance` alias を public から internal/private seam へ落とした。inventory は alias 自体の存在を bucket として保ちつつ、public 再流入だけを `target end state` violation として落とす。
- 2026-03-11: `S3-01` として `py_runtime.h` から template `py_runtime_type_id` / `py_isinstance` を削除し、C++ runtime/codegen/header-surface regression を thin helper (`py_runtime_object_isinstance`) 前提へ更新した。`shared_type_id_compat` bucket は空になり、header 側の final thin compat residual を archive 可能な状態にした。
