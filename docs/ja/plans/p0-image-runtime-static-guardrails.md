# P0: 画像runtime 静的ガードレール導入（core混入禁止）

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01`

背景:
- 画像runtimeで同種の再発（`py_runtime.*` への画像本体直書き）が複数回発生している。
- 運用ルールのみでは再発を防止できないため、機械的に fail させる静的検査が必要。

目的:
- `pytra-core` に画像実装本体が混入したら即 fail させる。
- `pytra-gen` が正本由来生成物であること（`source:` / `generated-by:`）を機械検証で固定する。
- ローカル・CIで同一の失敗条件を適用し、再発余地を無くす。

対象:
- `tools/` の静的検査スクリプト
- `tools/run_local_ci.py` と CI 導線
- `src/runtime/<lang>/` の画像runtime配置

非対象:
- 画像runtime本体の実装移行そのもの（別P0で実施）
- README 更新

受け入れ基準:
- `pytra-core` 配下に `write_rgb_png` / `save_gif` / `grayscale_palette`（および言語別プレフィックス）が存在すると検査が fail する。
- `pytra-gen` 配下の画像runtime生成物に `source: src/pytra/utils/{png,gif}.py` と `generated-by:` が無い場合に fail する。
- 検査は `tools/run_local_ci.py` と CI 必須ジョブで実行される。
- 既存runtimeに検査を適用して green が確認できる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/<new_image_runtime_guard_script>.py`
- `python3 -m unittest discover -s test/unit/tooling -p 'test_*image*guard*.py'`

## 分解

- [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01-S1-01] 検査仕様（許可パス/禁止シンボル/必須marker/除外規則）を定義する。
- [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01-S2-01] `tools/` に静的検査スクリプトを実装し、`pytra-core` 混入検知を fail 化する。
- [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01-S2-02] `pytra-gen` の `source:` / `generated-by:` 欠落検知を fail 化する。
- [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01-S3-01] unit test（正常系/違反系）を追加する。
- [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01-S3-02] ローカルCIとCI必須ジョブへ組み込む。
- [ ] [ID: P0-IMAGE-RUNTIME-STATIC-GUARDRAILS-01-S4-01] 全言語runtimeへ検査を適用し green を確認する。

決定ログ:
- 2026-03-04: ユーザー指示（「静的チェックを追加」）に基づき、再発防止専用のP0計画を新規起票。
