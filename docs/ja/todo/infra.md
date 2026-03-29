<a href="../../en/todo/infra.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — インフラ・ツール・仕様

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-30（P2-BENCH S1〜S5 完了）

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。

完了済みタスクは [アーカイブ](archive/20260330.md) / [P10-REORG アーカイブ](archive/20260330-p10reorg.md) を参照。

## 未完了タスク

### P3-SAMPLE-AUTO-COPY: sample parity PASS 時に sample/<lang>/ へ自動コピー

文脈: [docs/ja/plans/p3-sample-auto-copy.md](../plans/p3-sample-auto-copy.md)

1. [ ] [ID: P3-SAMPLE-COPY-S1] parity check（fast 版）で sample の parity PASS 時に、emit されたソースコードを `sample/<lang>/` にコピーするロジックを追加する — PASS したケースのみコピーし、FAIL のケースは既存ファイルを維持する
2. [ ] [ID: P3-SAMPLE-COPY-S2] コピー先のファイル名が既存の `sample/<lang>/` の命名規則（`01_mandelbrot.cpp` 等）と一致することを確認する
3. [ ] [ID: P3-SAMPLE-COPY-S3] `regenerate_samples.py` との責務整理 — parity check が自動コピーするなら `regenerate_samples.py` は不要になる可能性がある。廃止するか、手動再生成用として残すか判断する

### P20-INT32: int のデフォルトサイズを int64 → int32 に変更

文脈: [docs/ja/plans/p4-int32-default.md](../plans/p4-int32-default.md)

前提: Go selfhost 完了後に着手。影響範囲が大きいため P4 → P20 に降格。

1. [ ] [ID: P20-INT32-S1] spec-east.md / spec-east2.md の `int` → `int32` 正規化ルール変更
2. [ ] [ID: P20-INT32-S2] resolve の型正規化を修正
3. [ ] [ID: P20-INT32-S3] sample 18 件のオーバーフロー確認 + 必要な箇所を `int64` に明示
4. [ ] [ID: P20-INT32-S4] golden 再生成 + 全 emitter parity 確認
