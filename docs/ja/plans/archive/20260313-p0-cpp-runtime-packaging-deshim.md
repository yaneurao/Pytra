<a href="../../../en/plans/archive/20260313-p0-cpp-runtime-packaging-deshim.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: C++ runtime packaging を compiler 直結へ寄せ、repo shim を退役させる

最終更新: 2026-03-13

関連 TODO:
- 完了済み。`docs/ja/todo/archive/20260313.md` の `ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01`

背景:
- 現行の C++ backend は runtime symbol index の `public_headers` を compiler include 面と SDK/public 面で兼用しており、生成コードは `src/runtime/cpp/pytra/**` と `src/runtime/cpp/core/**` の shim を経由して runtime へ到達している。
- しかし EAST3 が本当に必要としているのは「どの runtime module / symbol を使うか」だけであり、`pytra/**` や `core/**` の forwarder tree 自体は C++ packaging 上の都合でしかない。
- ユーザー指示として、C++ runtime packaging が内部 header を直接 include できるなら shim に依存する必要はなく、compiler は `generated/native` の実体を直接見に行くべきだという方針が示された。
- 現状の `public_headers` 兼用モデルでは、`generated/std/pathlib.cpp` のような checked-in generated runtime ですら `pytra/std/*.h` を include し、`generated/std/*.h` は `runtime/cpp/core/*.h` forwarder に依存している。これでは compiler path から shim を退役できない。

目的:
- C++ compiler/emitter が `src/runtime/cpp/{generated,native}/**` と `src/runtime/cpp/native/core/**` を直接 include する構造へ切り替える。
- `runtime_symbol_index` で compiler 向け include 面と SDK/public 面を分離し、`public_headers` は export/package 用、`compiler_headers` は codegen/build 用に固定する。
- 最終的に `src/runtime/cpp/pytra/**` と `src/runtime/cpp/core/**` を repo 本体から削除し、compiler path も export path も `generated/native` ownership lane に一本化する。

対象:
- `src/toolchain/frontends/runtime_symbol_index.py`
- `tools/gen/gen_runtime_symbol_index.py`
- `tools/runtime_symbol_index.json`
- `src/backends/cpp/emitter/runtime_paths.py`
- `src/backends/cpp/emitter/module.py`
- `src/backends/cpp/emitter/header_builder.py`
- `src/backends/cpp/emitter/cpp_emitter.py`
- `src/backends/cpp/emitter/multifile_writer.py`
- `src/backends/cpp/program_writer.py`
- `src/backends/cpp/cli.py`
- `tools/cpp_runtime_deps.py`
- `tools/check/check_runtime_cpp_layout.py`
- `src/runtime/cpp/generated/**`
- 関連 docs / tests

非対象:
- runtime API の新機能追加
- non-C++ backend への横展開
- C++ runtime の機能 parity 作業
- 最初の slice で `src/runtime/cpp/pytra/**` / `src/runtime/cpp/core/**` を即 delete すること

受け入れ基準:
- runtime symbol index に `compiler_headers` が追加され、`cpp` target では module runtime に対して `generated/**` または `native/**`、core runtime に対して `native/core/**` が返る。
- C++ emitter / runtime emit / multi-file prelude / helper artifact は `pytra/**` や `core/**` ではなく compiler header を include する。
- checked-in generated runtime (`src/runtime/cpp/generated/**`) は `pytra/**` と `runtime/cpp/core/**` を compiler path として使わず、必要な runtime 依存を `generated/**` と `runtime/cpp/native/core/**` へ直接張る。
- `public_headers` は C++ では `compiler_headers` と同じ direct header を返し、repo 常設 shim へは戻らない。
- `tools/check/check_runtime_cpp_layout.py` は `src/runtime/cpp/{pytra,core}` が再出現していないこと、そして generated/native/compiler lane だけが `native/core` を直接 include できることを監査する。
- first wave 完了時点で、transpiled user code / checked-in generated runtime / build graph が `pytra/**` と `core/**` に依存しなくても通る。
- final wave 完了時点で、repo 本体の `src/runtime/cpp/{pytra,core}` は 0 file となり、`--emit-runtime-cpp` もそれらを再生成しない。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/gen/gen_runtime_symbol_index.py --check`
- `python3 tools/check/check_runtime_cpp_layout.py`
- `PYTHONPATH=src:. python3 -m unittest test.unit.tooling.test_runtime_symbol_index`
- `PYTHONPATH=src:. python3 -m unittest test.unit.tooling.test_cpp_runtime_build_graph`
- `PYTHONPATH=src:. python3 -m unittest test.unit.backends.cpp.test_cpp_runtime_symbol_index_integration`
- `PYTHONPATH=src:. python3 -m unittest test.unit.backends.cpp.test_py2cpp_features`

実施方針:
1. `public_headers` を消さずに、まず `compiler_headers` を index へ追加する。compiler は以後こちらだけを見る。
2. module runtime の compiler header は `generated/<bucket>/<module>.h` を優先し、generated header がない module だけ `native/<bucket>/<module>.h` を使う。
3. core runtime の compiler header は `native/core/<module>.h` を正本とし、`core/<module>.h` はあっても SDK/export 用の互換 lane としてしか扱わない。
4. helper include map や runtime emit の include 行は hard-coded `pytra/...` / `core/...` 文字列を減らし、可能な限り runtime symbol index を経由して決める。
5. first wave で compiler 依存を外し、final wave で repo 常設 shim を削除する。

## 目標構造

compiler/build が見る面:

- `src/runtime/cpp/generated/{built_in,std,utils,compiler}/`
- `src/runtime/cpp/native/{built_in,std,utils,compiler}/`
- `src/runtime/cpp/native/core/`

役割:

- `compiler_headers`
  - codegen された C++ と checked-in generated runtime が include する内部正本
- `public_headers`
  - C++ では compiler-facing direct header をそのまま返す
- `compile_sources`
  - build graph が compile 対象として集める実装 file

## 分解

- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S1-01] C++ runtime packaging の責務を docs/TODO に固定し、`compiler_headers` と `public_headers` の二面契約を導入する。
- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S1-02] `tools/gen/gen_runtime_symbol_index.py` / loader / tests に `compiler_headers` を追加し、module は `generated/native`、core は `native/core` を返す contract を固定する。
- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S2-01] C++ emitter/runtime-path/helper include 解決を `compiler_headers` 基準へ切り替え、transpiled user code が `pytra/**` / `core/**` を include しないようにする。
- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S2-02] `emit-runtime-cpp` 生成物・multi-file prelude・helper artifact の core include を `runtime/cpp/native/core/**` へ切り替え、checked-in generated runtime を再生成する。
- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S3-01] `tools/cpp_runtime_deps.py` と build graph test を compiler-direct include 契約へ同期し、shim 非依存で compile source を回収できるようにする。
- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S3-02] `tools/check/check_runtime_cpp_layout.py` と docs を「generated/native/compiler lane は native/core を直接 include 可、`src/runtime/cpp/{pytra,core}` は legacy residual」として更新する。
- [x] [ID: P0-CPP-RUNTIME-PACKAGING-DESHIM-01-S4-01] export-time SDK generator は不要と判断し、`src/runtime/cpp/{pytra,core}` を repo から削除する。

決定ログ:
- 2026-03-13: ユーザー指示により、C++ compiler は `pytra/**` / `core/**` shim に依存せず、runtime packaging が `generated/native` 実体を直接 include できる構造へ寄せる方針を新規 P0 として起票した。
- 2026-03-13: first wave は repo 上の shim を即 delete するのではなく、compiler path から外すことを優先する。`public_headers` は一時的に残してもよいが、codegen/build の正本には使わない。
- 2026-03-13: `compiler_headers` / `runtime_paths.py` / `emit-runtime-cpp` / `program_writer.py` / checked-in generated runtime / `cpp_runtime_deps.py` / `check_runtime_cpp_layout.py` はすでに current contract (`generated/native` + `native/core`) へ同期していたため、plan 前半 slice は README と progress state を current 実装へ揃えたうえで完了扱いにした。
- 2026-03-13: `runtime_symbol_index` は `public_headers` と別に `compiler_headers` を持つように変更した。C++ loader では module runtime に `generated/**`、core runtime に `native/core/**` を優先する `lookup_target_module_primary_compiler_header()` を追加し、emitter 側の include 解決はこの API だけを見るように切り替えた。
- 2026-03-13: helper include map の hard-coded `pytra/built_in/*.h` は廃止し、`pytra.built_in.*` module id から compiler header を引く方式へ寄せた。これにより transpiled user code は `generated/built_in/*` / `generated/std/*` / `generated/utils/*` を直接 include する。
- 2026-03-13: `emit-runtime-cpp` は `runtime/cpp/native/core/**` を直接 include するように変更し、`generated/<bucket>/<module>.h` には対応する `native/<bucket>/<module>.h` が存在する場合だけ companion include を自動注入するようにした。これで旧 `pytra/**` shim が担っていた `generated + native` aggregation を compiler-facing header 側へ移し直した。
- 2026-03-13: `src/toolchain/compiler/backend_registry_static.py` は self-hosted parser の既知 residual（`unterminated string literal`）で `--emit-runtime-cpp` 再生成に失敗したため、first wave では generated compiler shim を維持しつつ、hand-written `native/compiler/backend_registry_static.{h,cpp}` の include だけを `generated/std/{json,pathlib}.h` と `runtime/cpp/native/core/py_runtime.h` へ手同期した。
- 2026-03-13: final wave として C++ の `public_headers` を `compiler_headers` と同じ direct ownership header へ揃え、`--emit-runtime-cpp` は `src/runtime/cpp/generated/**` のみを書き戻すよう変更した。`src/runtime/cpp/{pytra,core}` の checked-in file は削除し、layout guard は shim/compat tree 再導入を fail-fast 化した。
- 2026-03-13: generated header の native companion include は `#endif` 直前へ注入するよう修正し、`iter_ops` など direct generated include で companion が generated 宣言を見失わないようにした。
