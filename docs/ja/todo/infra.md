<a href="../../en/todo/infra.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — インフラ・ツール・仕様

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-30（P0-SELFHOST-MATRIX-AUTO-REFRESH・P10-STDLIB-TEST-SEPARATION 完了）

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。

完了済みタスクは [アーカイブ](archive/20260330.md) / [P10-REORG アーカイブ](archive/20260330-p10reorg.md) を参照。

## 未完了タスク

### P0-PROGRESS-SUMMARY: バックエンド全体サマリページを自動生成する

1. [ ] [ID: P0-PROGRESS-SUMMARY-S1] `gen_backend_progress.py` に summary 生成を追加する — 各言語1行で fixture/sample/stdlib/selfhost/emitter lint の状況を表示する `backend-progress-summary.md` を日英同時生成。parity check 末尾の自動再生成（`_maybe_regenerate_progress`, `_maybe_regenerate_benchmark`, `_maybe_refresh_selfhost_python`, `_maybe_run_emitter_lint`）は `.parity-results/.gen.lock` で排他制御し、複数 agent の同時書き込みを防ぐこと
2. [ ] [ID: P0-PROGRESS-SUMMARY-S2] `progress/index.md` の「バックエンドサポート状況」セクションに summary へのリンクを追加する（または summary をインライン表示する）
3. [ ] [ID: P0-PROGRESS-SUMMARY-S3] `check_emitter_hardcode_lint.py` の出力に合計行（🟩 PASS / 🟥 FAIL）を追加する — 他のマトリクスと同じ形式
4. [ ] [ID: P0-PROGRESS-SUMMARY-S4] parity check の末尾に `_maybe_run_emitter_lint()` を追加する — `emitter-hardcode-lint.md` の mtime が 1 時間以上古ければ `check_emitter_hardcode_lint.py` を自動実行する

（P20-INT32 は [plans/p4-int32-default.md](../plans/p4-int32-default.md) に保留中。再開時にここへ戻す。）
