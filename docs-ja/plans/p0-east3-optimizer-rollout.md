# P0: EAST3 共通最適化層の実装導入

最終更新: 2026-02-26

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P0-EAST3-OPT-01`

背景:
- `EAST3` 共通最適化層の仕様（`docs-ja/spec/spec-east3-optimizer.md`）は定義済みだが、実装導線は未整備である。
- これまでの最適化ロジックは emitter 側へ分散しやすく、責務境界が曖昧になりがちだった。
- `for ... in range(...)` の正規化や未使用ループ変数の束縛削減は、backend 固有変換ではなく共通層で扱う方針を確定済み。

目的:
- `EAST3 -> EAST3` の共通 optimizer を実装し、意味保存・fail-closed・deterministic を運用可能な形で固定する。

対象:
- `src/pytra/compiler/east_parts/east3_optimizer.py`（新規）
- `src/pytra/compiler/east_parts/east3_opt_passes/*.py`（新規）
- `src/pytra/compiler/transpile_cli.py`（CLI オプション配線）
- pass 単体テストと統合回帰（`test/unit` と `tools/*`）

非対象:
- `EAST2` 構築/型解決ロジックの再設計
- C++ など backend 固有の構文化（`for (i=...; ...; ++i)`）
- 文字列化済みコードに対する後処理最適化

受け入れ基準:
- `O0/O1/O2` 切替と pass 単位 on/off が CLI から制御できる。
- `O1` 既定 pass（cast/literal/range-loop 正規化）が動作し、`O2` でループ系 pass を追加適用できる。
- 既存 parity（stdout/artefact）を破らない。
- 不適用ケース（副作用・評価順序不確実ケース）で fail-closed が確認できる。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_east3_*optimizer*.py'`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp,rs,cs,js,ts --all-samples --ignore-unstable-stdout`

決定ログ:
- 2026-02-26: 初版作成。`spec-east3-optimizer` に基づき、実装導入を S1/S2/S3 の3段で進める。

## 分解

- [ ] [ID: P0-EAST3-OPT-01-S1-01] optimizer エントリ (`east3_optimizer.py`) と pass manager 骨格（`PassContext`/`PassResult`）を追加する。
- [ ] [ID: P0-EAST3-OPT-01-S1-02] CLI オプション（`--east3-opt-level`, `--east3-opt-pass`, dump/trace）を実装し、`O0/O1/O2` 契約を固定する。
- [ ] [ID: P0-EAST3-OPT-01-S2-01] `NoOpCastCleanupPass` / `LiteralCastFoldPass` を実装し、`O1` 既定セットを確立する。
- [ ] [ID: P0-EAST3-OPT-01-S2-02] `RangeForCanonicalizationPass` / `UnusedLoopVarElisionPass` を実装し、`for ... in range(...)` の責務境界を反映する。
- [ ] [ID: P0-EAST3-OPT-01-S2-03] `LoopInvariantHoistLitePass` / `StrengthReductionFloatLoopPass` を `O2` 限定で導入する。
- [ ] [ID: P0-EAST3-OPT-01-S3-01] pass 単体テスト（入力/出力EAST3差分、非適用ガード、意味保存）を追加する。
- [ ] [ID: P0-EAST3-OPT-01-S3-02] `sample` 回帰 + parity 検証を実行し、`O0`/`O1`/`O2` 切替時の互換を確認する。
- [ ] [ID: P0-EAST3-OPT-01-S3-03] 実装差分を `spec-east3-optimizer` と同期し、運用手順（トレース確認/切り分け）を文書化する。
