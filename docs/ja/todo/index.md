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

### P1-EMIT-CPP: C++ emitter

文脈: `docs/ja/plans/p1-emit-cpp-parity.md`

作業ディレクトリ: `toolchain2/emit/cpp/`
必読: [docs/ja/spec/spec-emitter-guide.md](../spec/spec-emitter-guide.md)

1. [x] [ID: P1-EMIT-CPP-S1] C++ emitter を `toolchain2/emit/cpp/` に新規実装し、emit 成功 — fixture 132/132, sample 18/18 emit 成功
2. [x] [ID: P1-EMIT-CPP-S2] 既存 `src/runtime/cpp/` を新パイプラインの emitter 出力に合わせて修正する。新規作成ではなく既存の分割構成（`built_in/`, `std/`, `core/` 等）をそのまま活用する。`src/runtime/cpp/mapping.json` を追加し、命名ルールは plan §3.4 準拠。動作確認が取れるまで git push しない。— runtime symbol/include 解決を metadata + mapping ベースへ統一し、runtime bundle header/source を toolchain2 C++ 型系へ移行、`pytra-cli.py ... path_stringify.py --target cpp` の representative compile 成功
3. [ ] [ID: P1-EMIT-CPP-S3] sample 18 件の parity テストが通る — **emit + g++ compile + run + stdout 一致** が完了条件。emit のみ成功では不可。
4. [x] [ID: P1-EMIT-CPP-S4] `pytra-cli2 -emit --target=cpp` を toolchain2 emitter に切り替える — 完了
5. [x] [ID: P1-EMIT-CPP-S5] `toolchain/` への依存をゼロにし、`toolchain/` を除去する — pytra-cli2.py から toolchain/ import ゼロ達成

### P1-ISINSTANCE-POD: POD 型の isinstance exact match 実装 + golden 生成

文脈: [docs/ja/plans/p1-isinstance-pod-exact.md](../plans/p1-isinstance-pod-exact.md)

1. [ ] [ID: P1-ISINSTANCE-POD-S1] パーサー / resolve が `isinstance(x, int16)` 等の POD 型判定を処理できるようにする
2. [ ] [ID: P1-ISINSTANCE-POD-S2] EAST3 で POD isinstance を exact match 命令に lower する
3. [ ] [ID: P1-ISINSTANCE-POD-S3] `isinstance_pod_exact.py` の golden 生成（east1/east2/east3/east3-opt/linked）
4. [ ] [ID: P1-ISINSTANCE-POD-S4] C++ / Go emitter で compile + run + stdout 一致（`py_assert_stdout` 通過）

### P1-ISINSTANCE-NARROWING: isinstance 後の自動型ナローイング

文脈: [docs/ja/plans/p1-isinstance-narrowing.md](../plans/p1-isinstance-narrowing.md)

1. [x] [ID: P1-NARROW-S1] resolve に isinstance 条件式の検出 + if/elif ブロック内型環境更新を実装
2. [x] [ID: P1-NARROW-S2] early return guard の対応（`if not isinstance(x, T): return` 後の fallthrough narrowing）
3. [x] [ID: P1-NARROW-S3] ternary isinstance の対応（`y = x if isinstance(x, T) else None`）
4. [x] [ID: P1-NARROW-S4] 再代入検出による narrowing 無効化の実装
5. [x] [ID: P1-NARROW-S5] fixture 追加（全 narrowing パターン）+ golden 生成 + parity 確認
- 進捗メモ: resolver/EAST に narrowing を集約し、`JsonVal` は `dict[str,JsonVal]` / `list[JsonVal]` へ narrow。再代入失効と typing fixture/golden を追加。

### P2-SELFHOST: toolchain2 自身の変換テスト

文脈: `docs/ja/plans/plan-pipeline-redesign.md` §3.5

1. [x] [ID: P2-SELFHOST-S1] `src/toolchain2/` の全 .py が parse 成功 — 37/46（9件は ParseContext再帰/Union forward ref/walrus等の parser未対応構文）
2. [x] [ID: P2-SELFHOST-S2] parse → resolve → compile → optimize まで通す — 37/37 全段通過
3. [x] [ID: P2-SELFHOST-S3] golden を `test/selfhost/` に配置し、回帰テストとして維持 — east1/east2/east3/east3-opt 各 37 件
4. [ ] [ID: P2-SELFHOST-S4] Go emitter で toolchain2 を Go に変換し、`go build` が通る — emit 25/25 成功、`go build` は docstring/構文問題で未達

### P4-INT32: int のデフォルトサイズを int64 → int32 に変更

文脈: [docs/ja/plans/p4-int32-default.md](../plans/p4-int32-default.md)

前提: Go selfhost 完了後に着手。

1. [ ] [ID: P4-INT32-S1] spec-east.md / spec-east2.md の `int` → `int32` 正規化ルール変更
2. [ ] [ID: P4-INT32-S2] resolve の型正規化を修正
3. [ ] [ID: P4-INT32-S3] sample 18 件のオーバーフロー確認 + 必要な箇所を `int64` に明示
4. [ ] [ID: P4-INT32-S4] golden 再生成 + 全 emitter parity 確認

注: 完了済みタスクは [アーカイブ](archive/index.md) に移動済み。
