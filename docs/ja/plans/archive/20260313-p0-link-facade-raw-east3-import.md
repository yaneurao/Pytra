<a href="../../../en/plans/archive/20260313-p0-link-facade-raw-east3-import.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `validate_raw_east3_doc` の external import を `toolchain.link` facade に揃える

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-LINK-FACADE-RAW-EAST3-IMPORT-01`

背景:
- `toolchain.link` facade はすでに `validate_raw_east3_doc` を export している。
- それにもかかわらず、`src/toolchain/ir/east3.py` と focused regression の [`test/unit/common/test_frontend_type_expr.py`](/workspace/Pytra/test/unit/common/test_frontend_type_expr.py) は `toolchain.link.program_validator` を直接 import している。
- package facade が存在するのに external consumer 側で submodule reach-through が残ると、`program_validator` の内部配置に不要な結合が残り、前タスクで揃えた facade 方針とも不整合になる。

目的:
- external consumer として残っている `validate_raw_east3_doc` の direct submodule import を `toolchain.link` facade に揃える。
- runtime regression と source contract を追加し、今後 reach-through import が戻ったら fail-fast にする。

対象:
- `src/toolchain/ir/east3.py`
- `test/unit/common/test_frontend_type_expr.py`
- 必要なら `test/unit/common/test_py2x_entrypoints_contract.py`

非対象:
- `toolchain.link` package 内部での internal import 再編
- `validate_raw_east3_doc` の挙動変更
- 他 validator helper の一括 facade cleanup

受け入れ基準:
- `toolchain.ir.east3` が `validate_raw_east3_doc` を `toolchain.link` facade から import する。
- focused regression が facade import 前提で green になる。
- source contract が `toolchain.link.program_validator` 直接 import の再発を検知できる。

確認コマンド:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 test/unit/common/test_frontend_type_expr.py`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 test/unit/common/test_py2x_entrypoints_contract.py -k dynamic_carrier_seams_are_explicitly_isolated`
- `python3 /workspace/Pytra/tools/check_todo_priority.py`
- `git -C /workspace/Pytra diff --check`

分解:
- [x] [ID: P0-LINK-FACADE-RAW-EAST3-IMPORT-01] `toolchain.ir.east3` と focused test からの `validate_raw_east3_doc` import を `toolchain.link` facade 経由へ揃え、external consumer が `toolchain.link.program_validator` へ直接 reach-through しない状態を固定する。
- [x] [ID: P0-LINK-FACADE-RAW-EAST3-IMPORT-01-S1-01] facade import を要求する focused regression / source contract を追加し、current reach-through import surface を fail-fast に固定する。
- [x] [ID: P0-LINK-FACADE-RAW-EAST3-IMPORT-01-S2-01] `toolchain.ir.east3` と focused test の import を facade 経由へ切り替え、targeted unit を green に戻す。
- [x] [ID: P0-LINK-FACADE-RAW-EAST3-IMPORT-01-S3-01] TODO / plan / decision log を同期して close 条件を固める。

決定ログ:
- 2026-03-13: TODO 空き後の follow-up P0 として、`validate_raw_east3_doc` の external consumer に残る reach-through import を縮退する task を起票した。`toolchain.link` 内部の import graph には踏み込まず、external surface の統一に限定する。
- 2026-03-13: `S1-01/S2-01` では `toolchain.ir.east3` を facade import へ切り替えつつ、module-init cycle を避けるため local helper `_validate_raw_east3_via_link()` を置いた。runtime regression は `test_frontend_type_expr.py`、source contract は `test_py2x_entrypoints_contract.py` に固定した。
- 2026-03-13: `S3-01` では active TODO / plan / archive を同期し、close 条件を「`toolchain.ir.east3` が `toolchain.link` facade から `validate_raw_east3_doc` を引き、`test_frontend_type_expr.py` と `test_py2x_entrypoints_contract.py` が両方 green」に固定した。module-init cycle を避ける local helper 方式はこの task の accepted end state とする。
