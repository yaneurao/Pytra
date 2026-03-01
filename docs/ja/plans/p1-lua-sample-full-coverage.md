# P1: Lua sample 全18件対応（残り14件解消）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-LUA-SAMPLE-FULL-01`

背景:
- `P0-LUA-BACKEND-01` では Lua backend の初期導線を完了したが、`sample/lua` の再生成対象は `02/03/04/17` の4件に限定されていた。
- `tools/check_py2lua_transpile.py` の `DEFAULT_EXPECTED_FAILS` には `sample/py` の残り14件（`01,05..16,18`）が含まれ、検証時にスキップされている。
- そのため現状は「Lua backend あり」だが「sample 全件運用可能」ではない。

目的:
- Lua backend を `sample/py` 18件全てへ拡張し、`sample/lua` を全ケースで生成・回帰可能な状態にする。

対象:
- `src/hooks/lua/emitter/lua_native_emitter.py` の未対応 lower 実装
- `tools/check_py2lua_transpile.py` の expected-fail 縮退
- `tools/regenerate_samples.py --langs lua` の全件再生成
- `sample/lua/*.lua`（18件）
- `test/unit/test_py2lua_smoke.py` と parity 導線

非対象:
- Lua backend の性能最適化
- 他言語 backend の改修
- Lua runtime の高度機能拡張（必要最小以外）

受け入れ基準:
- `tools/check_py2lua_transpile.py` で `sample/py` 18件がスキップなしで変換成功する。
- `sample/lua` に 18 件すべての生成物が揃う。
- `runtime_parity_check --targets lua --all-samples` が既存条件で非退行（少なくとも output mismatch なし）となる。
- 既知スキップ理由が残る場合は、`DEFAULT_EXPECTED_FAILS` でなく計画書の未解決項目として明示される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2lua_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets lua --all-samples --ignore-unstable-stdout`
- `python3 tools/regenerate_samples.py --langs lua --force`

決定ログ:
- 2026-02-28: ユーザー指示により、Lua 残件14ケースを `P1` で回収する計画を新規起票した。
- 2026-03-01: `sample/py` 残件14ケースを個別実行し、失敗要因を4カテゴリへ分類した（assignment target / Tuple / ListComp / Slice）。
- 2026-03-01: `lua_native_emitter.py` に `Subscript` 代入 target / tuple assign / `Tuple` / `ListComp` / `Slice` / `Raise` を実装し、残件14ケースの transpile 失敗を解消した。
- 2026-03-01: `tools/check_py2lua_transpile.py` の `DEFAULT_EXPECTED_FAILS` から sample 14件（`01,05..16,18`）を削除し、`checked=101 ok=101 fail=0` を確認した。
- 2026-03-01: `tools/regenerate_samples.py --langs lua --force` で `sample/lua` を 18件へ再生成した。
- 2026-03-01: `test_py2lua_smoke.py`（16件）と `runtime_parity_check --targets lua --all-samples` を再実行し、output mismatch なしを確認した（環境上は `toolchain_missing` 分類）。

## 分解

- [x] [ID: P1-LUA-SAMPLE-FULL-01-S1-01] `sample/py` 残件14ケースの失敗要因を分類し、機能ギャップ一覧を固定する。
- [x] [ID: P1-LUA-SAMPLE-FULL-01-S2-01] 優先度順に未対応 lower（例: comprehension / lambda / tuple assign / stdlib 呼び出し差分）を実装する。
- [x] [ID: P1-LUA-SAMPLE-FULL-01-S2-02] `tools/check_py2lua_transpile.py` の `DEFAULT_EXPECTED_FAILS` から sample 対象を段階削除し、スキップ依存を解消する。
- [x] [ID: P1-LUA-SAMPLE-FULL-01-S3-01] `sample/lua` 全18件を再生成し、欠落ファイルゼロを確認する。
- [x] [ID: P1-LUA-SAMPLE-FULL-01-S3-02] Lua smoke/parity を再実行し、非退行を固定する。

## S1-01 失敗要因分類（sample 残14件）

1. `lang=lua unsupported assignment target`（10件）
対象: `05,06,07,08,10,11,12,13,14,15`
2. `lang=lua unsupported expr kind: Tuple`（2件）
対象: `01,16`
3. `lang=lua unsupported expr kind: ListComp`（1件）
対象: `09`
4. `lang=lua unsupported expr kind: Slice`（1件）
対象: `18`
