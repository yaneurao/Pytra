<a href="../../../en/plans/archive/20260313-p0-link-facade-linked-program-module-import.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `LinkedProgramModule` import を `toolchain.link` facade に揃える

最終更新: 2026-03-13

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01`

背景:
- `toolchain.link` facade はすでに `LinkedProgramModule` を export している。
- それにもかかわらず、[`tools/unittest/tooling/test_py2x_cli.py`](/workspace/Pytra/tools/unittest/tooling/test_py2x_cli.py) は `src.toolchain.link.program_model` を直接 import している。
- 同じ consumer lane でも [`src/ir2lang.py`](/workspace/Pytra/src/ir2lang.py) はすでに facade import へ揃っており、`py2x` tooling test だけが reach-through import を残している。

目的:
- `test_py2x_cli.py` の `LinkedProgramModule` import を `src.toolchain.link` facade 経由へ揃える。
- source contract を追加し、`program_model` への direct reach-through が戻ったら fail-fast にする。

対象:
- `tools/unittest/tooling/test_py2x_cli.py`
- `tools/unittest/common/test_py2x_entrypoints_contract.py`
- `docs/ja/todo/index.md` と英語ミラー

非対象:
- `toolchain.link.program_model` 内部構造の変更
- `LinkedProgram` / `LINK_INPUT_SCHEMA` など他の export の一括整理
- runtime / selfhost の import graph 再編

受け入れ基準:
- `test_py2x_cli.py` が `LinkedProgramModule` を `src.toolchain.link` facade から import する。
- source contract が `src.toolchain.link.program_model` direct import の再発を検知できる。
- focused unit が green になる。

確認コマンド:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 /workspace/Pytra/tools/unittest/common/test_py2x_entrypoints_contract.py`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 /workspace/Pytra/tools/unittest/tooling/test_py2x_cli.py`
- `python3 /workspace/Pytra/tools/check/check_todo_priority.py`
- `git -C /workspace/Pytra diff --check`

分解:
- [x] [ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01] `test_py2x_cli.py` の `LinkedProgramModule` import を `src.toolchain.link` facade 経由へ揃え、tooling consumer が `program_model` へ直接 reach-through しない状態を固定する。
- [x] [ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01-S1-01] facade import を要求する source contract と TODO/plan baseline を追加する。
- [x] [ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01-S2-01] `test_py2x_cli.py` の import を facade 経由へ切り替え、focused unit を green に戻す。
- [x] [ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01-S3-01] TODO / plan / archive を同期して close 条件を固める。

決定ログ:
- 2026-03-13: TODO 空き後の follow-up P0 として、`LinkedProgramModule` の tooling consumer に残る direct `program_model` import を facade import へ揃える task を起票した。scope は `test_py2x_cli.py` の consumer lane に限定する。
- 2026-03-13: `S1-01/S2-01` では `test_py2x_cli.py` の import を `from src.toolchain.link import LinkedProgramModule` に切り替え、source contract は `test_py2x_entrypoints_contract.py` に追加して facade import の再発防止を固定した。
- 2026-03-13: `S3-01` では active TODO / plan / archive を同期し、close 条件を「`test_py2x_cli.py` が `LinkedProgramModule` を `src.toolchain.link` facade から import し、source contract と focused tooling unit が green」で固定した。`program_model` 内部の export 再編は次 task へ持ち越す。
