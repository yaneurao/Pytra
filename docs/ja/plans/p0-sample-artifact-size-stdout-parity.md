# P0: sample 画像 artifact_size の stdout parity 導入

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-SAMPLE-ARTIFACT-SIZE-01`

背景:
- 現行の `runtime_parity_check` は主に stdout 比較で、画像 artifact（PNG/GIF）の内容一致を直接は検証していない。
- バイナリ完全一致（CRC/sha）導入は将来的に有効だが、現時点では仕様・実装の肥大化を避けたい。
- sample 側へ `Path(...).stat().st_size` を直接追加する案を試行したが、`Path.stat()` 未対応 backend（C++/Ruby など）があり互換性を損なうことを確認した。

目的:
- 画像出力ケースで `runtime_parity_check` が artifact サイズを直接比較し、stdout だけでは検出できない回帰を fail として検知できるようにする。

対象:
- `tools/runtime_parity_check.py` の artifact 比較仕様（`output:` からの実ファイルサイズ比較）
- 関連 smoke/parity テスト

非対象:
- CRC/sha などハッシュ比較の本格導入
- 画像以外 artifact の一般化
- sample 本体へ backend 非互換な `Path.stat()` 依存コードを追加すること

受け入れ基準:
- Python 実行時の `output:` で得た artifact 実ファイルサイズを基準に、各 backend でサイズ不一致を検知できる。
- artifact が未生成・欠落・出力行欠落のケースを `runtime_parity_check` で fail できる。
- `runtime_parity_check --case-root sample --all-samples` が既存 pass 範囲で非退行。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_runtime_parity_check_cli.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --all-samples --ignore-unstable-stdout`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 01_mandelbrot --ignore-unstable-stdout`

決定ログ:
- 2026-02-28: ユーザー指示により、バイナリ比較の代替として `artifact_size` stdout 出力を `P0` で導入する計画を起票した。
- 2026-02-28: `sample/py` へ `Path(out_path).stat().st_size` を追加する案は `Path.stat()` 非対応 backend（C++/Ruby）で実行失敗するため撤回した。
- 2026-02-28: `runtime_parity_check` 側で `output:` から artifact 実ファイルを解決し、サイズ比較（presence/missing/size mismatch）を行う方針へ pivot した。
- 2026-02-28: `test_runtime_parity_check_cli.py` に `artifact_size_mismatch` 回帰を追加し、`sample` parity 実行（ruby 18件、cpp 01）で非退行を確認した。

## 分解

- [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S1-01] 画像出力 sample ケースを棚卸しし、artifact 比較対象（`output:` 行を持つケース）を固定する。
- [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S2-01] `runtime_parity_check` に Python baseline artifact の解決・実サイズ取得ロジックを追加する。
- [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S2-02] target 実行時の artifact presence/size 比較（stale file ガード含む）を追加する。
- [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S3-01] `runtime_parity_check` の回帰テストを更新し、`artifact_size_mismatch` を固定する。
- [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S3-02] sample parity を再実行し、サイズ不一致検知機構を有効化した状態で非退行を確認する。
