<a href="../../../en/plans/archive/20260311-p0-relative-import-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: 相対 import (`from .m import x`) 正式対応

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-RELATIVE-IMPORT-SUPPORT-01`

背景:
- いまの self-hosted parser は `from .xxx import ...` を `relative import is not supported` として即 reject する。
- frontend CLI もその例外文字列を `kind=unsupported_import_form` へ変換しており、Pytra-NES のような multi-file 実験が import 段階で止まる。
- wildcard import はすでに対応済みなので、相対 import だけが import graph / export table / diagnostics から取り残されている。
- parser 側だけ受理しても `meta.import_bindings` / `meta.import_symbols` / `qualified_symbol_refs` / import graph が raw `.helper` のままだと backend へ安全に渡せない。

目的:
- `from .m import x` / `from ..pkg import y` / `from . import x` / `from .m import *` を multi-file 変換で正式対応する。
- static に解決できない relative import は fail-closed で `input_invalid` を返し、曖昧な生成コードを出さない。
- absolute import / wildcard import / import cycle / missing module / duplicate binding の既存契約を壊さない。

対象:
- self-hosted parser の relative `from-import` 受理
- EAST / import metadata の relative module 正規化
- import graph 解析時の relative module path 解決
- CLI 診断 (`unsupported_import_form` / `missing_module` / `duplicate_binding`) の契約更新
- representative unit / CLI 回帰
- `spec-user.md` / `spec-import.md` の同期

非対象:
- Python 非合法構文である `import .m`
- runtime 動的 import (`__import__`, `importlib`)
- `__package__` / `__main__` の完全互換
- namespace package 完全互換

方針:
- Stage 1 は「entry root 配下の静的 module_id」に対する relative normalize を正本とする。
- `from .m import x` の解決基準は importing file path と entry root から決まる static `module_id` であり、runtime の `__package__` は見ない。
- relative import が root より上へ出る場合は `kind=unsupported_import_form` で fail-closed とする。
- relative import の対象 module が存在しない場合は、正規化後の absolute module_id に対して `kind=missing_module` を返す。
- parser は raw relative module text を受理し、frontend の module map 構築時に absolute module_id へ正規化する。
- frontend 後段では `ImportFrom.module` / `meta.import_bindings[].module_id` / `meta.import_symbols[*].module` / `meta.qualified_symbol_refs[*].module_id` を absolute module_id へ揃える。

受け入れ基準:
- `main.py` と同じディレクトリの `helper.py` に対する `from .helper import f` が成功すること。
- `pkg/main.py` から `from ..common import f` が正しく absolute module_id へ正規化されること。
- `from .helper import *` が既存 wildcard import contract のまま解決されること。
- `from ...oops import f` のように root より上へ出る relative import は `kind=unsupported_import_form` で停止すること。
- relative import の missing module / missing symbol / duplicate binding が absolute import と同じ分類で報告されること。
- 既存の wildcard import 回帰、import cycle 回帰、reserved conflict 回帰を壊さないこと。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

分解:
- [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S1-01] relative import の syntax / diagnostics / root escape policy を spec と plan に固定する。
- [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S2-01] self-hosted parser が relative `from-import` を受理し、raw module text と `ImportFrom.level` を保持できるようにする。
- [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S2-02] frontend の module map 構築で relative module を absolute module_id へ正規化し、EAST / import meta 全体へ反映する。
- [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S2-03] import graph 診断を relative import 正式対応の contract に更新し、root escape と missing module を区別して fail-closed にする。
- [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S3-01] representative CLI / unit 回帰（正常系・missing・duplicate・root escape・wildcard）を追加する。
- [x] [ID: P0-RELATIVE-IMPORT-SUPPORT-01-S3-02] `spec-user.md` / `spec-import.md` / tutorial の import 記述を更新する。

決定ログ:
- 2026-03-11: ユーザー要望により relative import を `P0` へ昇格した。最初の互換目標は Python runtime 完全互換ではなく、entry root 配下の deterministic static normalize とする。
- 2026-03-11: `S1-01` として syntax / diagnostics / root escape policy を固定した。Stage 1 canonical surface は `from .m import x` / `from ..pkg import y` / `from . import x` / `from .m import *` とし、`import .m` は非対象、root escape は `kind=unsupported_import_form`、正規化後 missing module は `kind=missing_module` とする。
- 2026-03-11: `S2-01` として self-hosted parser の `from-import` head parser を共通 helper 化し、`from .helper import f` と `from . import f` を raw module text のまま受理するようにした。frontend 正規化前の EAST / import metadata では `module=".helper"` / `"."` を保持し、`ImportFrom.level` のみ parser 段階で付与する。
- 2026-03-11: `S2-02/S2-03` として import graph が relative `from-import` を importer path + entry root から absolute `module_id` へ正規化し、module EAST map 生成時に `ImportFrom.module` / `meta.import_bindings` / `meta.import_symbols` / `meta.qualified_symbol_refs` / `meta.import_resolution` 全体を rewrite するようにした。root escape は `unsupported_import_form`、正規化後 missing は `missing_module` に分類する。
- 2026-03-11: `S3-01/S3-02` として sibling success、relative wildcard success、missing relative module、duplicate relative binding、root escape の representative regression を追加し、tutorial の import 制約文言を current contract に同期した。
