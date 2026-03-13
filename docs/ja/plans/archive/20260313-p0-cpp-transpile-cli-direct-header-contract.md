# P0: `transpile_cli` typed C++ contract を direct ownership header/source に揃える

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01`

背景:
- `test/unit/common/test_py2x_entrypoints_contract.py` の `test_compiler_transpile_cli_typed_shim_skips_legacy_wrapper()` は、まだ `src/runtime/cpp/pytra/compiler/transpile_cli.h` を public wrapper として読みに行っている。
- しかし live tree では checked-in `src/runtime/cpp/pytra/compiler/transpile_cli.h` は既に存在せず、`src/runtime/cpp/generated/compiler/transpile_cli.h` と `src/runtime/cpp/generated/compiler/transpile_cli.cpp` が typed shim の direct ownership artifact になっている。
- `docs/ja/spec/spec-runtime.md` でも C++ は `public_headers == compiler_headers` を direct ownership header に揃える前提なので、この focused contract test だけが stale assumption を温存している。

目的:
- `transpile_cli` typed shim の focused C++ contract を、現行の `generated/native` direct ownership layout に揃える。
- 削除済み `cpp/pytra` wrapper を再要求しない source contract に直す。

対象:
- `test/unit/common/test_py2x_entrypoints_contract.py`
- 必要なら関連 plan / TODO / archive 記録

非対象:
- `transpile_cli.py` 自体の挙動変更
- C++ runtime packaging の再設計
- `backend_registry_static` など別 compiler module の一括見直し

受け入れ基準:
- focused contract test が `src/runtime/cpp/pytra/compiler/transpile_cli.h` の不在を expected state として扱う。
- 同テストが `src/runtime/cpp/generated/compiler/transpile_cli.h` と `src/runtime/cpp/generated/compiler/transpile_cli.cpp` の live contract を検証する。
- typed shim が `_front.load_east3_document_typed(...)` へ直送していることを引き続き guard する。

確認コマンド:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 /workspace/Pytra/test/unit/common/test_py2x_entrypoints_contract.py -k typed_shim_skips_legacy_wrapper`
- `python3 /workspace/Pytra/tools/check_todo_priority.py`
- `git -C /workspace/Pytra diff --check`

分解:
- [ ] [ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01] `transpile_cli` typed C++ contract を checked-in `cpp/pytra` wrapper 前提から外し、`generated/native` direct ownership header/source に揃える。
- [x] [ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01-S1-01] stale contract surface と close 条件を plan / TODO に固定する。
- [x] [ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01-S2-01] focused contract test を live tree に合わせて更新し、targeted test を green に戻す。
- [ ] [ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01-S3-01] TODO / plan / archive を同期して close 条件を固定する。

決定ログ:
- 2026-03-13: TODO 空き後の follow-up P0 として起票。live tree では `generated/compiler/transpile_cli.{h,cpp}` が存在し、`cpp/pytra/compiler/transpile_cli.h` は削除済みなので、task は runtime layout を変えるのではなく source contract の stale assumption を消すことに限定する。
- 2026-03-13: `S2-01` では `test_compiler_transpile_cli_typed_shim_skips_legacy_wrapper()` を更新し、削除済み `src/runtime/cpp/pytra/compiler/transpile_cli.h` を expected-missing として扱うようにした。代わりに `generated/compiler/transpile_cli.h` の native include と `generated/compiler/transpile_cli.cpp` の live ownership/source contract を直接検証する。
