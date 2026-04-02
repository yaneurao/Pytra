<a href="../../en/todo/cpp.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — C++ backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-02

## 運用ルール

- **旧 toolchain1（`src/toolchain/emit/cpp/`）は変更不可。** 新規開発・修正は全て `src/toolchain2/emit/cpp/` で行う（[spec-emitter-guide.md](../spec/spec-emitter-guide.md) §1）。
- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**
- **[emitter 実装ガイドライン](../spec/spec-emitter-guide.md)を必ず読むこと。** parity check ツール、禁止事項、mapping.json の使い方が書いてある。

## 未完了タスク

### P0-OPT-LEVEL-RENAME: `--east3-opt-level` を `--opt-level` に改名し最適化プリセットとして統合する

文脈: [docs/ja/plans/p0-subscript-bounds-east-optimizer.md](../plans/p0-subscript-bounds-east-optimizer.md)

`--east3-opt-level` は内部実装名がそのまま CLI に露出している。`--opt-level` に改名し、`--opt-level` が `negative_index_mode` / `bounds_check_mode` のデフォルトを決定する設計に統合する。emitter はオプションを知らず、EAST3 メタデータのみを参照する。

| `--opt-level` | negative_index | bounds_check |
|---|---|---|
| `0` | `always` | `always` |
| `1`（デフォルト） | `const_only` | `off` |
| `2` | `off` | `off` |

1. [ ] [ID: P0-OPT-LEVEL-S1] `pytra-cli2.py` / `runtime_parity_check_fast.py` / optimizer の `--east3-opt-level` を `--opt-level` に改名する
2. [ ] [ID: P0-OPT-LEVEL-S2] `--opt-level` が `negative_index_mode` / `bounds_check_mode` のデフォルトを決定し、個別オプションで上書きできるようにする
3. [ ] [ID: P0-OPT-LEVEL-S3] spec-options.md / spec-east3-optimizer.md / tutorial を更新する
4. [ ] [ID: P0-OPT-LEVEL-S4] fixture + sample + stdlib parity に回帰がないことを確認する

### P0-CPP-VARIANT: C++ を std::variant ベースに移行し object/box/unbox を廃止する

文脈: [docs/ja/plans/plan-cpp-variant-migration.md](../plans/plan-cpp-variant-migration.md)
仕様: [docs/ja/spec/spec-adt.md](../spec/spec-adt.md)

Phase 1（variant 出力追加）、Phase 2 の S5 まで完了済み（[archive/20260402.md](archive/20260402.md) 参照）。

**Phase 2: object 型を削除（残）**

1. [ ] [ID: P0-CPP-VARIANT-S6] `object.h` の `object` クラス削除に向けた blocker を分離し、削除順を固定する
2. [ ] [ID: P0-CPP-VARIANT-S6A] C++ runtime / emitter に残っている不要な `PYTRA_TID_OBJECT` / object-type-id 正規化の残骸を削除する
3. [ ] [ID: P0-CPP-VARIANT-S7] fixture 全件 + sample 全件が `object` 型なしで PASS することを確認する

**Phase 3: box/unbox 削除**

4. [ ] [ID: P0-CPP-VARIANT-S8] C++ emitter の box/unbox 処理を削除し、variant 代入 / `std::get` に置換する

**Phase 4: EAST から object 退化 / box / unbox を削除**

5. [ ] [ID: P0-CPP-VARIANT-S10] lower.py の Boxing（`resolved_type="object"` 生成）と iter boundary を削除する
6. [ ] [ID: P0-CPP-VARIANT-S11] EAST3 validation に「`resolved_type: "object"` ならエラー」を追加する
7. [ ] [ID: P0-CPP-VARIANT-S12] 全言語の fixture + sample が PASS することを確認する

### P20-CPP-SELFHOST: C++ emitter で toolchain2 を C++ に変換し g++ build を通す

文脈: [docs/ja/plans/p4-cpp-selfhost.md](../plans/p4-cpp-selfhost.md)

S0〜S4 完了済み（[archive/20260402.md](archive/20260402.md) 参照）。

1. [ ] [ID: P20-CPP-SELFHOST-S5] selfhost C++ バイナリを g++ でビルドし、リンクが通ることを確認する
2. [ ] [ID: P20-CPP-SELFHOST-S6] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root fixture` で fixture parity が PASS することを確認する
3. [ ] [ID: P20-CPP-SELFHOST-S7] `run_selfhost_parity.py --selfhost-lang cpp --emit-target cpp --case-root sample` で sample parity が PASS することを確認する
