# P1: 統合CLI `./pytra` の Rust target 追加

最終更新: 2026-02-27

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-PYTRA-CLI-RS-01`

背景:
- 現在の `./pytra` は `--target cpp` のみ対応で、Rust 変換は `py2rs.py` を直接呼ぶ必要がある。
- 入口を `./pytra` に寄せる方針に対して、Rust が統合CLI対象外だと操作一貫性が崩れる。
- 一時出力については新規トップレベル乱立を避け、既存 `out/`（必要なら `/tmp`）へ集約したい。

目的:
- `./pytra` から Rust 変換を実行できるようにし、C++ と同じ入口で運用できる状態にする。

対象:
- `src/pytra/cli.py` の target dispatch 拡張（`rs`）
- `--target rs` 時の出力パス整理（`--output` / `--output-dir`）
- `docs/ja/how-to-use.md` の統合CLI節への Rust 例追加

非対象:
- Rust backend 本体（`py2rs.py`）の意味論変更
- Rust 用 `--build` の高度化（Cargo 連携など）
- 既存 `py2rs.py` CLI の廃止

受け入れ基準:
- `./pytra INPUT.py --target rs --output OUT.rs` が成功する。
- `./pytra INPUT.py --target rs --output-dir DIR` で `DIR` 配下へ `.rs` が生成される。
- `./pytra --help` に `rs` が表示される。
- `docs/ja/how-to-use.md` に `./pytra --target rs` 使用例がある。
- 一時出力ポリシー（新規トップレベル乱立を避ける）が文書化されている。

確認コマンド:
- `./pytra --help`
- `./pytra test/fixtures/core/add.py --target rs --output /tmp/add.rs`
- `./pytra test/fixtures/core/add.py --target rs --output-dir out/rs_demo`
- `python3 -m py_compile src/pytra/cli.py`

決定ログ:
- 2026-02-27: ユーザー指示により、`--target rs` を P1 で TODO へ追加する方針を確定。

## 分解

- [ ] [ID: P1-PYTRA-CLI-RS-01-S1-01] `src/pytra/cli.py` に `--target rs` dispatch を追加し、`py2rs.py` 呼び出しを統合する。
- [ ] [ID: P1-PYTRA-CLI-RS-01-S1-02] Rust 出力時の `--output` / `--output-dir` 仕様を確定し、衝突ケース（拡張子、同名生成）を整理する。
- [ ] [ID: P1-PYTRA-CLI-RS-01-S1-03] `docs/ja/how-to-use.md` の統合CLI節へ Rust 例を追記し、出力先運用（`out/` / `/tmp`）を明記する。
