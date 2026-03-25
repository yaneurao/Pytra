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
- **emitter の parity テストは「emit 成功」ではなく「emit + compile + run + stdout 一致」を完了条件とする。** emit だけ成功してもプレースホルダーコードが混入している可能性がある。

## 未完了タスク

### P1-EMIT-GO-PARITY: Go emitter の compile + run parity 修正

Go emitter が fixture/sample の全件で `go run` + stdout 一致を達成すること。
現状 emit は成功するが list/dict comprehension 等がプレースホルダーになっており `go run` が通らない。

1. [ ] [ID: P1-GO-PARITY-S1] list/dict comprehension の Go 変換を実装
2. [ ] [ID: P1-GO-PARITY-S2] fixture 132 件で `go run` + stdout 一致
3. [ ] [ID: P1-GO-PARITY-S3] sample 18 件で `go run` + stdout 一致

### P1-EMIT-CPP: C++ emitter

作業ディレクトリ: `toolchain2/emit/cpp/`
必読: [docs/ja/spec/spec-emitter-guide.md](../spec/spec-emitter-guide.md)

1. [x] [ID: P1-EMIT-CPP-S1] C++ emitter を `toolchain2/emit/cpp/` に新規実装し、emit 成功 — fixture 132/132, sample 18/18 emit 成功
2. [ ] [ID: P1-EMIT-CPP-S2] 既存 `src/runtime/cpp/` を新パイプラインの emitter 出力に合わせて修正する。新規作成ではなく既存の分割構成（`built_in/`, `std/`, `core/` 等）をそのまま活用する。`src/runtime/cpp/mapping.json` を追加し、命名ルールは plan §3.4 準拠。動作確認が取れるまで git push しない。
3. [ ] [ID: P1-EMIT-CPP-S3] sample 18 件の parity テストが通る — **emit + g++ compile + run + stdout 一致** が完了条件。emit のみ成功では不可。
4. [x] [ID: P1-EMIT-CPP-S4] `pytra-cli2 -emit --target=cpp` を toolchain2 emitter に切り替える — 完了
5. [x] [ID: P1-EMIT-CPP-S5] `toolchain/` への依存をゼロにし、`toolchain/` を除去する — pytra-cli2.py から toolchain/ import ゼロ達成

### P2-SELFHOST: toolchain2 自身の変換テスト

文脈: `docs/ja/plans/plan-pipeline-redesign.md` §3.5

1. [x] [ID: P2-SELFHOST-S1] `src/toolchain2/` の全 .py が parse 成功 — 37/46（9件は ParseContext再帰/Union forward ref/walrus等の parser未対応構文）
2. [x] [ID: P2-SELFHOST-S2] parse → resolve → compile → optimize まで通す — 37/37 全段通過
3. [x] [ID: P2-SELFHOST-S3] golden を `test/selfhost/` に配置し、回帰テストとして維持 — east1/east2/east3/east3-opt 各 37 件
4. [ ] [ID: P2-SELFHOST-S4] Go emitter で toolchain2 を Go に変換し、`go build` が通る — emit 25/25 成功、`go build` は docstring/構文問題で未達

注: 完了済みタスクは [アーカイブ](archive/index.md) に移動済み。
