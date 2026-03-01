# P1: EAST2 を最初の共通 IR として再定義（Python 依存排除）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-EAST2-COMMON-IR-01`

背景:
- 現状の EAST2/EAST2->EAST3 連携には、`py_*` 命名や Python builtin 名前提の契約が残っており、IR 境界として Python 依存が混入している。
- 将来的に複数フロントエンド（Python 以外）を受ける場合、最初の共通 IR は言語非依存である必要がある。
- EAST2 が中立でないと、backend 側へ source 言語依存が漏れ、最適化・検証・保守が難しくなる。

目的:
- EAST2 を「source 言語非依存の最初の共通 IR」として定義し直す。
- Python 固有仕様（builtin 解決、標準ライブラリ慣習、補助 runtime 名称）を frontend 境界へ隔離する。
- EAST2->EAST3 lowering は中立契約の消費者に限定する。

対象:
- `src/pytra/compiler/east_parts/east2.py`
- `src/pytra/compiler/east_parts/east2_to_east3_lowering.py`
- `src/pytra/compiler/east_parts/core.py`（frontend 境界の調整範囲）
- `docs/ja/spec/spec-east.md`（必要に応じて関連仕様追記）
- EAST2/EAST3 周辺の unit test

非対象:
- Ruby/Lua/PHP など新規 frontend 実装の同時着手
- EAST3 optimizer 全面改修
- 各 backend emitter の大規模最適化

受け入れ基準:
- EAST2 契約（ノード・メタ・lowering 入力条件）から Python 固有名称依存が除去される。
- Python 固有解決ロジックは frontend 側 adapter に局所化される。
- EAST2->EAST3 lowering が中立契約のみを参照して動作する。
- 既存 Python 入力の transpile/smoke が非退行で通過する。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_east*.py' -v`
- `python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

決定ログ:
- 2026-03-01: ユーザー指示により、「EAST2 を最初の共通 IR として運用するための Python 依存排除」を P1 で分割着手する方針を確定した。

## 分解

- [ ] [ID: P1-EAST2-COMMON-IR-01-S1-01] EAST2/EAST2->EAST3 に残る Python 依存契約（`py_*` runtime call、builtin 名直参照、型メタ前提）を棚卸しする。
- [ ] [ID: P1-EAST2-COMMON-IR-01-S1-02] EAST2 共通 IR 契約（ノード種別、演算子、メタ情報、診断と fail-closed 条件）を仕様化する。
- [ ] [ID: P1-EAST2-COMMON-IR-01-S2-01] Python 固有の builtins/std 解決を frontend adapter 層へ移管し、EAST2 契約から分離する。
- [ ] [ID: P1-EAST2-COMMON-IR-01-S2-02] `east2_to_east3_lowering.py` を中立契約ベースへ更新し、Python 名称分岐を縮小・除去する。
- [ ] [ID: P1-EAST2-COMMON-IR-01-S2-03] 既存入力非退行のための移行ブリッジ（暫定互換）を導入し、段階移行できる状態にする。
- [ ] [ID: P1-EAST2-COMMON-IR-01-S3-01] EAST2 への Python 依存再混入を検知する unit 回帰を追加する。
- [ ] [ID: P1-EAST2-COMMON-IR-01-S3-02] transpile/smoke/parity 代表ケースで非退行を確認し、決定ログへ記録する。
