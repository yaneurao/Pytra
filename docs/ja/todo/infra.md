<a href="../../en/todo/infra.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — インフラ・ツール・仕様

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-30

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。

完了済みタスクは [アーカイブ](archive/20260430.md) を参照。

## 未完了タスク

### P1-EMITTER-HOST-RUNNER: emitter host parity の自動化スクリプトを作る

現在 emitter host の検証は手動（`pytra-cli.py -build` + target 言語でビルド + diff）で行い、`.parity-results/emitter_host_<lang>.json` も手書きしている。これを自動化する `run_emitter_host_parity.py` を作る。

処理フロー:
1. `pytra-cli.py -build src/toolchain/emit/<emitter>/cli.py --target <host_lang>` で emitter を変換
2. `runtime_parity_shared.py` の共通ビルド関数で target 言語のバイナリ/スクリプトを生成
3. ビルドした emitter に fixture の linked manifest を食わせて C++ (等) を生成
4. Python 版 emitter の出力と diff
5. 結果を `.parity-results/emitter_host_<host_lang>.json` に自動書き込み

1. [ ] [ID: P1-EHOST-RUNNER-S1] `tools/run/run_emitter_host_parity.py` を実装する（`--host-lang <lang> --hosted-emitter cpp --case-root fixture`）
2. [ ] [ID: P1-EHOST-RUNNER-S2] 結果を `.parity-results/emitter_host_<host_lang>.json` の `emitters` map に自動書き込みする
3. [ ] [ID: P1-EHOST-RUNNER-S3] 各 backend の P1-HOST-CPP-EMITTER タスクの S2 を `run_emitter_host_parity.py` の実行に更新する

### 保留中タスク

- P20-INT32 は [plans/p4-int32-default.md](../plans/p4-int32-default.md) に保留中。再開時にここへ戻す。
