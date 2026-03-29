<a href="../../../en/plans/archive/20260311-p1-ir-entrypoint-facade-pruning.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: `toolchain.ir.core` facade importer を剥がす

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-IR-ENTRYPOINT-FACADE-PRUNING-01`

背景:
- `P1-IR-CORE-DECOMPOSITION-01` と `P1-IR-CORE-IMPORT-SURFACE-01` により、`src/toolchain/ir/core.py` は `core_entrypoints` と stmt/module bridge だけを束ねる thin facade まで縮小した。
- ただし compiler frontend と representative test/backend lane の一部は、依然として `toolchain.ir.core` から `convert_path` / `convert_source_to_east_with_backend` / `EastBuildError` を import している。
- `core.py` を互換 facade として残す方針自体は妥当だが、internal compiler / regression lane までそこに依存すると、entrypoint surface と compatibility surface の境界が再び曖昧になる。

目的:
- internal compiler と representative regression lane を `toolchain.ir.core_entrypoints` へ寄せ、`toolchain.ir.core` を外部互換 facade としてのみ残す。
- `core facade` 依存の再流入を source-contract で fail-fast にする。

対象:
- `src/toolchain/frontends/transpile_cli.py`
- `src/toolchain/ir/core.py`
- `src/toolchain/ir/core_entrypoints.py`
- representative test/backend importers (`tools/unittest/common/*`, `tools/unittest/emit/*`, `tools/unittest/ir/test_east2_to_east3_lowering.py`)
- `tools/unittest/ir/test_east_core_source_contract_import_surface.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p1-ir-entrypoint-facade-pruning.md` / `docs/en/plans/p1-ir-entrypoint-facade-pruning.md`

非対象:
- parser/IR/runtime の仕様変更
- `toolchain.ir.core` の public export 削除
- backend 実装の機能追加

受け入れ基準:
- `src/toolchain/frontends/transpile_cli.py` が `toolchain.ir.core` ではなく `toolchain.ir.core_entrypoints` を import する。
- representative test/backend lane が `convert_path` / `convert_source_to_east_with_backend` / `EastBuildError` を `core_entrypoints` から取得する。
- `test_east_core_source_contract_import_surface.py` が `src` 側の `toolchain.ir.core` importer を 0 件に固定し、representative test lane の facade 依存再流入も fail-fast にする。
- representative regression (`test_east_core*.py`, `test_prepare_selfhost_source.py`, `build_selfhost.py`) が通る。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/check_transpiler_version_gate.py`
- `python3 tools/run/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

分解:
- [x] [ID: P1-IR-ENTRYPOINT-FACADE-PRUNING-01-S1-01] residual importer を棚卸しし、`src_compiler` / `representative_tests` / `compat_only` に分類する。
- [x] [ID: P1-IR-ENTRYPOINT-FACADE-PRUNING-01-S1-02] `toolchain.ir.core` は external compatibility facade、internal compiler / representative regression は `core_entrypoints` を使う方針を固定する。
- [x] [ID: P1-IR-ENTRYPOINT-FACADE-PRUNING-01-S2-01] `transpile_cli` と representative test/backend importer を `core_entrypoints` へ寄せる。
- [x] [ID: P1-IR-ENTRYPOINT-FACADE-PRUNING-01-S2-02] facade 依存の再流入を source-contract で fail-fast にする。
- [x] [ID: P1-IR-ENTRYPOINT-FACADE-PRUNING-01-S3-01] representative regression と version gate を通して安定化し、完了後は archive へ移す。

決定ログ:
- 2026-03-11: 初版作成。現時点の residual importer は `src/toolchain/frontends/transpile_cli.py`、`tools/unittest/common/test_self_hosted_signature.py`、backend smoke 11 本、`tools/unittest/emit/cpp/test_east3_cpp_bridge.py`、`tools/unittest/ir/test_east2_to_east3_lowering.py` である。
- 2026-03-11: `toolchain.ir.core` は public compatibility facade として維持するが、internal compiler と representative regression lane は canonical に `toolchain.ir.core_entrypoints` を使う。`core.py` への依存は external user compatibility のみを想定し、internal source-contract からは再流入を禁止する。
- 2026-03-11: `S2-01` として `src/toolchain/frontends/transpile_cli.py`、`test_self_hosted_signature.py`、backend smoke 11 本、`test_east3_cpp_bridge.py`、`test_east2_to_east3_lowering.py` の import を `toolchain.ir.core_entrypoints` へ寄せた。
- 2026-03-11: `S2-02` として `test_east_core_source_contract_import_surface.py` を更新し、`src` 側の `toolchain.ir.core` importer は 0 件、representative test/backend lane の facade importer も 0 件で固定した。
- 2026-03-11: `S3-01` として representative regression (`test_east_core*.py`, `test_prepare_selfhost_source.py`, `test_self_hosted_signature.py`, `test_east3_cpp_bridge.py`, `test_east2_to_east3_lowering.py`) と version gate / selfhost build を再実行し、archive へ移した。
