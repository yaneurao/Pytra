# P0: sample 画像 artifact_size の stdout parity 導入

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-SAMPLE-ARTIFACT-SIZE-01`

背景:
- 現行の `runtime_parity_check` は主に stdout 比較で、画像 artifact（PNG/GIF）の内容一致を直接は検証していない。
- バイナリ完全一致（CRC/sha）導入は将来的に有効だが、現時点では仕様・実装の肥大化を避けたい。
- sample 側で出力後のファイルサイズを標準出力へ明示すれば、既存 parity 導線に最小変更で artifact 回帰を追加できる。

目的:
- 画像出力 sample（PNG/GIF）で `artifact_size` を stdout に出し、`runtime_parity_check` でサイズ一致を検証可能にする。

対象:
- `sample/py/*.py` の画像出力ケース（PNG/GIF）
- 生成コード（`sample/{cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua}`）再生成
- `tools/runtime_parity_check.py` の比較仕様（`artifact_size:` 行の扱い）
- 関連 smoke/parity テスト

非対象:
- CRC/sha などハッシュ比較の本格導入
- 画像以外 artifact の一般化
- ベンチマーク値の再計測（必要時のみ別タスク）

受け入れ基準:
- 画像出力 sample 実行時に `artifact_size: <bytes>` 行が出力される。
- Python と各 backend の `artifact_size` が parity で比較され、サイズ不一致を検知できる。
- `runtime_parity_check --case-root sample --all-samples` が既存 pass 範囲で非退行。
- `sample` 再生成後、画像系ケースで `artifact_size` 出力が欠落しない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/regenerate_samples.py --force`
- `python3 tools/runtime_parity_check.py --case-root sample --all-samples --ignore-unstable-stdout`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_runtime_parity_check*.py' -v`

決定ログ:
- 2026-02-28: ユーザー指示により、バイナリ比較の代替として `artifact_size` stdout 出力を `P0` で導入する計画を起票した。

## 分解

- [ ] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S1-01] 画像出力 sample ケースを棚卸しし、`artifact_size` 出力追加対象を固定する。
- [ ] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S2-01] `sample/py` の対象ケースへ `artifact_size` 出力（`Path(out_path).stat().st_size`）を追加する。
- [ ] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S2-02] 各 backend 生成コードで同等 `artifact_size` 行が出ることを再生成で確認する。
- [ ] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S3-01] `runtime_parity_check` の回帰テストを更新し、`artifact_size` 行の一致検証を固定する。
- [ ] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S3-02] sample 全体 parity を再実行し、サイズ不一致があれば fail として検知できる状態を確認する。
