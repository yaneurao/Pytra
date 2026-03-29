<a href="../../../en/plans/archive/20260312-p0-relative-import-paren-sibling-contract.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: 括弧付き sibling relative import contract 固定

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RELATIVE-IMPORT-PAREN-SIBLING-CONTRACT-01`

背景:
- Pytra-NES の最初の blocker として、`from .controller import (BUTTON_A, BUTTON_B, ...)` のような括弧付き sibling relative import が報告された。
- current tree では self-hosted parser がこの syntax を受理し、C++ multi-file smoke でも representative case が build/run まで通っている。
- ただし current support は parser regression と C++ smoke に散っており、CLI 代表ケースや contract/doc 上では明示的に固定されていない。
- TODO が空になったため、next practical hardening としてこの lane を `P0` で current support contract 化する。

目的:
- `from .module import (...)` 形式の sibling relative import を current support lane として明示する。
- Pytra-NES に近い representative case を CLI regression に追加し、parser / CLI / C++ multi-file の 3 面で崩れないようにする。
- docs / plan には「これは新機能追加ではなく、既に通る lane の contract 固定」であることを残す。

対象:
- parser behavior と CLI representative smoke の contract 固定
- TODO / plan / English mirror の同期
- 必要最小限の regression 追加

非対象:
- relative import の新規 semantics 追加
- wildcard relative import support
- parent relative import (`..`) の追加 hardening
- non-C++ backend rollout

受け入れ基準:
- parser regression で `from .controller import (...)` が継続して受理される。
- `py2x.py --target cpp` representative CLI test で、括弧付き sibling relative import project が transpile 成功する。
- 既存の C++ multi-file build/run smoke は引き続き通る。
- TODO / plan の ja/en ミラーが current support contract を記録する。

確認コマンド:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/ir -p 'test_east_core_parser_behavior_types.py' -k parenthesized_symbol_list`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_py2x_cli.py' -k parenthesized`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k sibling_relative_import_constants_build_and_run`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: current tree では parser と C++ smoke が既に通っていたため、本 task は implementation 追加ではなく contract 固定として起票した。
- 2026-03-12: representative case は Pytra-NES の報告に合わせて `from .controller import (BUTTON_A, BUTTON_B)` 形式を優先する。
- 2026-03-12: parser regression、`py2x.py --target cpp` の representative CLI regression、C++ multi-file build/run smoke、support docs の handoff wording がそろったので task 全体を完了として archive へ移す。

## 分解

- [x] [ID: P0-RELATIVE-IMPORT-PAREN-SIBLING-CONTRACT-01] 括弧付き sibling relative import を current support contract として固定する。
- [x] [ID: P0-RELATIVE-IMPORT-PAREN-SIBLING-CONTRACT-01-S1-01] active plan / TODO / English mirror を追加し、task の scope を固定する。
- [x] [ID: P0-RELATIVE-IMPORT-PAREN-SIBLING-CONTRACT-01-S2-01] representative CLI regression を追加して `py2x.py --target cpp` lane を固定する。
- [x] [ID: P0-RELATIVE-IMPORT-PAREN-SIBLING-CONTRACT-01-S2-02] parser / CLI / C++ smoke / docs の handoff を current support wording に揃えて task を閉じる。
