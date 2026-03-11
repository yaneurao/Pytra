# P1: `toolchain.ir.core` の import hub を縮小する

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-IR-CORE-IMPORT-SURFACE-01`

背景:
- `P1-IR-CORE-DECOMPOSITION-01` と `P2-EAST-CORE-MODULARIZATION-01` により `core.py` 自体は 214 行の thin facade まで縮小した。
- ただし `core.py` は依然として 150 超の `toolchain.ir.*` helper import を抱え、split 済み module や一部 test / entrypoint が `toolchain.ir.core` を import hub として使い続けている。
- この状態だと、機能分割後も internal dependency が `core.py` に再集中し、循環依存の温床と public/private surface の曖昧さが残る。

目的:
- `toolchain.ir.core` を「外部向け thin facade」として再定義し、internal split module からの依存を段階的に専用 module へ移す。
- `convert_path` / `convert_source_to_east*` / `EastBuildError` などの public surface と、internal helper import を明確に分離する。

対象:
- `src/toolchain/ir/core.py`
- `src/toolchain/ir/core_entrypoints.py`
- `src/toolchain/ir/core_expr_*.py`
- `src/toolchain/ir/core_module_parser.py`
- `src/toolchain/ir/core_stmt_parser.py`
- `src/toolchain/compiler/east_parts/*`
- `test/unit/ir/test_east_core_source_contract_*.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p1-ir-core-import-surface-pruning.md` / `docs/en/plans/p1-ir-core-import-surface-pruning.md`

非対象:
- EAST/EAST3 の新仕様追加
- runtime / backend の機能追加
- `core.py` façade 自体の再肥大化を伴う re-export 追加

受け入れ基準:
- internal split module が `toolchain.ir.core` を経由せず dedicated module を直接 import する代表 lane を持つ。
- `toolchain.ir.core` に残す public surface が plan に明記され、source-contract で固定される。
- representative regression として `test_east_core*.py`、`test_prepare_selfhost_source.py`、`tools/build_selfhost.py` が通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

分解:
- [x] [ID: P1-IR-CORE-IMPORT-SURFACE-01-S1-01] `toolchain.ir.core` importers を棚卸しし、`public_entrypoint` / `internal_split_module` / `tests_only` / `bridge_compat` に分類する。
- [x] [ID: P1-IR-CORE-IMPORT-SURFACE-01-S1-02] `toolchain.ir.core` に残す public surface と internal import 禁止方針を決める。
- [ ] [ID: P1-IR-CORE-IMPORT-SURFACE-01-S2-01] internal split module の代表 lane を dedicated module import へ移し、`core.py` 経由依存を減らす。
- [ ] [ID: P1-IR-CORE-IMPORT-SURFACE-01-S2-02] tests / helper lane の import も public surface と dedicated module へ揃える。
- [ ] [ID: P1-IR-CORE-IMPORT-SURFACE-01-S3-01] `toolchain.ir.core` import surface guard を追加し、internal import の再流入を fail-fast にする。
- [ ] [ID: P1-IR-CORE-IMPORT-SURFACE-01-S4-01] representative regression を再実行して非退行を確認し、完了後は archive へ移す。

決定ログ:
- 2026-03-11: `P1-IR-CORE-DECOMPOSITION-01` 完了後も `core.py` は `toolchain.ir.*` import を 157 本抱え、internal split module からの `from toolchain.ir.core import ...` が残っているため、本 task を起票した。
- 2026-03-11: 初回 inventory では importers を `public_entrypoint`、`internal_split_module`、`tests_only`、`bridge_compat` の 4 区分で扱う。現時点の代表例は `frontends/transpile_cli.py` / backend smoke tests、`core_entrypoints.py` / `core_string_semantics.py` / `core_module_parser.py` / `core_stmt_parser.py` / `core_expr_primary.py` / `core_expr_lowered.py` / `core_expr_call_args.py`、`test_east_core_source_contract_*`、`compiler/east_parts/__init__.py` である。
- 2026-03-11: `toolchain.ir.core` の facade export は `CORE_PUBLIC_FACADE_EXPORTS = (EastBuildError, convert_path, convert_source_to_east, convert_source_to_east_with_backend)` を canonical とし、`convert_source_to_east_self_hosted` / `_sh_parse_stmt_block*` / `INT_TYPES` / `FLOAT_TYPES` は `CORE_BRIDGE_COMPAT_EXPORTS` に隔離して暫定維持する。
- 2026-03-11: `toolchain.ir.core_*` の internal split module は `toolchain.ir.core` を import hub として新規追加してはいけない。既存 lane は `S2-01/S2-02` で dedicated module import へ移す前提で、`public_entrypoint` と `bridge_compat` のみを facade 利用の許容対象とする。
- 2026-03-11: `S2-01` の representative bundle として `core_entrypoints` / `core_string_semantics` / `core_expr_primary` / `core_expr_lowered` / `core_expr_call_args` は `core_module_parser` / `core_expr_shell` を直接 import する形へ移し、`toolchain.ir.core` 経由の hub 依存を 5 lane まとめて外した。
