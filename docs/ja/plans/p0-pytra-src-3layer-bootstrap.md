# P0: `src/pytra` 内 3層分離ブートストラップ（`frontends` / `ir` / `backend`）

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PYTRA-SRC-3LAYER-01`

背景:
- 現状 `src/pytra/compiler` に Python 入力処理（frontends 相当）と EAST 系処理（IR 相当）が混在しており、責務境界が見えにくい。
- 既存 import は `pytra.*` 名前空間に依存しているため、いきなり `src/frontends` 直下へ切り出すと破壊的変更になりやすい。
- 要件は「まず `src/pytra` 名前空間を維持したまま `frontends` / `ir` を分け、段階移行を安全に進める」ことである。

目的:
- `src/pytra/frontends` と `src/pytra/ir` を新設し、`src/pytra/compiler` の責務を段階的に移設する。
- `src/backends` は現行維持とし、依存方向を `frontends -> ir -> backends` に固定する。
- `pytra/std` / `pytra/built_in` / `runtime` は実行時サポート層として分離し、今回の3層再配置対象外とする。

対象:
- `src/pytra/compiler`（frontends 相当・IR 相当の整理）
- `src/pytra/frontends`（新設）
- `src/pytra/ir`（新設）
- import 経路の互換 shim（段階移行期間）
- 境界ガード（禁止 import 検査）
- docs (`docs/ja/spec` の責務境界説明)

非対象:
- backend 出力品質改善
- runtime 実装の機能追加
- `src/pytra/std` / `src/pytra/built_in` / `src/runtime` の大規模移動
- `src/frontends` 直下への最終移設（今回は行わない）

受け入れ基準:
- `src/pytra/frontends` / `src/pytra/ir` が導入され、対象モジュールが責務に沿って移設されている。
- `src/pytra/compiler` は互換層（re-export / thin bridge）中心に縮退し、新規実装の流入を禁止できる状態である。
- `py2x` および既存 `py2*.py` が非退行で動作する。
- 境界ガードが追加され、`frontends` と `ir` の逆流 import を検知できる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_noncpp_east3_contract.py --skip-transpile`
- `python3 -m unittest discover -s test/unit -p test_py2x_cli.py`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2nim_transpile.py`

## 分解

- [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S1-01] `src/pytra/compiler` 配下を棚卸しし、`frontends` / `ir` / 互換層に分類する。
- [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S1-02] `src/pytra` 名前空間維持前提のディレクトリ規約と import 境界（依存方向）を定義する。
- [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S2-01] `src/pytra/frontends` / `src/pytra/ir` を新設し、最小 bootstrap モジュールを配置する。
- [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S2-02] Python入力〜EAST1 生成の frontends 相当モジュールを `src/pytra/frontends` へ移設する。
- [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S2-03] EAST1/2/3・lower/optimizer/analysis の IR 相当モジュールを `src/pytra/ir` へ移設する。
- [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S2-04] `src/pytra/compiler` を互換 shim 化し、既存 import を壊さない re-export 導線を整備する。
- [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S3-01] 境界ガード（禁止 import / 逆流依存）を追加し、再発防止を固定する。
- [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S3-02] 主要 unit/transpile 回帰を実行して非退行を確認する。
- [ ] [ID: P0-PYTRA-SRC-3LAYER-01-S3-03] `docs/ja/spec`（必要なら `docs/en/spec`）へ新責務境界と移行方針を反映する。

決定ログ:
- 2026-03-03: `src/pytra` 名前空間を維持したまま `frontends` / `ir` を導入し、`src/frontends` 直下への最終移設は後続フェーズとする方針を採用。
