# TASK GROUP: TG-P0-EAST123-MIGRATION

最終更新: 2026-02-24

関連 TODO:
- `docs-ja/todo.md` の `ID: P0-EASTMIG-01`
- `docs-ja/todo.md` の `ID: P0-EASTMIG-02`
- `docs-ja/todo.md` の `ID: P0-EASTMIG-03`
- `docs-ja/todo.md` の `ID: P0-EASTMIG-04`
- `docs-ja/todo.md` の `ID: P0-EASTMIG-05`

背景:
- 現状は `EAST1/EAST2/EAST3` の責務がファイル上で見えにくく、`transpile_cli.py` に集約されている。
- `EAST2 -> EAST3` は `east3_lowering.py` が担うが、入口 API と backend 側の責務境界が追いにくい。
- hooks を最小化する設計方針に対して、移行ステップと削除順が明文化されていない。

目的:
- `EAST1`/`EAST2`/`EAST3` の責務をモジュール単位で固定し、入口 API を明確化する。
- `py2cpp.py` の主経路を `EAST3` 前提に寄せ、backend 側の意味論再判断を縮退する。
- hooks を最終的に `EAST3` 向け構文差分専任へ収束させる。

対象:
- `src/pytra/compiler/transpile_cli.py`
- `src/pytra/compiler/east_parts/`
- `src/py2cpp.py`
- `src/hooks/cpp/`
- `test/unit/`

非対象:
- 新規最適化器の導入
- 全 backend の同時全面 rewrite
- runtime API の大規模仕様変更

受け入れ基準:
1. `EAST1 -> EAST2` と `EAST2 -> EAST3` の責務が API と実装ファイルで分離される。
2. `py2cpp.py` が `EAST3` を標準入力経路として扱い、`EAST2` 再判断の新規追加を禁止する。
3. `--object-dispatch-mode` は `EAST2 -> EAST3` で一度だけ適用される。
4. hooks の意味論実装は段階的に撤去され、構文差分専任に近づく。
5. 主要回帰コマンドが継続して成功する。

確認コマンド（最低）:
- `python3 -m pytest -q test/unit/test_east3_lowering.py`
- `python3 -m pytest -q test/unit/test_east3_cpp_bridge.py`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`

サブタスク実行順（todo 同期）:
1. `P0-EASTMIG-01`: stage 名と責務境界（`EAST1/2/3`）を `spec` と `plan` で同期する。
2. `P0-EASTMIG-02`: `transpile_cli.py` に集中している段階 API を `east_parts/east1.py`, `east_parts/east2.py`, `east_parts/east3.py` へ分離する。
3. `P0-EASTMIG-03`: `py2cpp.py` を `EAST3` 主経路化し、`EAST2` 再判断ロジックを段階縮退する。
4. `P0-EASTMIG-04`: hooks を `EAST3` 前提で棚卸しし、意味論 hook の流入を禁止する。
5. `P0-EASTMIG-05`: `--east-stage 3` 主経路の回帰導線を標準化し、`EAST2` 互換を移行モードへ格下げする。

実行メモ:
- `EAST3 lower` は `EAST2 -> EAST3` 変換のことを指す。
- `EAST1 -> EAST2` は parser 出力正規化層であり、意味論確定は行わない。
- backend hooks は移行期間中に分離してもよいが、最終形は `EAST3` 向け最小 hook 集合に収束させる。

決定ログ:
- 2026-02-24: 本計画を `materials/refs/` に `plans` 形式で追加。
- 2026-02-24: dispatch 方針は単一オプション `--object-dispatch-mode`（既定 `native`）を維持。
- 2026-02-24: `docs-ja/plans/plan-east123-migration.md` として採用し、`docs-ja/todo.md` へ `P0-EASTMIG-*` タスク群を登録する。
