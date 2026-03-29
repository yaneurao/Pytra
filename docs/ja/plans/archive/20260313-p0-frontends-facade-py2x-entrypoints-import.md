<a href="../../../en/plans/archive/20260313-p0-frontends-facade-py2x-entrypoints-import.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `py2x` entrypoint import を `toolchain.frontends` facade に揃える

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01`

背景:
- canonical な Python frontend 実装は `toolchain.frontends` 配下へ寄せているが、[`src/py2x.py`](/workspace/Pytra/src/py2x.py) と [`src/py2x-selfhost.py`](/workspace/Pytra/src/py2x-selfhost.py) はまだ `toolchain.compiler.transpile_cli` を直接 import している。
- [`src/toolchain/compiler/transpile_cli.py`](/workspace/Pytra/src/toolchain/compiler/transpile_cli.py) は compatibility shim であり、external entrypoint がこの shim にぶら下がると canonical import surface が曖昧なまま残る。
- [`src/toolchain/frontends/__init__.py`](/workspace/Pytra/src/toolchain/frontends/__init__.py) はすでに `add_common_transpile_args` と `load_east3_document_typed` を export しているが、`py2x.py` が使う `build_module_east_map` はまだ facade に載っていない。

目的:
- `toolchain.frontends` facade に `build_module_east_map` を加え、`py2x.py` / `py2x-selfhost.py` の frontend import を facade 経由へ揃える。
- source contract を追加し、entrypoint が再び `toolchain.compiler.transpile_cli` へ reach-through しないようにする。

対象:
- `src/toolchain/frontends/python_frontend.py`
- `src/toolchain/frontends/__init__.py`
- `src/py2x.py`
- `src/py2x-selfhost.py`
- `tools/unittest/common/test_py2x_entrypoints_contract.py`
- 必要なら `tools/unittest/tooling/test_py2x_cli.py`

非対象:
- `toolchain.frontends.transpile_cli` 実装そのものの仕様変更
- `toolchain.compiler.transpile_cli` の削除
- frontend 以外の compiler/backend registry import 整理

受け入れ基準:
- `toolchain.frontends` facade が `build_module_east_map` を export する。
- `py2x.py` / `py2x-selfhost.py` が frontend helper を `toolchain.frontends` facade から import する。
- source contract が `toolchain.compiler.transpile_cli` 直 import の再発を検知し、focused test が green になる。

確認コマンド:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 /workspace/Pytra/tools/unittest/common/test_py2x_entrypoints_contract.py -k dynamic_carrier`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 /workspace/Pytra/tools/unittest/tooling/test_py2x_cli.py`
- `python3 /workspace/Pytra/tools/check/check_todo_priority.py`
- `git -C /workspace/Pytra diff --check`

分解:
- [x] [ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01] `py2x.py` / `py2x-selfhost.py` の frontend import を `toolchain.compiler.transpile_cli` から `toolchain.frontends` facade へ揃え、entrypoint consumer が compat shim へ reach-through しない状態を固定する。
- [x] [ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01-S1-01] stale import surface と close 条件を plan / TODO に固定する。
- [x] [ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01-S2-01] `toolchain.frontends` facade export と entrypoint import を更新し、source contract / focused test を green に戻す。
- [x] [ID: P0-FRONTENDS-FACADE-PY2X-ENTRYPOINTS-IMPORT-01-S3-01] TODO / plan / archive を同期して close 条件を固定する。

決定ログ:
- 2026-03-13: TODO 空き後の follow-up P0 として起票。scope は external entrypoint consumer に限定し、`toolchain.compiler.transpile_cli` compat shim の削除までは踏み込まない。
- 2026-03-13: `S2-01` では `python_frontend.py` と `toolchain.frontends` facade に `build_module_east_map` を通し、`py2x.py` / `py2x-selfhost.py` の frontend import を facade へ切り替えた。source contract は `test_py2x_entrypoints_contract.py` に追加し、compat shim 直 import の再発を fail-fast にした。
- 2026-03-13: `S3-01` では active TODO / plan / archive を同期し、close 条件を「`toolchain.frontends` facade が `build_module_east_map` を export し、`py2x.py` / `py2x-selfhost.py` が compat shim ではなく facade を import し、source contract と `test_py2x_cli.py` が green」で固定した。
