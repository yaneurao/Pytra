# P1: Rust runtime 外出し（inline helper / `mod pytra` 埋め込み撤去）

最終更新: 2026-03-01

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

## 分解

- [x] [ID: P1-RS-RUNTIME-EXT-01-S1-01] Rust emitter の inline helper 出力一覧と `src/runtime/rs/pytra` 正本 API 対応表を確定する。
- [x] [ID: P1-RS-RUNTIME-EXT-01-S1-02] Rust 生成物の runtime 参照方式（`mod/use` 構成と出力ディレクトリ配置契約）を確定し、fail-closed 条件を文書化する。
- [x] [ID: P1-RS-RUNTIME-EXT-01-S2-01] `src/runtime/rs/pytra` 側へ不足 helper/API を補完し、inline 実装と同等の意味を提供する。
- [x] [ID: P1-RS-RUNTIME-EXT-01-S2-02] `py2rs.py` に runtime ファイル配置導線を追加し、生成コードが外部 runtime を解決できる状態へ移行する。
- [ ] [ID: P1-RS-RUNTIME-EXT-01-S2-03] `rs_emitter.py` から runtime/helper 本体出力を撤去し、runtime API 呼び出し専用へ切り替える。
- [ ] [ID: P1-RS-RUNTIME-EXT-01-S3-01] `check_py2rs_transpile` / Rust smoke / parity を更新して回帰を固定する。
- [ ] [ID: P1-RS-RUNTIME-EXT-01-S3-02] `sample/rs` を再生成し、inline helper 残存ゼロを確認する。

## S1-01 棚卸し結果（inline helper vs runtime 正本）

### A. `RUST_RUNTIME_SUPPORT`（`rs_emitter.py` の固定文字列）

- inline 出力対象:
  - `py_perf_counter`, `py_isdigit`, `py_isalpha`, `py_str_at`, `py_slice_str`
  - PNG/GIF 系: `py_write_rgb_png`, `py_save_gif` と補助関数
  - `mod time`, `mod math`, `mod pytra`（`pytra::runtime::{png,gif}` と `pytra::utils` 再輸出）
- `src/runtime/rs/pytra/built_in/py_runtime.rs` との対応:
  - 既存実装あり: `py_isdigit`, `py_isalpha`, `py_write_rgb_png`, `py_save_gif`, `perf_counter`
  - 命名差分あり: `py_perf_counter`（inline） vs `perf_counter`（runtime）
  - 機能欠落あり: `py_str_at`, `py_slice_str`, `mod time/math/pytra` の公開モジュール

### B. `_emit_pyany_runtime`（必要時のみ動的出力）

- inline 出力対象:
  - `enum PyAny`
  - 変換 helper: `py_any_to_i64`, `py_any_to_f64`, `py_any_to_bool`, `py_any_to_string`, `py_any_as_dict`
  - 補助 trait 群（`PyAnyTo*Arg`）
- runtime 正本対応:
  - `src/runtime/rs/pytra/built_in/py_runtime.rs` に未実装（全量ギャップ）。

### C. `_emit_isinstance_runtime_helpers`（必要時のみ動的出力）

- inline 出力対象:
  - `PYTRA_TID_*` 定数
  - `PyTypeInfo`, `py_type_info`
  - `PyRuntimeTypeId` trait
  - `py_runtime_type_id`, `py_is_subtype`, `py_issubclass`, `py_isinstance`
- runtime 正本対応:
  - `src/runtime/rs/pytra/built_in/py_runtime.rs` に未実装（全量ギャップ）。

### D. S2 で埋める不足 API（確定）

- 追加先: `src/runtime/rs/pytra/built_in/py_runtime.rs`
- 追加対象:
  - `py_str_at`, `py_slice_str`
  - `pub mod time`, `pub mod math`, `pub mod pytra`
  - `PyAny` と `py_any_*` 一式
  - `type_id/isinstance` 一式（`PYTRA_TID_*`, `PyRuntimeTypeId`, `py_isinstance` 等）

## S1-02 runtime 参照方式（契約）

### 生成物レイアウト

- `py2rs.py` 出力時に、対象 `.rs` と同じディレクトリへ `py_runtime.rs` を必ず配置する。
- 生成メインファイル先頭で次を宣言する。
  - `mod py_runtime;`
  - `pub use crate::py_runtime::{math, pytra, time};`
  - `use crate::py_runtime::*;`

### 参照ルール

- 既存 import lower（`use crate::time::perf_counter;`, `use crate::pytra::runtime::png;`）は維持し、`pub use` で後方互換にする。
- emitter は runtime helper 本体を出力せず、helper 呼び出しのみを出力する。
- runtime 正本で公開される識別子のみ使用可とし、未公開 API を emitter が参照しない。

### fail-closed 条件

- `py_runtime.rs` 正本が見つからない場合、`py2rs.py` は即時 `RuntimeError` で失敗する。
- 出力先への runtime 配置に失敗した場合、メイン `.rs` 書き出し後でもプロセスを失敗扱いにする（不完全生成を黙認しない）。
- unit/smoke で `fn py_perf_counter` / `mod pytra {` など inline 残存を検知したら失敗扱いにする。

決定ログ:
- 2026-02-28: ユーザー指示により、Rust の helper/runtime 分離を `P1` として新規起票した。
- 2026-03-01: `RUST_RUNTIME_SUPPORT`/`_emit_pyany_runtime`/`_emit_isinstance_runtime_helpers` の棚卸しを実施し、`py_runtime.rs` への移管対象と不足 API を確定した（`S1-01`）。
- 2026-03-01: 生成時の runtime 配置契約（`mod py_runtime;` + `pub use` + `use crate::py_runtime::*;`）と fail-closed 条件を確定した（`S1-02`）。
- 2026-03-01: `src/runtime/rs/pytra/built_in/py_runtime.rs` に `py_str_at`/`py_slice_str`、`PyAny` 変換群、`type_id/isinstance` 基盤、`pub mod time/math/pytra` を追加し、`rustc --crate-type lib` で単体構文確認した（`S2-01`）。
- 2026-03-01: `py2rs.py` に `py_runtime.rs` 同梱コピー導線を追加し、CLI smoke で生成先に runtime が配置されることを確認した（`S2-02`）。`check_py2rs_transpile.py` の失敗4件（`Try/Yield/Swap` 未対応）は既存仕様差分として `S3-01` で扱う。
