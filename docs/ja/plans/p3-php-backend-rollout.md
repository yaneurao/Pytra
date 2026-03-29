<a href="../../en/plans/p3-php-backend-rollout.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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
- `tools/check/check_py2php_transpile.py`（新規）
- `tools/check/runtime_parity_check.py`（PHP target 追加）
- `tools/gen/regenerate_samples.py`（php 出力先追加）
- `sample/php/*`（再生成）
- `tools/unittest/test_py2php_smoke.py`（新規）
- `docs/ja/how-to-use.md` / `docs/ja/spec/spec-user.md`（導線追記）

非対象:
- PHP backend の selfhost 化（P4 の別タスクで管理）
- 高度最適化（EAST3 optimizer 強化は別タスク）
- フロントエンド拡張（Python 以外からの入力）

仕様スコープ（S1-01 確定）:
- 対応構文（v1）:
  - 文: `Assign/AnnAssign/Expr/Return/If/While/ForCore(RuntimeIter, StaticRange)/Break/Continue/Pass`
  - 式: `Name/Constant/BinOp/UnaryOp/Compare/BoolOp/Call/Attribute/Subscript/List/Dict/Tuple/IfExp`
  - 宣言: `FunctionDef/ClassDef`（単一継承のみ）
  - コンテナ: `list/dict/tuple/bytes/bytearray` を PHP 配列 + helper で表現
  - 組み込み: `len/int/float/bool/str/min/max/isinstance/print/range/enumerate`
- 非対応（fail-closed）:
  - `Yield/Await/Try/With/Lambda/Match`、多重継承、generator 式、可変長 keyword 展開
  - 未対応ノード検出時は emitter で `RuntimeError` を投げ、部分生成を許可しない
- 互換方針:
  - EAST2 互換は持たず、`--east-stage 3` のみ
  - 型不明式は `mixed` 相当の helper 経路へ退避し、型既知経路を優先

runtime 分離契約（S1-01 確定）:
- 生成コード冒頭で `require_once __DIR__ . "/pytra/py_runtime.php";` を参照する。
- 生成 `.php` へ helper 本体は埋め込まない（import only）。
- runtime 配置:
  - `src/runtime/php/pytra/py_runtime.php`（共通 helper）
  - `src/runtime/php/pytra/utils/png.php` / `gif.php`（I/O helper）
  - `src/runtime/php/pytra/std/*.php`（`time`, `math`, `pathlib`）
- `tools/gen/regenerate_samples.py` は sample 出力時に `sample/php/pytra/**` を同期コピーする。
- 同一 helper 名は全 backend で意味を揃える（例: `py_truthy`, `py_len`, `py_str`）。

受け入れ基準:
- `src/py2php.py` で EAST3 入力から PHP 生成が通る。
- 生成コードが runtime 分離方式（`require` / `include`）で実行可能。
- `test/fixtures` を対象に `check_py2php_transpile.py` が安定通過する。
- `sample/php` が再生成され、代表ケースで parity が通る（少なくとも `01/03/06/16/18`）。
- docs に PHP backend の使い方と制約が反映される。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2php_smoke.py' -v`
- `python3 tools/check/check_py2php_transpile.py`
- `python3 tools/gen/regenerate_samples.py --langs php --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets php --ignore-unstable-stdout 01_mandelbrot 03_julia_set 06_julia_parameter_sweep 16_glass_sculpture_chaos 18_parser_combinator`

決定ログ:
- 2026-03-02: ユーザー指示により、PHP 対応を `P3` として計画化し、`Ruby -> Lua -> PHP` 順の次段として起票した。
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S1-01] v1 スコープを確定。対応構文・非対応構文・runtime 分離契約を本計画書へ明文化し、非対応は fail-closed（例外停止）で扱う方針を固定した。
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S1-02] `src/py2php.py` と `hooks/php/emitter` を追加し、`load_east3_document(target_lang="php")` 経由で EAST3 読み込み可能な CLI 導線を新設。runtime は `output/pytra/py_runtime.php` コピー方式で接続した。
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S2-01] `php_native_emitter` を拡張し、`FunctionDef/If/While/ForCore(StaticRange, RuntimeIter)` と基本式（定数/二項/比較/呼び出し/コンテナ）を出力可能にした。`core/add`, `control/if_else`, `control/for_range` を `py2php` で変換し、for-range が PHP `for` へ出力されることを確認。
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S2-02] `ClassDef` 出力（`extends`, `__construct`, `parent::method`）と `isinstance`/`dict.get`/`Unbox` 系 lower を追加。`oop/inheritance.py`, `oop/inheritance_virtual_dispatch_multilang.py`, `oop/is_instance.py`, `sample/py/18_mini_language_interpreter.py` の変換で class/コンテナ経路の生成崩れが解消することを確認。
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S2-03] runtime を `src/runtime/php/pytra/{py_runtime.php,runtime/{png,gif}.php,std/time.php}` に分離し、`py2php.py` で `output/pytra/**` へ同期コピーする方式へ拡張。emitter は `__pytra_perf_counter/__pytra_len/__pytra_str_*` を参照し、生成コードへの helper 本体埋め込みを行わない構成へ統一した。
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S3-01] `tools/unittest/test_py2php_smoke.py`（11件）と `tools/check/check_py2php_transpile.py` を追加。`PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2php_smoke.py' -v` および `python3 tools/check/check_py2php_transpile.py` の双方で pass を確認した。
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S3-02] `tools/gen/regenerate_samples.py` と `tools/check/runtime_parity_check.py` に `php` ターゲットを追加し、`transpiler_versions.json` へ `php` version token を登録。`python3 tools/gen/regenerate_samples.py --langs php --force` で `sample/php` 18件を再生成し、`runtime_parity_check --targets php` はこの環境で `php` ツールチェーン未導入のため `toolchain_missing` skip まで確認した。
- 2026-03-02: [ID: P3-PHP-BACKEND-01-S3-03] docs 導線を更新。`docs/{ja,en}/spec/spec-user.md` に `py2php` と `work/transpile/php` / `sample/php` の配置を追記し、`docs/{ja,en}/how-to-use.md` に PHP 実行手順と回帰コマンドを追加、`README.md` / `docs/ja/README.md` のサンプル変換コード一覧へ PHP リンクを反映した。

## 分解

- [x] [ID: P3-PHP-BACKEND-01-S1-01] PHP backend のスコープ（対応構文・非対応構文・runtime 分離契約）を確定する。
- [x] [ID: P3-PHP-BACKEND-01-S1-02] `src/py2php.py` と profile loader を追加し、CLI 導線を確立する。
- [x] [ID: P3-PHP-BACKEND-01-S2-01] PHP native emitter 骨格を実装し、関数・条件分岐・ループ・基本式の出力を通す。
- [x] [ID: P3-PHP-BACKEND-01-S2-02] class/inheritance と container 操作（list/dict/tuple 相当）の最低限 lower を実装する。
- [x] [ID: P3-PHP-BACKEND-01-S2-03] runtime helper を `src/runtime/php/pytra/` へ分離し、生成コードから参照する方式へ統一する。
- [x] [ID: P3-PHP-BACKEND-01-S3-01] `test_py2php_smoke.py` と `check_py2php_transpile.py` を追加し、回帰検知導線を整備する。
- [x] [ID: P3-PHP-BACKEND-01-S3-02] `runtime_parity_check` と `regenerate_samples` に PHP を統合し、`sample/php` を再生成する。
- [x] [ID: P3-PHP-BACKEND-01-S3-03] docs（how-to-use/spec/README 系）の PHP backend 記載を更新し、利用導線を固定する。
