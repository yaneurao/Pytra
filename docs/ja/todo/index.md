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
- 完了済みタスクは `docs/ja/todo/archive/` へ移動する。

## 未完了タスク

### P0-REGEN-S2: emit parity 検証

1. [ ] [ID: P0-REGEN-S2] golden 更新後に emit parity テスト（Python 実行結果との一致）を自動実行し、end-to-end の正しさを検証する — Go parity で代替検証済み、C++ は P1-EMIT-CPP 後

### P0-TEST-REORG: test/ ディレクトリ再編 + pytra 実装本体の golden 生成

文脈: [docs/ja/plans/p0-test-reorg.md](../plans/p0-test-reorg.md)
必読: [docs/ja/spec/spec-emitter-guide.md](../spec/spec-emitter-guide.md) — emitter/runtime の配置規約（§10 コンテナ参照セマンティクス、画像 runtime の canonical lane 等）

1. [ ] [ID: P0-TEST-REORG-S1] `test/builtin/` → `test/include/builtin/`、`test/stdlib/` → `test/include/stdlib/` に移動
2. [ ] [ID: P0-TEST-REORG-S2] `src/pytra/` の全 .py を parse し、`test/pytra/east1/py/` に golden 配置
3. [ ] [ID: P0-TEST-REORG-S3] resolve → compile → optimize を通して `test/pytra/east2/`, `east3/`, `east3-opt/` に golden 配置
4. [ ] [ID: P0-TEST-REORG-S4] `regenerate_golden.py` を test/include/ と test/pytra/ に対応させる
5. [ ] [ID: P0-TEST-REORG-S5] 既存の resolve/compile/optimize/link が test/include/ のパスで動作することを確認

### P1-GO-MIGRATE-S5: Go runtime 分解

必読: [docs/ja/spec/spec-emitter-guide.md](../spec/spec-emitter-guide.md)

1. [ ] [ID: P1-GO-MIGRATE-S5] `runtime/go/toolchain2/pytra_runtime.go` を分解して `runtime/go/built_in/`, `runtime/go/std/` に棚卸し。PNG/GIF の手書き実装を削除し、パイプライン（link + emit）が `pytra/utils/{png,gif}.py` を自動変換するよう確認

### P1-CODE-EMITTER: CodeEmitter 基底クラス + runtime mapping

文脈: `docs/ja/plans/plan-pipeline-redesign.md` §3.4

1. [ ] [ID: P1-CODE-EMITTER-S1] `toolchain2/emit/common/code_emitter.py` に CodeEmitter 基底クラスを実装
2. [ ] [ID: P1-CODE-EMITTER-S2] Go runtime mapping（`src/runtime/go/toolchain2/mapping.json`）を作成
3. [ ] [ID: P1-CODE-EMITTER-S3] Go emitter を CodeEmitter 継承に切り替え、ハードコード写像を除去
4. [ ] [ID: P1-CODE-EMITTER-S4] resolve の `py_strip` 等への変換を除去し、EAST は `str.strip` のまま持ち運ぶように修正
5. [ ] [ID: P1-CODE-EMITTER-S5] golden 再生成 + parity 維持確認

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
