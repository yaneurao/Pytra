<a href="../../../en/plans/archive/20260311-p4-crossruntime-pyruntime-thincompat-followup.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P4: C++/Rust/C# emitter の final thin compat 依存を整理する

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01`

背景:
- `P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` と `P1-CPP-PYRUNTIME-HEADER-SHRINK-01` により、`src/runtime/cpp/native/core/py_runtime.h` の残存 surface は object-bridge mutation helper と final thin compat 2 本（template `py_runtime_type_id` / `py_isinstance`）まで縮退した。
- ただし、これ以上 header を縮めるには、C++ emitter の `runtime_expr.py` / `stmt.py` に残る generic `py_isinstance(...)` と、Rust/C# emitter が共有している `type_id` API residual を別々に扱う必要がある。
- 既存の `P4-CROSSRUNTIME-PYRUNTIME-EMITTER-ALIGN-01` は広い residual contract を揃えたが、「final thin compat removal の blocker」を専用に追跡する inventory はまだない。

目的:
- `py_runtime.h` の final thin compat 2 本を落とす前提として、C++/Rust/C# emitter 側の blocker と shared API residual を明確に分離する。
- `C++ header blocker` と `cross-runtime shared API residual` の end state、および bundle 単位の削減順を docs / tooling / representative smoke で固定する。

対象:
- `src/backends/cpp/emitter/runtime_expr.py`
- `src/backends/cpp/emitter/stmt.py`
- `src/backends/rs/emitter/rs_emitter.py`
- `src/backends/cs/emitter/cs_emitter.py`
- `tools/check_crossruntime_pyruntime_thincompat_inventory.py`
- `test/unit/tooling/test_check_crossruntime_pyruntime_thincompat_inventory.py`
- 必要に応じて `test/unit/backends/cpp/test_east3_cpp_bridge.py`
- 必要に応じて `test/unit/backends/rs/test_py2rs_smoke.py`
- 必要に応じて `test/unit/backends/cs/test_py2cs_smoke.py`

非対象:
- `py_runtime.h` 自体の直ちの追加削減
- Rust/C#/C++ runtime mirror の全面再設計
- generated stdlib C++ 全面再生成とその最終最適化
- `Any/object` 境界や `type_id` 仕様そのものの変更

受け入れ基準:
- emitter-side final thin compat blocker が inventory 化され、未分類再流入を tooling で落とせる。
- `cpp_header_thincompat_blocker` と `crossruntime_shared_type_id_api` の境界が docs / tests / tooling で固定される。
- representative C++/Rust/C# smoke または contract test が通る。
- 少なくとも 1 bundle は blocker の棚卸し・source guard・docs 整理まで完了する。

end state:
- `cpp_header_thincompat_blocker`: C++ emitter で `py_runtime.h` の final thin compat removal を直接ブロックしている generic helper 呼び出しだけを保持する。初期状態では `runtime_expr.py` / `stmt.py` の `py_isinstance` 2 箇所。
- `crossruntime_shared_type_id_api`: Rust/C# emitter では generic 名を直接 emit せず、`py_runtime_value_type_id` / `py_runtime_value_isinstance` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass` の thin helper naming に揃える。generic `py_runtime_type_id` / `py_isinstance` / `py_is_subtype` / `py_issubclass` は runtime 内部 alias としてのみ残ってよい。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_crossruntime_pyruntime_thincompat_inventory.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_crossruntime_pyruntime_thincompat_inventory.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

分解:
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01-S1-01] final thin compat blocker を `cpp_header_thincompat_blocker` / `crossruntime_shared_type_id_api` に棚卸しし、inventory / test を追加する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01-S1-02] end state と bundle 単位の削減順を docs / source guard に固定する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01-S2-01] C++ emitter の `py_isinstance` blocker lane を explicit helper へ寄せ、`cpp_header_thincompat_blocker` を縮める。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01-S2-02] Rust/C# emitter の shared `type_id` API residual を naming / bridge end state に揃え、残る non-blocker を docs へ固定する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-THINCOMPAT-01-S3-01] representative smoke / docs / archive を更新して閉じる。

決定ログ:
- 2026-03-11: `P1-CPP-PYRUNTIME-HEADER-SHRINK-01` を archive した時点で、header に残る final thin compat は template `py_runtime_type_id` / `py_isinstance` の 2 本だけになった。次段階は header 単体の掃除ではなく、C++/Rust/C# emitter 側の blocker と shared API residual の分離になる。
- 2026-03-11: `S1-01` として `tools/check_crossruntime_pyruntime_thincompat_inventory.py` と unit test を追加し、C++ emitter の `py_isinstance` blocker 2 箇所と Rust/C# emitter の shared `type_id` API residual を bucket 化した。
- 2026-03-11: `S1-02` として end state を「`cpp_header_thincompat_blocker` は空 bucket が目標、Rust/C# 側は `crossruntime_shared_type_id_api` へ隔離したまま naming/bridge follow-up を待つ」に固定した。
- 2026-03-11: `S2-01` として C++ emitter の `runtime_expr.py` / `stmt.py` に残っていた generic `py_isinstance` 2 箇所を `py_runtime_object_isinstance` へ寄せ、`cpp_header_thincompat_blocker` bucket を空にした。
- 2026-03-11: `S2-02` として Rust/C# emitter の render surface を `py_runtime_value_type_id` / `py_runtime_value_isinstance` / `py_runtime_type_id_is_subtype` / `py_runtime_type_id_issubclass` に揃え、inventory は raw file-wide regex ではなく renderer end-state helper 専用の classifier に切り替えた。runtime 内部の generic 名は alias として残し、non-blocker として扱う。
- 2026-03-11: `S3-01` として representative inventory/tooling と C++/Rust/C# smoke を再確認し、thincompat follow-up の docs を archive へ移して active TODO を閉じる状態にした。
