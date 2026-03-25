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

### P1-SPEC-CONFORM: 仕様整合（Codex-review 指摘対応）

resolve / parser / validator が spec-east1.md / spec-east2.md の契約から逸脱している箇所を修正する。

1. [ ] [ID: P1-SPEC-CONFORM-S1] validator 修正: `resolved_type: "unknown"` を error 扱いにする。`RangeExpr` を `_EXPR_KINDS` に追加。未正規化型を warning → error に昇格。missing resolved_type を error にする
2. [ ] [ID: P1-SPEC-CONFORM-S2] ForRange の loop target `resolved_type` を `unknown` 固定から正しい型に修正（resolve）
3. [ ] [ID: P1-SPEC-CONFORM-S3] `_resolve_builtin_call()` の `if name == ...` ハードコード連鎖を除去し、registry（extern_v2）からの型解決に統一する
4. [ ] [ID: P1-SPEC-CONFORM-S4] `_infer_stdlib_return_type()` の math/time/random/json/pathlib 決め打ちを除去し、stdlib EAST1 の FunctionDef から解決に統一する
5. [ ] [ID: P1-SPEC-CONFORM-S5] parser の `_normalize_typing_prefix()` を除去し、EAST1 で `typing.List[int]` 等をソースのまま保持する。resolve 側で正規化する
6. [ ] [ID: P1-SPEC-CONFORM-S6] `resolve_east1_to_east2()` の空 registry silent fallback を削除し、registry 未指定時はエラーにする
7. [ ] [ID: P1-SPEC-CONFORM-S7] golden 再生成 + parity 維持確認

### P1-SPEC-CONFORM2: 仕様整合（Codex-review 追加指摘対応）

compile / link / optimize / emit の仕様逸脱を修正する。修正順は link → emit → optimize/compile。

**フェーズ1: link（canonical source を正す）**

1. [ ] [ID: P1-SPEC-CONFORM2-S1] `type_id.py`: `bases` (複数) を正しく読む。未定義基底・循環継承を fail-fast にする
2. [ ] [ID: P1-SPEC-CONFORM2-S2] `runtime_discovery.py`: .east 読込失敗の `except: pass` をエラーにする
3. [ ] [ID: P1-SPEC-CONFORM2-S3] `manifest_loader.py`: 不正 entry・欠損ファイル・不正 JSON の `continue` 黙殺をエラーにする
4. [ ] [ID: P1-SPEC-CONFORM2-S4] `linker.py`: manifest `modules[*].input` を raw EAST3 入力パスに修正
5. [ ] [ID: P1-SPEC-CONFORM2-S5] `normalize_runtime_calls.py`: 暫定互換レイヤを除去
6. [ ] [ID: P1-SPEC-CONFORM2-S6] `expand_defaults.py`: シンボル解決を module_id::name ベースに限定し、曖昧解決を防止

**フェーズ2: emit（workaround を剥がす）**

7. [ ] [ID: P1-SPEC-CONFORM2-S7] `emit/go/emitter.py`: 型推論・型変更・cast 追加・ハードコードモジュール判定を除去
8. [ ] [ID: P1-SPEC-CONFORM2-S8] `emit/cpp/emitter.py`: 同上
9. [ ] [ID: P1-SPEC-CONFORM2-S9] `emit/common/code_emitter.py`: mapping.json のみで分岐するように整理

**フェーズ3: optimize / compile（型責務を前段に戻す）**

10. [ ] [ID: P1-SPEC-CONFORM2-S10] `optimize/passes/typed_repeat_materialization.py`: resolved_type 後付け補完を除去
11. [ ] [ID: P1-SPEC-CONFORM2-S11] `optimize/passes/typed_enumerate_normalization.py`: 同上
12. [ ] [ID: P1-SPEC-CONFORM2-S12] `compile/passes.py`: int32 先行混入を戻す（P4-INT32 着手前は現仕様に合わせる）
13. [ ] [ID: P1-SPEC-CONFORM2-S13] golden 再生成 + parity 維持確認

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
