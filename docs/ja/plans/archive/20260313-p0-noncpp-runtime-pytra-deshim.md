<a href="../../../en/plans/archive/20260313-p0-noncpp-runtime-pytra-deshim.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: 非 C++/非 C# runtime checked-in `pytra/` lane 全廃

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01`

背景:
- 2026-03-13 時点で、checked-in tree には `src/runtime/{rs,go,java,kotlin,scala,swift,nim,js,ts,lua,ruby,php}/pytra/**` が残っている。
- archive 済みの `20260313-p1-noncpp-runtime-layout-rollout-remaining.md` は、non-C++ backend の一部で `pytra/` を public shim / compatibility lane として残す前提で完了扱いになっている。
- しかしユーザー指示はそれと異なり、C++ / C# を除く全 backend について checked-in `src/runtime/<lang>/pytra/**` をなくし、repo 常設 runtime layout を `generated/native` のみに限定するものだった。
- 現在の PHP/Lua/Ruby 系の smoke / packaging / contract は repo-tree `pytra/**` direct-load や compat shim inventory を前提に固定されており、この差が未解消のまま残っている。
- C# はすでに duplicate lane を delete target として空にしたが、Rust を含む他 backend はまだ `pytra/` directory 自体が checked-in tree に存在する。

目的:
- C++ / C# を除く全 backend (`rs`, `go`, `java`, `kotlin`, `scala`, `swift`, `nim`, `js`, `ts`, `lua`, `ruby`, `php`) から checked-in `src/runtime/<lang>/pytra/**` を撤去する。
- repo 常設の runtime ownership vocabulary を `generated/native` のみに揃える。
- public compatibility が必要な backend でも、compat wrapper は checked-in `src/runtime/**` に置かず、出力先 staging / packaging / generated artifact 側で扱う。
- contract / guard / smoke / docs を新方針へ同期し、`pytra/` 再侵入を fail-fast にする。

対象:
- `src/runtime/{rs,go,java,kotlin,scala,swift,nim,js,ts,lua,ruby,php}/pytra/**`
- `src/toolchain/compiler/backend_registry_metadata.py`
- `src/toolchain/compiler/pytra_cli_profiles.py`
- `src/toolchain/compiler/js_runtime_shims.py`
- selfhost / packaging / transpile output / runtime copy 導線
- `tools/check_noncpp_runtime_layout_contract.py`
- `tools/check_noncpp_runtime_layout_rollout_remaining_contract.py`
- runtime layout / marker / naming / SoT guard
- representative backend smoke / tooling unit / docs / TODO

非対象:
- C++ runtime packaging / shim tree の再設計
- C# runtime duplicate lane cleanup のやり直し
- `generated/**` / `native/**` の ownership 自体を別方式へ変えること
- `src/pytra/**` 正本 module の挙動変更
- 出力物側 compat wrapper を即時全面禁止すること

受け入れ基準:
- `find src/runtime -maxdepth 2 -type d -name pytra | sort` の結果が checked-in tree では `src/runtime/cpp/pytra` のみになる。
- `src/runtime/{rs,go,java,kotlin,scala,swift,nim,js,ts,lua,ruby,php}/pytra/**` は file だけでなく directory ごと存在しない。
- `tools/check_noncpp_runtime_layout_contract.py` と `tools/check_noncpp_runtime_layout_rollout_remaining_contract.py` は、対象 backend の checked-in `pytra/` を compat lane と見なさず、再出現を fail-fast にする。
- repo-tree direct-load / source-reexport smoke は `src/runtime/<lang>/pytra/**` を前提にしない。
- backend registry / selfhost / packaging / transpile output contract は `generated/native` 直参照、または output-side staging artifact で完結する。
- 旧 `pytra/` compat lane 前提は archive 文書にのみ残り、active plan / TODO / spec / checker wording からは除去される。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `find src/runtime -maxdepth 2 -type d -name pytra | sort`
- `python3 tools/check_noncpp_runtime_layout_contract.py`
- `python3 tools/check_noncpp_runtime_layout_rollout_remaining_contract.py`
- `python3 tools/check_runtime_core_gen_markers.py`
- `python3 tools/check_runtime_pytra_gen_naming.py`
- `python3 tools/check_runtime_std_sot_guard.py`
- `python3 tools/check_multilang_selfhost_stage1.py`
- `python3 tools/check_multilang_selfhost_multistage.py`
- `git diff --check`

実施方針:
1. checked-in repo tree の runtime lane は `generated/native` だけを canonical / allowed にする。対象 backend の `pytra/` は temporary compat lane ではなく delete target とする。
2. `pytra/**` 依存を見つけた場合は、repo tree に shim を残すのではなく、`generated/native` 直参照へ切り替えるか、必要最小限の output-side artifact 生成へ押し出す。
3. repo-tree direct-load smoke は layout 契約の誤固定になっているため、`generated/native` または output staging を検証する smoke へ置き換える。
4. Rust は `rs/cs` 専用 P0 の残差として独立 cleanup し、残 backend は static family と script family に分けて進める。
5. archive 文書は履歴として残すが、active policy はこの P0 と `docs/ja/todo/index.md` を正とする。

## backend 分類

### Rust cleanup

- `rs`

### static family

- `go`
- `java`
- `kotlin`
- `scala`
- `swift`
- `nim`

### script family

- `js`
- `ts`
- `lua`
- `ruby`
- `php`

## 分解

- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01] 非 C++ / 非 C# backend の checked-in `src/runtime/<lang>/pytra/**` を全廃し、repo 常設 runtime layout を `generated/native` のみに揃える。
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S1-01] 対象 backend 12 言語の current `pytra/**` inventory、参照元、delete blocker を棚卸しし、current->target mapping を plan / contract に固定する。
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S1-02] active contract / checker / spec wording を `generated/native only` へ切り替え、対象 backend の checked-in `pytra/**` 再出現を fail-fast にする。
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S2-01] Rust (`rs`) の checked-in `src/runtime/rs/pytra/**` を削除し、`py2rs` / selfhost / runtime guard / smoke から repo-tree `pytra/**` 前提を外す。
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S2-02] static family (`go/java/kotlin/scala/swift/nim`) の backend registry / packaging / smoke / tooling を `generated/native` 直参照へ揃え、checked-in `pytra/**` は deletion inventory としてのみ残す。
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S2-03] static family の checked-in `src/runtime/<lang>/pytra/**` を物理削除し、allowlist / inventory / representative smoke を deletion end state に同期する。
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S3-01] JS/TS の import path / shim writer / selfhost / smoke を見直し、repo-tree `src/runtime/{js,ts}/pytra/**` direct-load と compat shim 契約を撤去する。
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S3-02] Lua/Ruby/PHP の packaging / runtime copy / loader contract を `generated/native` または output-side staging へ移し、repo-tree `pytra/**` 常設前提を撤去する。
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S3-03] script family (`js/ts/lua/ruby/php`) の checked-in `src/runtime/<lang>/pytra/**` を物理削除し、representative smoke と contract baseline を deletion end state へ更新する。
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S4-01] docs / TODO / archive 参照 / inventory を最終同期し、「非 C++ / 非 C# backend に checked-in `pytra/` は存在しない」状態で close する。

決定ログ:
- 2026-03-13: ユーザー指示に従い、archive 側 P1 が許容していた「non-C++ backend の `pytra/` compat lane 維持」は active policy から取り消し、新規 P0 として `checked-in pytra 全廃` を起票する。
- 2026-03-13: 起票時点の observed checked-in `pytra/` directory は `rs`, `go`, `java`, `kotlin`, `scala`, `swift`, `nim`, `js`, `ts`, `lua`, `ruby`, `php` の 12 backend。C# は空 directory cleanup 済み、C++ は本 task の対象外とする。
- 2026-03-13: この P0 では「repo 常設 shim の削除」を目的とし、public compatibility が必要でも output-side artifact として扱う。`src/runtime/<lang>/pytra/**` を薄い forwarder として温存する対応は不許可とする。
- 2026-03-13: `P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S1-01` で current `pytra/` directory/file inventory、backend mapping、delete blocker references を `noncpp_runtime_pytra_deshim_contract.py` / checker / unit test に固定した。まだ policy 切替は行わず、削除前の current state を明示する段階に留める。
- 2026-03-13: S1-02 first bundle で `spec-folder/spec-dev` を `generated/native only` wording に合わせ、doc-policy drift を checker で fail-fast にした。
- 2026-03-13: S1-02 second bundle で Rust active contract / layout guard の `pytra` 語彙を `compat` から `delete-target debt` へ切り替え、`noncpp_runtime_layout_contract.py` / `check_rs_runtime_layout.py` / dedicated deshim blocker baseline から「checked-in `rs/pytra` は live compat lane」という前提を外した。
- 2026-03-13: S1-02 third bundle で Rust user-facing docs (`docs/ja/tutorial/transpiler-cli.md`, `docs/en/how-to-use.md`) を `delete target debt` wording へ直し、dedicated deshim doc-policy checker でも監視するようにした。S1-02 は `rollout_remaining_contract` 側の live `pytra` wording が残るため、まだ open のままとする。
- 2026-03-13: S1-02 fourth bundle で `noncpp_runtime_layout_rollout_remaining_contract.py` と checker の `pytra` rationale / message を `delete-target debt` wording に寄せた。まだ `target_roots=("generated","native","pytra")` と `compat_*` schema が残るため、S1-02 close には至っていない。
- 2026-03-13: S1-02 fifth bundle で `noncpp_runtime_layout_rollout_remaining_contract.py` の lane ownership 値を `compat` から `delete_target` へ反転した。まだ schema field 名 `compat_*` と `target_roots=("generated","native","pytra")` が残るため、S1-02 は継続する。
- 2026-03-13: S1-02 sixth bundle で `noncpp_runtime_layout_rollout_remaining_contract.py` の live `target_roots` を `("generated","native")` に縮め、checker も `delete_target` lane だけ `pytra/**` を許す形へ更新した。`compat_files` / `compat_modules` と wave-B helper/iterator の `compat` 命名はまだ残るため、S1-02 は継続する。
- 2026-03-13: S1-02 seventh bundle で `noncpp_runtime_layout_rollout_remaining_contract.py` / checker / test の wave-B `compat` helper / iterator 命名を `delete_target` へ置換した。S1-02 の主残差は `noncpp_runtime_generated_cpp_baseline_contract.py` とその checker/test に残る `compat_files` 語彙になった。
- 2026-03-13: S1-02 eighth bundle で `noncpp_runtime_generated_cpp_baseline_contract.py` / checker / test の `compat_files` 語彙も `delete_target_files` へ置換した。これで active contract / checker / spec 側の pytra-specific live `compat` wording は除去されたため、S1-02 を完了扱いにした。
- 2026-03-13: S1-02 third bundle で `spec-java-native-backend.md` / `spec-lua-native-backend.md` / `spec-gsk-native-backend.md` の live runtime root wording を `src/runtime/<lang>/{generated,native}/` へ統一し、doc-policy checker が active native-backend spec まで監視するように広げた。
- 2026-03-13: S2-01 で checked-in `src/runtime/rs/pytra/**` を物理削除し、`check_rs_runtime_layout.py` は Rust `pytra` lane が再出現したら fail する absent-end-state guard へ更新した。`noncpp_runtime_pytra_deshim_contract.py` / `noncpp_runtime_layout_contract.py` / `noncpp_runtime_generated_cpp_baseline_contract.py` と crossruntime inventory checker も Rust `delete_target` を現物 inventory ではなく「削除済み」前提に合わせた。
- 2026-03-13: S2-02 で static family は `backend_registry_metadata.py` と representative smoke がすでに `generated/native` 直参照であることを前提に、`noncpp_runtime_layout_rollout_remaining_contract.py` から `pytra` current lane mapping を外した。checked-in `pytra/**` は `delete_target_files` / `delete_target_modules` の明示 inventory としてのみ残し、`noncpp_runtime_pytra_deshim_contract.py` の static-family `contract_allowlist` blocker も除去した。
- 2026-03-13: S2-03 で `src/runtime/{go,java,kotlin,scala,swift,nim}/pytra/**` を物理削除し、`noncpp_runtime_pytra_deshim_contract.py` の current directory/file inventory を script family のみへ縮退させた。`noncpp_runtime_generated_cpp_baseline_contract.py` / `noncpp_runtime_layout_rollout_remaining_contract.py` の static-family delete-target inventory は空に揃え、`runtime_std_sot_allowlist.txt` の Go stale entry も除去した。
- 2026-03-13: S2-03 では representative smoke の `runtime_source_path_is_migrated` 群を「`generated/native` は存在し、checked-in `pytra/**` は存在しない」という end state に強化した。あわせて active spec (`spec-java-native-backend.md`, `spec-gsk-native-backend.md`) の static-family runtime boundary から delete-target debt wording を外した。
- 2026-03-13: S3-01 で JS/TS の repo-tree direct-load smoke を output-side generated shim smoke に置き換えた前提で、`noncpp_runtime_pytra_deshim_contract.py` から JS/TS blocker bucket と exact blocker baseline を除去した。checked-in `src/runtime/{js,ts}/pytra/**` は deletion inventory としてのみ残し、repo-tree direct-load / selfhost / compat-contract blocker は解消済みとする。
- 2026-03-13: S3-02 で Lua/Ruby/PHP の repo-tree direct-load smoke を output-side staging smoke に置き換え、`noncpp_runtime_pytra_deshim_contract.py` から script-family blocker baseline を全廃した。PHP の `require_once __DIR__ . '/pytra/py_runtime.php';` は repo-tree 前提ではなく output-side staging rewrite とみなし、runtime shim writer blocker から外す。
- 2026-03-13: S3-03 で `src/runtime/{js,ts,lua,ruby,php}/pytra/**` を物理削除し、`noncpp_runtime_pytra_deshim_contract.py` の current directory/file inventory を空へ縮退させた。`noncpp_runtime_layout_rollout_remaining_contract.py` / `noncpp_runtime_generated_cpp_baseline_contract.py` の script-family delete-target inventory も空に揃え、representative smoke は repo-tree `pytra/**` 不在を確認する deletion end state に同期した。
- 2026-03-13: S4-01 で active tutorial/spec wording を final invariant に合わせ、plan/TODO を archive へ移した。checked-in tree の `pytra/` directory は `src/runtime/cpp/pytra` のみで、non-C++ / non-C# backend に repo-owned `pytra/**` は残さない状態を close とする。
