<a href="../../en/todo/rust.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — Rust backend

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-03-29 (更新: 2026-03-29)

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。
- **parity テストは「emit + compile + run + stdout 一致」を完了条件とする。**

## 現状

- toolchain2 に Rust emitter は未実装（`src/toolchain2/emit/rs/` が存在しない）
- runtime は `src/runtime/rs/` に存在する（旧 toolchain1 時代の実装）
- 旧 toolchain1 の Rust emitter は `src/toolchain/emit/rs/` に存在するが、toolchain2 への移行が必要

## 未完了タスク

### P7-RS-EMITTER: Rust emitter を toolchain2 に新規実装する

前提: Go emitter（参照実装）と CommonRenderer が安定してから着手。

1. [x] [ID: P7-RS-EMITTER-S1] `src/toolchain2/emit/rs/` に Rust emitter を新規実装する — Go emitter を参考に CommonRenderer + override 構成で作成。Rust 固有のノード（所有権・ライフタイム・borrow、match、impl ブロック等）だけ override として残す
   - 完了: `src/toolchain2/emit/rs/{emitter.py,types.py,__init__.py}` と `src/toolchain2/emit/profiles/rs.json` を作成。全 1001 件 fixture エラーなし emit 成功。pytra-cli2.py に rs target を追加。
2. [x] [ID: P7-RS-EMITTER-S2] `src/runtime/rs/mapping.json` を作成し、runtime_call の写像を定義する
   - 完了: `src/runtime/rs/mapping.json` を作成。Go mapping.json を参考に Rust 向け関数名でマッピング定義。
3. [ ] [ID: P7-RS-EMITTER-S3] fixture 132 件 + sample 18 件の Rust emit 成功を確認する
4. [ ] [ID: P7-RS-EMITTER-S4] Rust runtime を toolchain2 の emit 出力と整合させる（旧 toolchain1 runtime の引き継ぎ or 再実装）
5. [ ] [ID: P7-RS-EMITTER-S5] fixture + sample の Rust compile + run parity を通す

### P9-RS-SELFHOST: Rust emitter で toolchain2 を Rust に変換し cargo build を通す

前提: P7-RS-EMITTER 完了後に着手。

1. [ ] [ID: P9-RS-SELFHOST-S0] selfhost 対象コード（`src/toolchain2/` 全 .py）で戻り値型の注釈が欠けている関数に型注釈を追加する — resolve が `inference_failure` にならない状態にする（P4/P6 と共通。先に完了した側の成果を共有）
2. [ ] [ID: P9-RS-SELFHOST-S1] toolchain2 全 .py を Rust に emit し、cargo build が通ることを確認する
3. [ ] [ID: P9-RS-SELFHOST-S2] cargo build 失敗ケースを emitter/runtime の修正で解消する（EAST の workaround 禁止）
4. [ ] [ID: P9-RS-SELFHOST-S3] selfhost 用 Rust golden を配置し、回帰テストとして維持する
