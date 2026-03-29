<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

最終更新: 2026-03-29

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 各領域の agent は自分の領域ファイル内で優先度順（小さい P 番号から）に着手する。
- P0 は緊急タスク。`infra.md` に積み、インフラ担当 agent が対応する。他の領域 agent は P0 に着手しない（重複着手を防止）。P0 が他領域の作業をブロックすることはない。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモ（件数等）を追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **emitter の parity テストは「emit 成功」ではなく「emit + compile + run + stdout 一致」を完了条件とする。** emit だけ成功してもプレースホルダーコードが混入している可能性がある。
- **タスク詳細は領域別ファイルに記載する。** この index.md は優先度一覧と領域リンクのみ保持する。

## 領域別 TODO

| 領域 | ファイル | 主なタスク |
|---|---|---|
| C++ backend | [cpp.md](./cpp.md) | P3-CR-CPP, P4-CPP-SELFHOST |
| Go backend | [go.md](./go.md) | P1-GO-CONTAINER, P5-CR-GO, P6-GO-SELFHOST |
| Rust backend | [rust.md](./rust.md) | P7-RS-EMITTER |
| TS/JS backend | [ts.md](./ts.md) | P8-TS-EMITTER |
| インフラ・ツール | [infra.md](./infra.md) | P10-REORG, P11-VERSION-GATE, P20-INT32 |

## 全タスク優先度一覧

各領域内の優先度順を示す。P0 は領域横断の緊急タスク（主にインフラ担当が対応）。

| 優先度 | ID | 領域 | 概要 |
|---|---|---|---|
| P1 | P1-GO-CONTAINER-WRAPPER | Go | container 既定表現を spec 準拠に |
| P3 | P3-COMMON-RENDERER-CPP | C++ | CommonRenderer 移行 + fixture parity |
| P4 | P4-CPP-SELFHOST | C++ | toolchain2 → C++ 変換 + g++ build |
| P5 | P5-COMMON-RENDERER-GO | Go | CommonRenderer 移行 + fixture parity |
| P6 | P6-GO-SELFHOST | Go | toolchain2 → Go 変換 + go build |
| P7 | P7-RS-EMITTER | Rust | Rust emitter を toolchain2 に新規実装 |
| P8 | P8-TS-EMITTER | TS/JS | TS/JS emitter を toolchain2 に新規実装 |
| P9 | P9-RS-SELFHOST | Rust | toolchain2 → Rust 変換 + cargo build |
| P10 | P10-REORG | インフラ | tools/ と test/unit/ の棚卸し |
| P11 | P11-VERSION-GATE | インフラ | toolchain2 用バージョンチェッカー |
| P12 | P12-TS-SELFHOST | TS/JS | toolchain2 → TS 変換 + tsc build |
| P20 | P20-INT32 | インフラ | int のデフォルトサイズ int64 → int32 |

注: 完了済みタスクは [アーカイブ](archive/index.md) に移動済み。
