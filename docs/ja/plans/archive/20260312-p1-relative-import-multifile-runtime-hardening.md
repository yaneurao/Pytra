<a href="../../../en/plans/archive/20260312-p1-relative-import-multifile-runtime-hardening.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: relative import の multi-file runtime smoke hardening

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01`

背景:
- relative import 自体は既に frontend / import graph / CLI contract 上で実装済みで、`py2x.py` の nested package project-style transpile regression も存在する。
- ただし、Pytra-NES のような package tree を `--multi-file` で C++ に出し、そのまま build/run する representative regression はまだ薄い。
- 現状の回帰は transpile 完了や generated source の一部確認に寄っており、runtime link / namespace / manifest build まで含む end-to-end 契約が弱い。

目的:
- nested package の relative import chain が `py2x.py --target cpp --multi-file` から `tools/build_multi_cpp.py`、実行まで通る representative contract を固定する。
- relative import 実装済み状態を Pytra-NES 型の project layout で再確認し、再退行を早期検知できるようにする。

対象:
- nested package relative import の multi-file C++ build/run regression 追加
- bare parent import / package-local relative import の runtime smoke 強化
- 必要なら generated manifest / module label / namespace の小修正
- TODO / plan の current contract 同期

非対象:
- relative import の新構文追加
- Rust / C# / 他 backend への同時展開
- import graph 実装の大規模再設計

受け入れ基準:
- `from .cpu.runner import run` と `from ..util.bits import low_nibble` を含む nested package 入力が `--multi-file` で build/run まで成功する。
- `from .. import helper` の bare parent relative import も `--multi-file` で build/run まで成功する。
- relative import root escape の fail-closed contract を壊さない。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative`
- `python3 tools/build_selfhost.py`
- `git diff --check`

決定ログ:
- 2026-03-12: relative import 自体は既に supported なので、新機能追加ではなく Pytra-NES 型 project layout の multi-file runtime smoke hardening を `P1` として起票した。
- 2026-03-12: representative runtime smoke は `from .cpu.runner import run` + `from ..util.bits import low_nibble` と `from .. import helper` の 2 系統を C++ multi-file build/run まで固定する方針にした。
- 2026-03-12: `from .. import helper` は validation 時に plain symbol binding ではなく module alias binding へ正規化し、multi-file C++ では namespace-qualified module call として扱う契約に揃えた。

## 分解

- [x] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01-S1-01] current gap を plan / TODO に固定し、nested package runtime smoke の代表ケースを決める。
- [x] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01-S2-01] nested package relative import chain の multi-file C++ build/run regression を追加した。
- [x] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01-S2-02] bare parent relative import の multi-file C++ build/run regression を追加した。
- [x] [ID: P1-RELATIVE-IMPORT-MULTIFILE-RUNTIME-HARDENING-01-S3-01] docs / plan / TODO と focused regression を current contract に同期して task を閉じた。
