# P1: sample/18 PHP コード生成改善（実行可能化 + 品質向上）

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-PHP-S18-CODEGEN-QUALITY-01`

背景:
- `sample/php/18_mini_language_interpreter.php` は現状、生成コードの意味崩れにより実行不能。
- 具体例として、`dict` リテラルが空配列へ崩れる、`x in env` が配列同値比較に崩れる、`Token/ExprNode/StmtNode` のコンストラクタ契約が欠落する、entrypoint 名衝突が発生する。
- この状態では `sample/18` の PHP 実行時間計測・parity 比較・品質評価が継続できない。

目的:
- `sample/18` の PHP 生成コードを実行可能にし、意味互換を担保した上でコード品質（可読性・保守性）を引き上げる。
- 改善を「sample/18 で再現できる最小スコープ」に限定し、fail-closed で段階適用する。

対象:
- `src/toolchain/emit/php/emitter/php_native_emitter.py`
- `src/runtime/php/pytra/py_runtime.php`（必要最小限の補助のみ）
- `test/unit/test_py2php_smoke.py`（必要に応じて PHP codegen 回帰を追加）
- `sample/php/18_mini_language_interpreter.php`（再生成による確認）

非対象:
- PHP backend 全体の全面最適化
- `sample/18` 以外ケースの大規模挙動変更
- 画像 runtime 実装（PNG/GIF writer の本実装）

受け入れ基準:
- `sample/php/18_mini_language_interpreter.php` が実行エラーなく完走し、`elapsed_sec` を出力する。
- `runtime_parity_check --case-root sample --targets php --ignore-unstable-stdout 18_mini_language_interpreter` が pass する。
- 以下の生成品質条件を満たす:
  - `single_char_token_tags` が空配列ではなく、期待キー付き辞書として生成される。
  - `name in env` / `name not in env` が PHP 配列向けの正しい membership 判定へ lower される。
  - `Token/ExprNode/StmtNode` のコンストラクタ呼び出しとクラス定義が整合する。
  - `main`/`__pytra_main` 名衝突時に entrypoint が衝突回避される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2php_smoke.py' -v`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/regenerate_samples.py --langs php --stems 18_mini_language_interpreter --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets php --ignore-unstable-stdout 18_mini_language_interpreter`

決定ログ:
- 2026-03-02: ユーザー指示により、`sample/18` PHP のコード生成改善を P1 計画として起票。
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S1-01] 旧 `sample/php/18` の失敗断片（dict 空配列化 / membership 崩れ / dataclass ctor 不整合）を再現して改善境界を固定。
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-01] `Dict` の `entries` 形式を出力可能にし、連想配列 literal を正しく生成。
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-02] `Compare(In/NotIn)` を型別 membership lower へ修正し、`dict` では `array_key_exists` を使用。
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-03] dataclass class の field 宣言 + 自動 `__construct` 生成を追加して ctor 契約を整合。
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-04] entrypoint 名決定時に function/class 衝突回避を一般化。
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S3-01] `tools/check_py2php_transpile.py` に `sample/18` 品質断片チェックを追加。
- 2026-03-03: [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S3-02] `sample/php/18` 再生成後に `runtime_parity_check`（php, case18）を pass。

## 分解

- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S1-01] `sample/18` の失敗断片（dict literal / membership / ctor / entrypoint）を棚卸しし、改善境界を固定する。
- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-01] PHP emitter の dict literal 出力を修正し、キー付き連想配列を正しく生成する。
- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-02] `in` / `not in` の lower を型別に修正し、dict membership を `array_key_exists` 系へ統一する。
- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-03] dataclass 由来クラス（`Token/ExprNode/StmtNode`）のフィールド/コンストラクタ出力を整合させる。
- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S2-04] `main_guard` 出力の entrypoint 名衝突回避を一般化し、`sample/18` で衝突しないことを保証する。
- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S3-01] unit/smoke 回帰を追加し、同種崩れ（dict/in/ctor/entrypoint）の再発検知を固定する。
- [x] [ID: P1-PHP-S18-CODEGEN-QUALITY-01-S3-02] `sample/php/18` 再生成と parity 実行で非退行を確認する。
