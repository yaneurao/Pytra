# P1: `ir2lang.py` 導入（EAST3 JSON 直入力 + target lazy import）

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-IR2LANG-LAZY-EMIT-01`

背景:
- `test/` / `sample/` の backend 回帰で、毎回 `py -> EAST3` を通すと時間コストが高い。
- backend 単体の回帰を回したいが、現在は frontend 経路（`py2x.py`）への依存が残り、責務分離が弱い。
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

- [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S1-01] `test/ir` / `sample/ir` の入力形式（JSON schema / stage marker / 必須メタ）を棚卸しし、`ir2lang` の受理契約を確定する。
- [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S1-02] `ir2lang.py` CLI 仕様（必須引数、出力先、層別 option、fail-fast 条件）を定義する。
- [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-01] `src/ir2lang.py` を実装し、EAST3 JSON 読み込みと target dispatch を導入する。
- [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-02] backend registry 経由の target lazy import を実装し、非指定 backend の import を回避する。
- [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-03] `--lower/--optimizer/--emitter-option` の層別 pass-through を実装する。
- [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-04] EAST2/不正IR入力の fail-fast エラー整備とメッセージ標準化を行う。
- [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S3-01] 主要 target で `sample/ir` / `test/ir` 変換スモークを追加し、backend 単体回帰導線を固定する。
- [ ] [ID: P1-IR2LANG-LAZY-EMIT-01-S3-02] `docs/ja/how-to-use.md`（必要なら `docs/en/how-to-use.md`）へ `ir2lang.py` 手順を追記する。

決定ログ:
- 2026-03-03: ユーザー指示により、selfhost 非対応を前提として `ir2lang.py`（EAST3 JSON 直入力 + lazy target import）を P1 で起票。
