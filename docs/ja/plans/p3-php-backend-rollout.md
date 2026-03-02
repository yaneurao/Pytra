# P3: PHP backend 追加（EAST3 -> PHP native）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P3-PHP-BACKEND-01`

背景:
- 追加言語の実装順は `Ruby -> Lua -> PHP` で合意済みで、Ruby/Lua は backend 導線が整備された。
- 現時点で PHP は変換対象言語に未対応であり、`py2<lang>` 系の多言語運用から抜けている。
- 既存方針として、sidecar ではなく `EAST3` から各言語へ native 直生成する路線を採用している。

目的:
- `py2php.py` を入口として `EAST3 -> PHP` の native 変換経路を追加する。
- runtime helper は生成コードへの inline 埋め込みではなく、PHP runtime ファイル分離で運用する。
- `sample/` / `test/fixtures` で transpile と parity の基本導線を確立する。

対象:
- `src/py2php.py`（新規）
- `src/hooks/php/emitter/`（新規）
- `src/runtime/php/pytra/`（新規 runtime）
- `tools/check_py2php_transpile.py`（新規）
- `tools/runtime_parity_check.py`（PHP target 追加）
- `tools/regenerate_samples.py`（php 出力先追加）
- `sample/php/*`（再生成）
- `test/unit/test_py2php_smoke.py`（新規）
- `docs/ja/how-to-use.md` / `docs/ja/spec/spec-user.md`（導線追記）

非対象:
- PHP backend の selfhost 化（P4 の別タスクで管理）
- 高度最適化（EAST3 optimizer 強化は別タスク）
- フロントエンド拡張（Python 以外からの入力）

受け入れ基準:
- `src/py2php.py` で EAST3 入力から PHP 生成が通る。
- 生成コードが runtime 分離方式（`require` / `include`）で実行可能。
- `test/fixtures` を対象に `check_py2php_transpile.py` が安定通過する。
- `sample/php` が再生成され、代表ケースで parity が通る（少なくとも `01/03/06/16/18`）。
- docs に PHP backend の使い方と制約が反映される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2php_smoke.py' -v`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/regenerate_samples.py --langs php --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets php --ignore-unstable-stdout 01_mandelbrot 03_julia_set 06_julia_parameter_sweep 16_glass_sculpture_chaos 18_parser_combinator`

決定ログ:
- 2026-03-02: ユーザー指示により、PHP 対応を `P3` として計画化し、`Ruby -> Lua -> PHP` 順の次段として起票した。

## 分解

- [ ] [ID: P3-PHP-BACKEND-01-S1-01] PHP backend のスコープ（対応構文・非対応構文・runtime 分離契約）を確定する。
- [ ] [ID: P3-PHP-BACKEND-01-S1-02] `src/py2php.py` と profile loader を追加し、CLI 導線を確立する。
- [ ] [ID: P3-PHP-BACKEND-01-S2-01] PHP native emitter 骨格を実装し、関数・条件分岐・ループ・基本式の出力を通す。
- [ ] [ID: P3-PHP-BACKEND-01-S2-02] class/inheritance と container 操作（list/dict/tuple 相当）の最低限 lower を実装する。
- [ ] [ID: P3-PHP-BACKEND-01-S2-03] runtime helper を `src/runtime/php/pytra/` へ分離し、生成コードから参照する方式へ統一する。
- [ ] [ID: P3-PHP-BACKEND-01-S3-01] `test_py2php_smoke.py` と `check_py2php_transpile.py` を追加し、回帰検知導線を整備する。
- [ ] [ID: P3-PHP-BACKEND-01-S3-02] `runtime_parity_check` と `regenerate_samples` に PHP を統合し、`sample/php` を再生成する。
- [ ] [ID: P3-PHP-BACKEND-01-S3-03] docs（how-to-use/spec/README 系）の PHP backend 記載を更新し、利用導線を固定する。
