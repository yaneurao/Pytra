<a href="../../../en/plans/archive/20260311-p0-relative-import-package-root-01.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: package-style relative import の root 推定を安定化する

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RELATIVE-IMPORT-PACKAGE-ROOT-01`

背景:
- 現在の relative import support は `from .helper import f` の sibling case は通るが、package 内 submodule からの `from ..util import g` はまだ `unsupported_import_form` で落ちる。
- 実装上は [transpile_cli.py](/workspace/Pytra/src/toolchain/frontends/transpile_cli.py) の `rewrite_relative_imports_in_module_east_map()` と `analyze_import_graph()` が `entry_path.parent` を root とみなし、package root を `__init__.py` chain から推定していない。
- Pytra-NES のような package-style project は `pkg/sub/main.py -> from ..util import ...` を多用するため、この gap を先に埋めないと実験が止まる。

目的:
- package root を `__init__.py` chain から推定し、package 内の parent relative import を multi-file transpile で正式に通す。
- root escape は引き続き fail-closed に保ち、current diagnostics contract を壊さない。

対象:
- entry file から package root を推定する shared helper
- `rewrite_relative_imports_in_module_east_map()` / `analyze_import_graph()` の root 決定更新
- parent relative import success / root escape failure の representative CLI と metadata regression
- TODO / plan / English mirror の整合

非対象:
- import graph algorithm 自体の変更
- wildcard import / absolute import の仕様変更
- namespace package や `pyproject.toml` ベース root 推定

受け入れ基準:
- `pkg/sub/main.py` から `from ..util import f` が multi-file transpile で通ること。
- module metadata / import binding は normalized absolute module_id に rewrite されること。
- package root を越える `from ...bad import x` は引き続き `unsupported_import_form` で fail-closed すること。
- representative CLI / metadata regression と selfhost build が通ること。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 tools/unittest/tooling/test_py2x_cli.py -k relative_import -v`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/check_transpiler_version_gate.py`
- `python3 tools/run/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

決定ログ:
- 2026-03-11: TODO 空き後の次タスクとして起票。probe では sibling relative import は通る一方、`pkg2/sub/main.py -> from ..util import two` は `unsupported_import_form` で落ちた。v1 は `__init__.py` chain に基づく package root 推定だけを対象にする。
- 2026-03-11: representative gap を固定した。`pkg/main.py -> from .helper import f` は通るが、`pkg/sub/main.py -> from ..util import two` は `entry_path.parent` を root とみなすため `unsupported_import_form` で落ちる。
- 2026-03-11: `resolve_import_graph_entry_root()` を追加し、`pkg/sub/main.py -> from ..util import two` を package root `pkg` 基準で `util` へ rewrite するようにした。package root escape は引き続き `unsupported_import_form` を維持する。
- 2026-03-11: `S3-01` として docs/archive を更新し、package-style parent relative import success と root escape fail-closed の representative contract を archive へ移した。

## 分解

- [x] [ID: P0-RELATIVE-IMPORT-PACKAGE-ROOT-01-S1-01] current root 推定 gap と representative package layout を plan/TODO に固定する。
- [x] [ID: P0-RELATIVE-IMPORT-PACKAGE-ROOT-01-S2-01] package root 推定 helper を追加し、`rewrite_relative_imports_in_module_east_map()` / `analyze_import_graph()` を helper 経由へ切り替える。
- [x] [ID: P0-RELATIVE-IMPORT-PACKAGE-ROOT-01-S2-02] parent relative import success / root escape failure の CLI / metadata regression を追加する。
- [x] [ID: P0-RELATIVE-IMPORT-PACKAGE-ROOT-01-S3-01] docs / archive を更新して閉じる。
