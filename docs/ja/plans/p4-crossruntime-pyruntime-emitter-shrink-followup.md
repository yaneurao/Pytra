# P4: emitter 側の `py_runtime.h` shrink follow-up

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01`

背景:
- `P0-CPP-PYRUNTIME-CONTRACT-SHRINK-01` と `P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01` により、`py_runtime.h` から generic `py_runtime_type_id` / `py_isinstance` は除去済みになった。
- ただし `py_runtime.h` には object bridge mutation helper や shared `type_id` thin helper がまだ残っており、さらに縮めるには header 単体ではなく caller 側の emitter 契約を揃える必要がある。
- 既存の C++/Rust/C# emitter は thin helper naming へある程度寄っている一方で、residual helper 依存の棚卸しや削減順は未固定で、今後の shrink 作業を再び局所最適な微修正へ戻すリスクがある。

目的:
- C++/Rust/C# emitter に残る `py_runtime` helper 依存を bucket 化し、`py_runtime.h` をさらに縮めるための caller-side 契約を固定する。
- mutation helper / object bridge / shared `type_id` の end state を docs / tooling / smoke で fail-closed にする。

対象:
- `src/backends/cpp/emitter/`
- `src/backends/rs/emitter/rs_emitter.py`
- `src/backends/cs/emitter/cs_emitter.py`
- 必要に応じて runtime helper inventory tooling
- representative C++ / Rust / C# smoke / contract tests
- `docs/ja/todo/index.md`
- `docs/ja/plans/p4-crossruntime-pyruntime-emitter-shrink-followup.md`

非対象:
- `py_runtime.h` そのものの再分割
- runtime mirror 全面再生成
- `type_id` 仕様の再設計
- language-level `Any/object` semantics の変更

受け入れ基準:
- C++/Rust/C# emitter に残る `py_runtime` helper 依存が bucket 化され、未分類再流入を tooling で検知できる。
- mutation helper / object bridge / shared `type_id` の削減順が docs/source guard に固定される。
- representative C++/Rust/C# regression が現在の thin helper / object bridge 契約を source of truth として固定する。
- follow-up 後の `py_runtime.h` shrink 候補が「caller-side 契約が未整理だから消せない helper」へ限定される。

end state:
- `cpp_emitter_object_bridge_residual`: C++ emitter がまだ object bridge helper に依存する箇所。typed lane からの再流入は禁止。
- `cpp_emitter_shared_type_id_residual`: C++ emitter が shared `type_id` thin helper を使う箇所。generic helper への再流入は禁止。
- `rs_emitter_shared_type_id_residual`: Rust emitter の shared `type_id` helper 依存。
- `cs_emitter_shared_type_id_residual`: C# emitter の shared `type_id` helper 依存。
- `crossruntime_mutation_helper_residual`: C++/Rust/C# emitter の mutation helper 依存。object bridge 以外からの再流入は禁止。

bundle 順:
1. residual helper 依存を bucket 化し、inventory/test を追加する。
2. end state と削減順を docs/source guard に固定する。
3. C++ emitter の residual helper 依存を thin/object-bridge seam に寄せる。
4. Rust/C# emitter の shared helper 依存を shared contract に揃える。
5. representative smoke / docs / archive を更新する。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

分解:
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01] `py_runtime.h` をさらに縮められるよう、C++/Rust/C# emitter 側の residual helper 依存を整理する。
- [x] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S1-01] C++/Rust/C# emitter の residual `py_runtime` helper 使用を bucket 化し、inventory/test を追加する。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S1-02] mutation / `type_id` / object bridge の end state と削減順を docs/source guard に固定する。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-01] C++ emitter の residual helper 依存を thin/object-bridge seam に寄せる。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-02] Rust emitter の residual helper 依存を shared contract へ揃える。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S2-03] C# emitter の residual helper 依存を shared contract へ揃える。
- [ ] [ID: P4-CROSSRUNTIME-PYRUNTIME-EMITTER-SHRINK-01-S3-01] representative smoke / docs / archive を更新し、header shrink follow-up を閉じる。

決定ログ:
- 2026-03-11: `P4-CROSSRUNTIME-PYRUNTIME-FINAL-THINCOMPAT-REMOVAL-01` 完了後の follow-up として起票した。header 側の generic thin compat は除去済みなので、次の shrink は caller-side residual 契約を整理しないと進まない。
- 2026-03-11: `S1-01` として `tools/check_crossruntime_pyruntime_emitter_inventory.py` を thin helper 名ベースへ更新し、residual を `cpp_emitter_object_bridge_residual` / `cpp_emitter_shared_type_id_residual` / `rs_emitter_shared_type_id_residual` / `cs_emitter_shared_type_id_residual` / `crossruntime_mutation_helper_residual` に bucket 化した。C++ は `py_runtime_object_*` と `py_runtime_type_id_*`、Rust/C# は `py_runtime_value_*` / `py_runtime_type_id_*`、mutation helper は C++ object-bridge fallback と C# bytes/bytearray lane だけを許容する。
