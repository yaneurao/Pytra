<a href="../../ja/plans/p0-pytra-cli-boundary-and-dispatch-removal.md"><img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square"></a>

> [!WARNING]
> This file is synchronized from `docs/ja/plans/p0-pytra-cli-boundary-and-dispatch-removal.md` and still requires manual English translation.

> Source of truth: `docs/ja/plans/p0-pytra-cli-boundary-and-dispatch-removal.md`

# P0: `pytra-cli` の責務再編（命名統一 + target分岐撤去）

最終更新: 2026-03-05

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-PYTRA-CLI-REALIGN-01`

背景:
- `src/pytra/` は runtime/stdlib の SoT を配置する領域であり、CLI 実装を置く責務ではない。
- 直近で CLI を `src/pytra_cli.py` へ退避したが、命名規約（`pytra-cli.py` などハイフン系）と不一致で誤読しやすい。
- 現行 `pytra-cli` は target 言語ごとの build/run 分岐（`if target == ...`）を内部に多数保持しており、backend の責務を侵食している。
- ユーザー要件として、CLI は言語分岐を持たず、共通入口として backend プロファイルを解決して実行する構成へ寄せる必要がある。

目的:
- CLI 実体を `src/pytra-cli.py` に統一し、`pytra_cli.py` 命名を廃止する。
- `pytra-cli` から target 固有分岐を撤去し、backend ごとの build/run/transpile 契約は別レイヤー（プロファイル/レジストリ）へ移譲する。
- parity/smoke を含む実行導線を「CLI単一路線」に揃え、ツール側の target 直書きを縮小する。

対象:
- `src/pytra-cli.py`
- ルートランチャー `./pytra`
- `tools/check/runtime_parity_check.py` の CLI 呼び出し経路
- `tools/unittest/tooling/test_pytra_cli.py`
- 関連ドキュメント（`docs/ja|en/how-to-use.md`, `docs/ja|en/spec/spec-make.md`）

非対象:
- backend のコード生成品質改善
- runtime API 仕様変更
- selfhost 導線の機能拡張（別IDで実施）

受け入れ基準:
- `src/pytra-cli.py` が唯一の CLI 実装ファイルであり、`src/pytra_cli.py` は存在しない。
- `src/pytra-cli.py` に target ごとの build/run 実装分岐（`if target == "..."` 群）が残らない。
- target 固有情報は backend プロファイル（外部定義）として管理し、CLI は共通ディスパッチのみを担う。
- `tools/check/runtime_parity_check.py` が `pytra-cli` 経由で実行でき、少なくとも `cpp/java` の sample parity が非退行。
- `tools/unittest/tooling/test_pytra_cli.py` が新構成で通過する。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `python3 -m py_compile src/pytra-cli.py tools/check/runtime_parity_check.py`
- `python3 -m unittest discover -s tools/unittest/tooling -p 'test_pytra_cli.py' -v`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets cpp,java 01_mandelbrot`

## 分解

- [x] [ID: P0-PYTRA-CLI-REALIGN-01-S1-01] `pytra-cli` の責務境界（CLI本体 / backendプロファイル / 実行runner）を文書化し、禁止事項（target分岐直書き）を固定する。
- [x] [ID: P0-PYTRA-CLI-REALIGN-01-S1-02] CLI 実体を `src/pytra-cli.py` 命名へ統一し、`./pytra` / parity / tooling 参照を更新する。
- [x] [ID: P0-PYTRA-CLI-REALIGN-01-S2-01] target 固有 build/run/transpile 契約を `toolchain` 側のプロファイル定義へ抽出する。
- [x] [ID: P0-PYTRA-CLI-REALIGN-01-S2-02] `src/pytra-cli.py` を「引数正規化 + プロファイル解決 + 共通実行」のみに縮退し、target 分岐を撤去する。
- [x] [ID: P0-PYTRA-CLI-REALIGN-01-S2-03] `--codegen-opt` など target 非互換オプションの受理条件をプロファイルベースで検証し、fail-fast を統一する。
- [x] [ID: P0-PYTRA-CLI-REALIGN-01-S3-01] parity/tooling をプロファイル駆動の新CLI契約へ追従させ、target 直書き重複を削減する。
- [x] [ID: P0-PYTRA-CLI-REALIGN-01-S3-02] unit/parity/docs を更新し、回帰を固定する。

決定ログ:
- 2026-03-05: ユーザー指示により、`pytra_cli.py` ではなく `pytra-cli.py` を正式名称とし、CLI から target ごとの分岐実装を排除する方針を確定。
- 2026-03-05: [ID: `P0-PYTRA-CLI-REALIGN-01-S1-01`] `docs/ja/spec/spec-make.md` / `docs/en/spec/spec-make.md` に `pytra-cli` 境界節を追加し、CLI本体・backendプロファイル・実行runnerの責務/禁止事項（target分岐直書き禁止、runtimeファイル直書き禁止、tooling重複禁止）を固定した。
- 2026-03-05: [ID: `P0-PYTRA-CLI-REALIGN-01-S2-01`] `src/toolchain/misc/pytra_cli_profiles.py` を新設し、target 固有の出力拡張子・出力パス決定・non-cpp build/run コマンド契約を CLI 本体から抽出。`src/pytra-cli.py` は契約参照へ切替え、`test_pytra_cli.py` / `test_pytra_cli_profiles.py` を通過。
- 2026-03-05: [ID: `P0-PYTRA-CLI-REALIGN-01-S2-02`] `src/pytra-cli.py` の `target == ...` 分岐を撤去し、`TargetProfile.build_driver` を使った共通ディスパッチへ移行。transpile/build の target 依存は `pytra_cli_profiles.py` に集約。
- 2026-03-05: [ID: `P0-PYTRA-CLI-REALIGN-01-S2-03`] `validate_profile_option_compatibility()` を追加して profile ベース fail-fast を導入し、`--codegen-opt` の non-cpp 禁止と non-cpp `--build` 時の `--compiler/--std/--opt/--exe` 禁止を固定。`test_pytra_cli.py` / `test_pytra_cli_profiles.py` を拡張して回帰を追加。
- 2026-03-05: [ID: `P0-PYTRA-CLI-REALIGN-01-S3-01`] `tools/check/runtime_parity_check.py` の target order/needs の直書きを `pytra_cli_profiles` 参照へ置換し、parity の target 契約重複を削減。`test_runtime_parity_check_cli.py` を新CLI契約期待値へ更新し、tooling unit が通過。
- 2026-03-05: [ID: `P0-PYTRA-CLI-REALIGN-01-S3-02`] non-cpp `run_cmd` が stderr へ誤転送される不具合を修正し、`test_pytra_cli.py` に stdout 保持回帰を追加。`python3 tools/check/runtime_parity_check.py --case-root sample --targets cpp,java 01_mandelbrot` を再実行して `cpp/java` とも artifact size/CRC32 一致を確認。
