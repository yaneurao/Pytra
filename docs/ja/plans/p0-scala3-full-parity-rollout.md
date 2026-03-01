# P0: Scala3 parity 全通過化（sample + fixture）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-SCALA3-PARITY-ALL-01`

背景:
- Scala3 backend は `runtime_parity_check` の target に登録済みだが、現状は `ARTIFACT_OPTIONAL_TARGETS` に `scala` が含まれ、画像生成系の artifact parity が実質免除されている。
- `scala_native_emitter.py` には `save_gif` / `write_rgb_png` を `__pytra_noop` へ落とす分岐と、`// TODO: unsupported ...` の出力経路が残っており、sample/fixture 全件 parity の阻害要因になっている。
- 「Scala3 でも parity チェックをすべて通す」ためには、正規経路で transpile/compile/run/stdout/artifact を検証できる状態まで引き上げる必要がある。

目的:
- Scala3 backend を parity 検証の対象として完全化し、`sample/py` 全件と指定 fixture 群で `runtime_parity_check` を pass させる。
- artifact parity（PNG/GIF のサイズ一致）も Scala3 で有効化し、他 backend と同じ検証契約へ揃える。

対象:
- Scala emitter の TODO/no-op 経路削減（`ForCore` / statement / image writer 呼び出し）
- Scala runtime helper（画像出力・型変換・container 操作）の不足補完
- `tools/runtime_parity_check.py` の Scala artifact optional 扱い撤廃
- Scala parity 用の回帰導線（コマンド/スクリプト/テスト）整備
- ドキュメント（how-to-use / spec-tools）への運用反映

非対象:
- Scala 負例 fixture の expected-fail 契約改修（`P2-SCALA-NEGATIVE-ASSERT-01` で扱う）
- Scala backend の性能最適化（速度改善）
- Scala 以外の backend 品質改善

受け入れ基準:
- `python3 tools/runtime_parity_check.py --case-root sample --targets scala --all-samples` が `pass=18 fail=0` になること。
- Scala parity 実行で artifact 比較が有効になり、PNG/GIF 出力ケースで `artifact_presence_mismatch` / `artifact_missing` / `artifact_size_mismatch` が 0 件になること。
- Scala fixture parity（正例マニフェスト）で `run_failed` / `output_mismatch` が 0 件になること。
- `test/unit/test_runtime_parity_check_cli.py` の Scala 前提テストが新契約（artifact optional ではない）で通ること。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets scala --all-samples --summary-json out/scala_parity_sample_summary.json`
- `python3 tools/runtime_parity_check.py --case-root fixture --targets scala <fixture-case-list> --summary-json out/scala_parity_fixture_summary.json`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2scala_smoke.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_runtime_parity_check_cli.py' -v`

決定ログ:
- 2026-03-01: Scala3 parity を「stdout のみ暫定一致」から「artifact 含む完全一致」へ引き上げる方針で P0 起票。

## 分解

- [ ] [ID: P0-SCALA3-PARITY-ALL-01-S1-01] Scala parity の現状失敗を baseline 取得（sample 全件 + fixture 正例群）し、失敗カテゴリを固定する。
- [ ] [ID: P0-SCALA3-PARITY-ALL-01-S1-02] Scala fixture parity の対象マニフェスト（正例のみ）を定義し、負例タスク（P2）と境界を明文化する。
- [ ] [ID: P0-SCALA3-PARITY-ALL-01-S2-01] `save_gif` / `write_rgb_png` の `__pytra_noop` 経路を撤去し、Scala runtime 実装へ接続する。
- [ ] [ID: P0-SCALA3-PARITY-ALL-01-S2-02] `// TODO: unsupported ...` 出力経路を縮小し、必要ノードの lowering を実装（未対応は fail-closed）する。
- [ ] [ID: P0-SCALA3-PARITY-ALL-01-S2-03] sample/18 を含む高難度ケースで不足する builtin/container 操作を補完し、run_failed を解消する。
- [ ] [ID: P0-SCALA3-PARITY-ALL-01-S2-04] 継承先で上書きされるメソッドに `override def` を出力し、継承メソッド契約を Scala3 コンパイラ規約へ一致させる。
- [ ] [ID: P0-SCALA3-PARITY-ALL-01-S3-01] `runtime_parity_check` の Scala artifact optional を撤去し、関連 unit テストを新契約へ更新する。
- [ ] [ID: P0-SCALA3-PARITY-ALL-01-S3-02] Scala parity 専用チェック導線（スクリプトまたは既存コマンド束）を追加し、再実行手順を固定する。
- [ ] [ID: P0-SCALA3-PARITY-ALL-01-S3-03] sample/fixture parity 実行結果を確認し、`docs/ja/how-to-use.md` / `docs/en/how-to-use.md` / `docs/ja/spec/spec-tools.md` を同期する。
