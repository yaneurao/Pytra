# P1: Rust runtime 外出し（inline helper / `mod pytra` 埋め込み撤去）

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RS-RUNTIME-EXT-01`

背景:
- 現在の Rust 生成コード（例: `sample/rs/01_mandelbrot.rs`）には `py_*` helper 群と `mod pytra { ... }` が inline 展開されている。
- inline 展開は単一ファイル実行の利便性はあるが、生成コード肥大化・runtime 実装重複・runtime 更新漏れの温床になる。
- `src/runtime/rs/pytra/built_in/py_runtime.rs` など runtime 正本は既に存在する一方、`py2rs.py` は単一 `.rs` 出力のみで runtime 配置導線を持たない。

目的:
- Rust backend の生成コードから runtime/helper 本体の inline 出力を撤去し、runtime 外部参照方式へ統一する。
- runtime 正本を `src/runtime/rs/pytra/` に一本化し、emitter は呼び出し生成に専念させる。

対象:
- `src/hooks/rs/emitter/rs_emitter.py`
- `src/py2rs.py`
- `src/runtime/rs/pytra/`（不足 API の補完を含む）
- `test/unit/test_py2rs_smoke.py`
- `tools/check_py2rs_transpile.py`
- `tools/runtime_parity_check.py`（Rust 導線）
- `tools/regenerate_samples.py` と `sample/rs` 再生成

非対象:
- Rust backend の性能最適化（clone 削減、括弧削減など）
- `isinstance/type_id` 意味仕様の再設計
- Cargo プロジェクト生成機能の追加

受け入れ基準:
- `py2rs` 生成コードに runtime/helper 本体（`fn py_perf_counter`、`fn py_isdigit`、`mod pytra { ... }` など）が inline 出力されない。
- 生成コードは外部 runtime ファイル参照で build/run できる。
- `check_py2rs_transpile` / Rust smoke / parity（最低 `sample/18`、原則 `--all-samples`）が非退行で通る。
- `sample/rs` 再生成後に inline helper 残存ゼロを確認できる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rs_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets rs --all-samples --ignore-unstable-stdout`
- `python3 tools/regenerate_samples.py --langs rs --force`
- `rg -n "fn py_perf_counter|fn py_isdigit|mod pytra \\{" sample/rs`

決定ログ:
- 2026-02-28: ユーザー指示により、Rust の helper/runtime 分離を `P1` として新規起票した。

## 分解

- [ ] [ID: P1-RS-RUNTIME-EXT-01-S1-01] Rust emitter の inline helper 出力一覧と `src/runtime/rs/pytra` 正本 API 対応表を確定する。
- [ ] [ID: P1-RS-RUNTIME-EXT-01-S1-02] Rust 生成物の runtime 参照方式（`mod/use` 構成と出力ディレクトリ配置契約）を確定し、fail-closed 条件を文書化する。
- [ ] [ID: P1-RS-RUNTIME-EXT-01-S2-01] `src/runtime/rs/pytra` 側へ不足 helper/API を補完し、inline 実装と同等の意味を提供する。
- [ ] [ID: P1-RS-RUNTIME-EXT-01-S2-02] `py2rs.py` に runtime ファイル配置導線を追加し、生成コードが外部 runtime を解決できる状態へ移行する。
- [ ] [ID: P1-RS-RUNTIME-EXT-01-S2-03] `rs_emitter.py` から runtime/helper 本体出力を撤去し、runtime API 呼び出し専用へ切り替える。
- [ ] [ID: P1-RS-RUNTIME-EXT-01-S3-01] `check_py2rs_transpile` / Rust smoke / parity を更新して回帰を固定する。
- [ ] [ID: P1-RS-RUNTIME-EXT-01-S3-02] `sample/rs` を再生成し、inline helper 残存ゼロを確認する。
