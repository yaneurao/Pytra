<a href="../../en/plans/p0-pytra-src-3layer-bootstrap.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

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

- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S1-01] `src/pytra/compiler` 配下を棚卸しし、`frontends` / `ir` / 互換層に分類する。
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S1-02] `src/pytra` 名前空間維持前提のディレクトリ規約と import 境界（依存方向）を定義する。
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S2-01] `src/pytra/frontends` / `src/pytra/ir` を新設し、最小 bootstrap モジュールを配置する。
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S2-02] Python入力〜EAST1 生成の frontends 相当モジュールを `src/pytra/frontends` へ移設する。
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S2-03] EAST1/2/3・lower/optimizer/analysis の IR 相当モジュールを `src/pytra/ir` へ移設する。
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S2-04] `src/pytra/compiler` を互換 shim 化し、既存 import を壊さない re-export 導線を整備する。
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S3-01] 境界ガード（禁止 import / 逆流依存）を追加し、再発防止を固定する。
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S3-02] 主要 unit/transpile 回帰を実行して非退行を確認する。
- [x] [ID: P0-PYTRA-SRC-3LAYER-01-S3-03] `docs/ja/spec`（必要なら `docs/en/spec`）へ新責務境界と移行方針を反映する。

## S1 棚卸し結果（2026-03-03）

frontends 候補（`src/pytra/frontends` へ段階移設）:
- `src/pytra/compiler/transpile_cli.py`
- `src/pytra/compiler/stdlib/frontend_semantics.py`
- `src/pytra/compiler/stdlib/signature_registry.py`
- `src/pytra/compiler/east_parts/east1_build.py`（EAST1 構築と import graph 解決）

IR 候補（`src/pytra/ir` へ段階移設）:
- `src/pytra/compiler/east.py`
- `src/pytra/compiler/east_parts/east1.py`
- `src/pytra/compiler/east_parts/east2.py`
- `src/pytra/compiler/east_parts/east3.py`
- `src/pytra/compiler/east_parts/east2_to_east3_lowering.py`
- `src/pytra/compiler/east_parts/east3_optimizer.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/*`
- `src/pytra/compiler/east_parts/east_io.py`
- `src/pytra/compiler/east_parts/east2_to_human_repr.py`
- `src/pytra/compiler/east_parts/east3_to_human_repr.py`
- `src/pytra/compiler/east_parts/core.py`
- `src/pytra/compiler/east_parts/code_emitter.py`

互換層 / 導線維持（`src/pytra/compiler` 残置）:
- `src/pytra/compiler/__init__.py`
- `src/pytra/compiler/py2x_wrapper.py`
- `src/pytra/compiler/backend_registry.py`
- `src/pytra/compiler/backend_registry_static.py`
- `src/pytra/compiler/js_runtime_shims.py`
- `src/pytra/compiler/transpiler_versions.json`
- `src/pytra/compiler/east_parts/__init__.py`
- `src/pytra/compiler/east_parts/cli.py`（移行期間は `pytra.ir` 参照の薄い CLI ファサード化）

S1-02 で固定した境界ルール:
- 依存方向は `frontends -> ir -> backends` を原則とし、逆方向 import を禁止する。
- `frontends` は入力解釈と EAST1 構築までを担当し、target 言語固有分岐を持たない。
- `ir` は EAST1/2/3、lower/optimizer/analysis、IR 入出力のみを担当し、CLI 引数解析や runtime コピー処理を持たない。
- `compiler` は互換 shim と統合導線の薄い橋渡しに限定し、新規ロジック実装先として扱わない。
- `backends` から `frontends` への import は禁止し、必要な共有処理は `toolchain/emit/common` または `pytra/ir` に寄せる。

決定ログ:
- 2026-03-03: `src/pytra` 名前空間を維持したまま `frontends` / `ir` を導入し、`src/frontends` 直下への最終移設は後続フェーズとする方針を採用。
- 2026-03-03: `git ls-files src/pytra/compiler` で追跡対象を棚卸しし、`transpile_cli/stdlib/east1_build` を frontends 候補、EAST本体・lower・optimizer・human/io を ir 候補、registry/wrapper/version/shim を互換層として分類した。
- 2026-03-03: 移行中の責務衝突を避けるため、`compiler/east_parts/cli.py` は当面互換層に残して `pytra.ir` 参照のみを許可する方針を採用した。
- 2026-03-03: `src/pytra/frontends/__init__.py`, `src/pytra/frontends/python_frontend.py`, `src/pytra/ir/__init__.py`, `src/pytra/ir/pipeline.py` を追加し、既存 `pytra.compiler.*` 実装へ委譲する最小 bootstrap 導線を導入した。
- 2026-03-03: `test/unit/test_pytra_layer_bootstrap.py` を追加し、`pytra.frontends` と `pytra.ir` の公開 API（import 可能性）を固定した。`test_py2x_cli.py` と主要 transpile check（rs/js）および version gate で非退行を確認した。
- 2026-03-03: `src/pytra/frontends/{east1_build.py,frontend_semantics.py,signature_registry.py}` へ実体を移設し、旧 `src/pytra/compiler/east_parts/east1_build.py` と `src/pytra/compiler/stdlib/{frontend_semantics.py,signature_registry.py}` は互換 shim 化した。
- 2026-03-03: `src/pytra/compiler/east_parts/core.py` の stdlib 参照を `pytra.frontends.*` へ切替し、`py2cpp`/`multifile_writer`/`transpile_cli` の `East1BuildHelpers` 参照を新経路へ更新した。
- 2026-03-03: `pytra.frontends.__init__` は package import 時循環を避けるため lazy 委譲実装へ変更した。`test_stdlib_signature_registry.py`, `test_east1_build.py`, `test_pytra_layer_bootstrap.py`, `check_py2{cpp,rs,js}_transpile.py`, `check_noncpp_east3_contract.py --skip-transpile`, `check_transpiler_version_gate.py --base-ref HEAD` の通過を確認した。
- 2026-03-03: IR 本体として `src/pytra/ir/{core,east1,east2,east3,east2_to_east3_lowering,east3_optimizer,east_io}.py` と `src/pytra/ir/east3_opt_passes/*` を新設し、旧 `src/pytra/compiler/east_parts/*` 側は互換 shim 化した。
- 2026-03-03: `transpile_cli` と `frontends/east1_build` の EAST stage 参照を `pytra.ir.*` へ切替。`ir/east_io` が `compiler.east` 経由で循環する問題は `ir.core` 直接参照へ変更して解消した。
- 2026-03-03: IR移設後の回帰として `test_east{2_to_east3_lowering,3_optimizer,3_non_escape_interprocedural_pass,3_lifetime_analysis_pass}`、`check_py2{cpp,rs,js}_transpile.py`、`check_noncpp_east3_contract --skip-transpile`、`check_transpiler_version_gate --base-ref HEAD` を実行し通過を確認した。
- 2026-03-03: `src/pytra/frontends/transpile_cli.py` へ `transpile_cli` 実体を移設し、旧 `src/pytra/compiler/transpile_cli.py` は互換 shim 化した。`python_frontend` は新経路（`pytra.frontends.transpile_cli`）参照へ切替した。
- 2026-03-03: 互換導線検証として `test_py2x_cli.py`, `test_pytra_layer_bootstrap.py`, `test_stdlib_signature_registry.py`, `check_py2{cpp,rs,js}_transpile.py`, `check_noncpp_east3_contract --skip-transpile`, `check_transpiler_version_gate --base-ref HEAD` を再実行し通過を確認した。
- 2026-03-03: 境界ガードとして `tools/check_pytra_layer_boundaries.py` を追加し、`frontends -> backends` / `ir -> backends` / `backends -> frontends` を禁止、`ir -> frontends` は `ir/core.py` のみ許可する静的 import 監視を導入した。
- 2026-03-03: ガード追加時に `toolchain/emit/cpp/emitter/multifile_writer.py` が `pytra.frontends.east1_build` を直参照していたため、互換 shim 経由（`pytra.compiler.east_parts.east1_build`）へ戻して逆流依存を解消した。
- 2026-03-03: 境界ガード導入後の回帰として `check_pytra_layer_boundaries.py`, `test_py2x_cli.py`, `check_py2{cpp,rs,js}_transpile.py`, `check_noncpp_east3_contract --skip-transpile`, `check_transpiler_version_gate --base-ref HEAD` を通過確認した。
- 2026-03-03: S3-02 の主要回帰として `check_pytra_layer_boundaries`, `check_noncpp_east3_contract --skip-transpile`, `test_py2x_cli`, `check_py2{cpp,rs,js,ts,go,java,kotlin,swift,rb,lua,php,scala,nim}_transpile`, `check_transpiler_version_gate --base-ref HEAD` を一括実行し全通過を確認した。
- 2026-03-03: `docs/ja/spec` の責務境界記述を更新し、`spec-folder.md`（3層+互換）、`spec-east.md`（担当ファイル表・移行後正本）、`spec-stdlib-signature-source-of-truth.md`（参照層/利用側パス）、`spec-options.md`（共通CLIの正本パス）へ反映した。
