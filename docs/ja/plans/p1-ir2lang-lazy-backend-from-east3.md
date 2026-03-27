<a href="../../en/plans/p1-ir2lang-lazy-backend-from-east3.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: `ir2lang.py` 導入（EAST3 JSON 直入力 + target lazy import）

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-IR2LANG-LAZY-EMIT-01`

背景:
- `test/` / `sample/` の backend 回帰で、毎回 `py -> EAST3` を通すと時間コストが高い。
- backend 単体の回帰を回したいが、現在は frontend 経路（`pytra-cli.py`）への依存が残り、責務分離が弱い。
- ユーザー要件として、`test/ir` / `sample/ir` の EAST3 から target 言語へ直接変換するスクリプトが必要。
- selfhost 用導線は今回不要であり、対象外とする。

目的:
- `ir2lang.py` を追加し、`EAST3(JSON) -> target code` を frontend 非依存で実行可能にする。
- backend は `--target` 指定に応じて lazy import し、必要な backend だけ読み込む。
- backend 回帰の高速実行導線（IR固定）を整備する。

対象:
- 追加: `src/ir2lang.py`
- 追加: `EAST3(JSON)` 入力バリデーション（stage2/未知形式の fail-fast）
- 追加: `--target` 単位 lazy import dispatch（backend registry 再利用）
- 追加: 層別 option pass-through（`--lower-option`, `--optimizer-option`, `--emitter-option`）
- 追加: `test/ir` / `sample/ir` 用の最小運用手順（docs）

非対象:
- selfhost 用 `ir2lang` 実装（static import 版）
- frontend (`py -> EAST3`) 実装の変更
- backend 機能追加・最適化仕様変更

受け入れ基準:
- `ir2lang.py --input <east3.json> --target <lang>` で target 変換が動作する。
- 非指定 target backend は import されない（lazy import）。
- `EAST2` / 不正 IR 入力は fail-fast で明確にエラーになる。
- `test/ir` / `sample/ir` から少なくとも主要 target（`cpp/rs/js`）で変換スモークが通る。
- 使い方が `docs/ja/how-to-use.md`（必要なら `docs/en/how-to-use.md`）に追記される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 src/ir2lang.py --help`
- `python3 src/ir2lang.py --input sample/ir/01_mandelbrot.json --target cpp --output out/ir2lang_cpp_01.cpp`
- `python3 src/ir2lang.py --input sample/ir/01_mandelbrot.json --target rs --output out/ir2lang_rs_01.rs`
- `python3 src/ir2lang.py --input sample/ir/01_mandelbrot.json --target js --output out/ir2lang_js_01.js`

## 分解

- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S1-01] `test/ir` / `sample/ir` の入力形式（JSON schema / stage marker / 必須メタ）を棚卸しし、`ir2lang` の受理契約を確定する。
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S1-02] `ir2lang.py` CLI 仕様（必須引数、出力先、層別 option、fail-fast 条件）を定義する。
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-01] `src/ir2lang.py` を実装し、EAST3 JSON 読み込みと target dispatch を導入する。
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-02] backend registry 経由の target lazy import を実装し、非指定 backend の import を回避する。
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-03] `--lower/--optimizer/--emitter-option` の層別 pass-through を実装する。
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-04] EAST2/不正IR入力の fail-fast エラー整備とメッセージ標準化を行う。
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S3-01] 主要 target で `sample/ir` / `test/ir` 変換スモークを追加し、backend 単体回帰導線を固定する。
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S3-02] `docs/ja/how-to-use.md`（必要なら `docs/en/how-to-use.md`）へ `ir2lang.py` 手順を追記する。

## S1-01: 入力受理契約（確定）

- `ir2lang.py` の入力は JSON のみを受理し、`.py` は受理しない（frontend 依存を遮断）。
- JSON ルートは次のどちらか:
  - `{"ok": true, "east": {...Module...}}`
  - `{"kind": "Module", ...}`
- 受理する `Module` ルート必須キー:
  - `kind == "Module"`
  - `east_stage == 3`（`1/2` は fail-fast）
  - `body` が `list`
- `schema_version` は存在時に `int >= 1` を要求する（不正型/不正値は fail-fast）。
- `meta` は未指定許容（内部で `{}` 扱い）。指定時は `dict` を要求する。

## S1-02: CLI 仕様（確定）

- エントリ: `python3 src/ir2lang.py`
- 必須:
  - 位置引数 `input`（EAST3 JSON）
  - `--target <lang>`
- 任意:
  - `-o/--output`（未指定時は `input` stem + target 拡張子）
  - `--lower-option key=value`（複数可）
  - `--optimizer-option key=value`（複数可）
  - `--emitter-option key=value`（複数可）
  - `--no-runtime-hook`（runtime 配置を抑止）
- fail-fast 条件:
  - `--target` 未指定
  - `key=value` 形式違反
  - 未知 layer option / 型不一致（`backend_registry.resolve_layer_options`）
  - 入力 JSON 不正 / `EAST2` / `Module` 契約違反
- 終了コード:
  - 正常終了 `0`
  - ユーザー入力エラー `2`

決定ログ:
- 2026-03-03: ユーザー指示により、selfhost 非対応を前提として `ir2lang.py`（EAST3 JSON 直入力 + lazy target import）を P1 で起票。
- 2026-03-03: `ir2lang.py` の入力は `EAST3 JSON` 専用とし、`east_stage==3` を必須化する方針を確定。
- 2026-03-03: CLI は `pytra-cli.py` と同様の layer option 文法を採用し、`--no-runtime-hook` で backend 単体検証を可能にする方針を確定。
- 2026-03-03: `src/ir2lang.py` を追加し、`backend_registry` の lazy dispatch・層別 option pass-through・`EAST3` 契約 fail-fast を実装。
- 2026-03-03: `sample/ir/01_mandelbrot.east3.json` と `test/ir/core_add.east3.json` を fixture 化し、`tools/check_ir2lang_smoke.py`（`cpp/rs/js`）で backend-only 回帰導線を固定。
- 2026-03-03: `docs/ja/how-to-use.md` / `docs/en/how-to-use.md` に `ir2lang.py` 手順（fixture作成・直接変換・smoke実行）を追記。
