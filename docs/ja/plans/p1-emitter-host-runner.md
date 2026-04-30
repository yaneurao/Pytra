# P1-EMITTER-HOST-RUNNER: emitter host parity 自動化

最終更新: 2026-04-30

## 背景

emitter host parity は手動で `pytra-cli.py -build`、host 言語の build/run、Python 版 emitter との diff、`.parity-results/emitter_host_<lang>.json` 更新を行っていた。

## 方針

- `tools/run/run_emitter_host_parity.py` を追加し、host 言語と hosted emitter を引数で受ける。
- host 言語への emitter 変換は `src/pytra-cli.py -build src/toolchain/emit/<emitter>/cli.py --target <host>` を使う。
- host 側 build は `runtime_parity_shared.py` の `build_emitted_target_artifact()` を使う。
- fixture の linked manifest は指定がなければ代表 fixture から生成する。
- Python 版 emitter と hosted emitter の出力ディレクトリを再帰比較する。
- 結果は `.parity-results/emitter_host_<host>.json` の `emitters` map へ merge する。

## サブタスク

1. [x] [ID: P1-EHOST-RUNNER-S1] `tools/run/run_emitter_host_parity.py` を実装する
2. [x] [ID: P1-EHOST-RUNNER-S2] 結果を `.parity-results/emitter_host_<host_lang>.json` の `emitters` map に自動書き込みする
3. [x] [ID: P1-EHOST-RUNNER-S3] 各 backend の P1-HOST-CPP-EMITTER タスクの S2 を `run_emitter_host_parity.py` の実行に更新する

## 決定ログ

- 2026-04-30: [ID: P1-EHOST-RUNNER-S1/S2] `tools/run/run_emitter_host_parity.py` を追加。`--host-lang <lang> --hosted-emitter cpp --case-root fixture` で host emitter を build し、Python emitter 出力と比較して `emitters` map に結果を書き込む。
- 2026-04-30: [ID: P1-EHOST-RUNNER-S3] 各 backend TODO の `P1-HOST-CPP-EMITTER-*-S2` を runner 実行へ更新した。
- 2026-04-30: 検証として `python3 -m py_compile tools/run/run_emitter_host_parity.py` と `python3 tools/run/run_emitter_host_parity.py --help` を実行。代表の Go-hosted C++ emitter 実行は現行生成 Go の型不整合で build fail まで進み、runner が `.parity-results/emitter_host_go.json` へ結果を書けることを確認した（既存 PASS 記録を壊さないよう手元 JSON は復元）。
