# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-25

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモ（件数等）を追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。

## 未完了タスク

### P1-EMIT-CPP: C++ emitter

作業ディレクトリ: `toolchain2/emit/cpp/`
必読: [docs/ja/spec/spec-emitter-guide.md](../spec/spec-emitter-guide.md)

1. [ ] [ID: P1-EMIT-CPP-S1] C++ emitter を `toolchain2/emit/cpp/` に新規実装し、fixture parity が通る
2. [ ] [ID: P1-EMIT-CPP-S2] sample 18 件の parity テストが通る
3. [ ] [ID: P1-EMIT-CPP-S3] `pytra-cli2 -emit --target=cpp` を toolchain2 emitter に切り替える
4. [ ] [ID: P1-EMIT-CPP-S4] `toolchain/` への依存をゼロにし、`toolchain/` を除去する

### P2-SELFHOST: toolchain2 自身の変換テスト

文脈: `docs/ja/plans/plan-pipeline-redesign.md` §3.5

1. [ ] [ID: P2-SELFHOST-S1] `src/toolchain2/` の全 .py が parse 成功
2. [ ] [ID: P2-SELFHOST-S2] parse → resolve → compile → optimize → link まで通す
3. [ ] [ID: P2-SELFHOST-S3] golden を `test/selfhost/` に配置し、回帰テストとして維持
4. [ ] [ID: P2-SELFHOST-S4] Go emitter で toolchain2 を Go に変換し、`go build` が通る

注: 完了済みタスクは [アーカイブ](archive/index.md) に移動済み。
