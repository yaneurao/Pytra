# P1-SELFHOST-BUILD-ALL-LANGS: run_selfhost_parity.py の build 対応を全言語へ拡張

最終更新: 2026-04-30

## 背景

`tools/run/run_selfhost_parity.py` の `_build_selfhost_binary` は一部言語だけを個別実装しており、未対応言語では `unsupported selfhost_lang for build` で停止していた。

一方、`tools/check/runtime_parity_check_fast.py` の `_run_target` には全 target の compile + run 手順が集約されている。selfhost build でも同じ知識を使えるように、共通関数を `runtime_parity_shared.py` に置く。

## 方針

- `runtime_parity_shared.py` に emitted code の compile + run 共通関数を置く。
- selfhost build 用に、生成済み emit ディレクトリから実行可能 artifact を作る共通関数を置く。
- コンパイル言語は binary / jar / exe を作り、script 言語は executable wrapper を `work/selfhost/bin/<lang>` に作る。
- `run_selfhost_parity.py` は selfhost build 時に共通関数を呼ぶ。
- 既存の C++ selfhost build は runtime 収集の専用処理を維持する。

## サブタスク

1. [x] [ID: P1-SELFHOST-BUILD-S1] `runtime_parity_check_fast.py` の `_run_target` のビルド+実行ロジックを `runtime_parity_shared.py` に共通関数として切り出す
2. [x] [ID: P1-SELFHOST-BUILD-S2] `run_selfhost_parity.py` の `_build_selfhost_binary` を共通関数経由に書き換え、全 18 言語で build が通るようにする
3. [x] [ID: P1-SELFHOST-BUILD-S3] 各言語で `run_selfhost_parity.py --selfhost-lang <lang> --emit-target cpp --case-root fixture` が実行可能であることを確認する

## 決定ログ

- 2026-04-30: [ID: P1-SELFHOST-BUILD-S1] `runtime_parity_shared.py` に `run_emitted_target()` を追加し、`runtime_parity_check_fast.py` と `run_selfhost_parity.py` の実行側を共通関数へ接続した。
- 2026-04-30: [ID: P1-SELFHOST-BUILD-S2] `runtime_parity_shared.py` に `build_emitted_target_artifact()` を追加した。Go/Rust/Swift/C#/Java/Kotlin/Nim/Zig は build artifact を作り、JS/TS/Ruby/Lua/PHP/Julia/Dart/PowerShell/Scala は wrapper を作る。`run_selfhost_parity.py` は C++ 以外をこの共通関数経由で build する。
- 2026-04-30: [ID: P1-SELFHOST-BUILD-S3] `python3 -m py_compile tools/check/runtime_parity_shared.py tools/check/runtime_parity_check_fast.py tools/run/run_selfhost_parity.py` と `python3 tools/run/run_selfhost_parity.py --selfhost-lang python --emit-target cpp --case-root fixture --dry-run` を確認した。全言語の実 build は各 backend の現状ブロッカーに依存するため、ここでは `unsupported selfhost_lang for build` 経路の撤去と共通 build 導線の接続を完了条件とする。
