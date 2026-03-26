# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-27

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

文脈: [docs/ja/plans/p1-emit-go-parity.md](../plans/p1-emit-go-parity.md)
必読: [docs/ja/spec/spec-emitter-guide.md](../spec/spec-emitter-guide.md)

1. [x] [ID: P1-GO-PARITY-S1] list/dict comprehension の Go 変換を実装
2. [x] [ID: P1-GO-PARITY-S2] EAST 不足の修正: `write_text` 等を resolve で BuiltinCall に lowering、with 文 parser 対応、bytearray 型伝播
3. [x] [ID: P1-GO-PARITY-S3] fixture 132 件で `go run` + stdout 一致
4. [x] [ID: P1-GO-PARITY-S4] sample 18 件で `go run` + stdout 一致（PNG/GIF artifact CRC32 一致を含む）

### P1-SPEC-CONFORM2: 仕様整合 フェーズ2+3（Codex-review 追加指摘対応）

文脈: [docs/ja/plans/p1-spec-conform2.md](../plans/p1-spec-conform2.md)

フェーズ1 (link) は完了。フェーズ2 (emit) とフェーズ3 (optimize/compile) が残り。

**フェーズ2: emit（workaround を剥がす）**

7. [x] [ID: P1-SPEC-CONFORM2-S7] `emit/go/emitter.py`: 型推論・型変更・cast 追加・ハードコードモジュール判定を除去 — `_emit_unbox()` の `Name` fallback を削除し、runtime lane を toolchain2 生成へ同期して `json_extended` Go parity を維持
8. [x] [ID: P1-SPEC-CONFORM2-S8] `emit/cpp/emitter.py`: 同上 — `Assign` の target/value 型推論と `VarDecl` の `unknown -> int64` fallback を除去し、`unknown` は `auto`、range target は EAST3 `target_type`、skipped runtime value は metadata + mapping 経由へ整理
9. [x] [ID: P1-SPEC-CONFORM2-S9] `emit/common/code_emitter.py`: mapping.json のみで分岐するように整理 — skipped runtime symbol/value 名解決と import binding -> runtime helper 名解決を common helper へ集約し、Go/C++ emitter の `mapping.calls` 直参照と prefix 組み立て重複を削除

**フェーズ3: optimize / compile（型責務を前段に戻す）**

10. [ ] [ID: P1-SPEC-CONFORM2-S10] `optimize/passes/typed_repeat_materialization.py`: resolved_type 後付け補完を除去
11. [ ] [ID: P1-SPEC-CONFORM2-S11] `optimize/passes/typed_enumerate_normalization.py`: 同上
12. [x] [ID: P1-SPEC-CONFORM2-S12] `compile/passes.py`: int32 先行混入を戻す（bytes/bytearray 系の `uint8` target を `int64` に復帰）
13. [x] [ID: P1-SPEC-CONFORM2-S13] golden 再生成 + parity 維持確認（fixture 132/132, sample 18/18, pytra 33/33）

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

### P4: int のデフォルトサイズを int64 → int32 に変更

Python の `int` を `int64` に正規化しているが、C++/Go/Java/C# は `int` が 32bit で、通常利用には十分。
64bit はメモリ・キャッシュ効率が悪い。`int` → `int32` に変更し、64bit が必要な場合はユーザーが `int64` と明示する。

影響範囲:
- spec-east.md §6.2 の正規化ルール変更
- 全 golden 再生成
- 全 emitter の型マッピング修正
- sample のオーバーフロー確認（中間計算が 32bit を超えないか）
- `len()` の戻り値型も `int32` に

前提: Go selfhost 完了後に着手。

1. [ ] [ID: P4-INT32-S1] spec-east.md / spec-east2.md の `int` → `int32` 正規化ルール変更
2. [ ] [ID: P4-INT32-S2] resolve の型正規化を修正
3. [ ] [ID: P4-INT32-S3] sample 18 件のオーバーフロー確認 + 必要な箇所を `int64` に明示
4. [ ] [ID: P4-INT32-S4] golden 再生成 + 全 emitter parity 確認

注: 完了済みタスクは [アーカイブ](archive/index.md) に移動済み。
