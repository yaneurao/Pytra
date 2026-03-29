<a href="../../en/spec/spec-tools.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# `tools/` スクリプト一覧

`tools/` は、Pytra の開発運用を自動化するための補助スクリプト群です。
目的は次の 3 つです。

- 回帰確認を短時間で繰り返せるようにする。
- selfhost の調査・比較・ビルドを定型化する。
- `src/pytra/` 正本から C++ ランタイム生成物を更新・検証する。

## 詳細ページ

| ページ | 内容 |
|---|---|
| [日常運用ツール](./spec-tools-daily.md) | check_* / build_* / generate_* 系ツール、Stop-Ship チェックリスト、golden file 生成 |
| [言語間 parity 確認](./spec-tools-parity.md) | runtime_parity_check、backend health、smoke テスト、parity 完了条件、bootstrap |
| [更新ルール](./spec-tools-update-rules.md) | ツール追加時のドキュメント同期、バージョン運用 |

## ツール早見表

### 日常運用（[詳細](./spec-tools-daily.md)）

| ツール | 目的 |
|---|---|
| `run_local_ci.py` | ローカル最小 CI 一括実行 |
| `check_tools_ledger.py` | tools/ 台帳突合チェック |
| `check_mapping_json.py` | mapping.json 妥当性チェック（全言語） |
| `gen_backend_progress.py` | バックエンド進捗ページ生成 |
| `check_todo_priority.py` | TODO 優先度逸脱の検証 |
| `check_jsonvalue_decode_boundaries.py` | JSON artifact 境界の正本検証 |
| `check_py2x_transpile.py` | 全言語統一 transpile チェック |
| `check_transpiler_version_gate.py` | バージョン更新検証 |
| `check_east3_golden.py` | EAST3 golden スナップショット |
| `verify_image_runtime_parity.py` | 画像 runtime 一致確認 |
| `check_runtime_std_sot_guard.py` | stdlib 正本ガード |
| `check_runtime_core_gen_markers.py` | generated marker 検証 |
| `check_runtime_pytra_gen_naming.py` | generated 命名検証 |
| `check_emitter_runtimecall_guardrails.py` | emitter runtime-call 直書きガード |
| `check_emitter_forbidden_runtime_symbols.py` | emitter 禁止シンボルガード |
| `gen_makefile_from_manifest.py` | manifest → Makefile 生成 |
| `regenerate_samples.py` | sample 再生成 |
| `run_regen_on_version_bump.py` | バージョン bump 時の再生成 |
| `sync_todo_history_translation.py` | TODO アーカイブ翻訳同期 |
| `generate_golden.py` | golden file 一括生成 |

### 言語間 parity（[詳細](./spec-tools-parity.md)）

| ツール | 目的 |
|---|---|
| `runtime_parity_check.py` | 多言語 runtime parity チェック（`--category` でカテゴリ絞り込み可） |
| `runtime_parity_check_fast.py` | 同上の高速版（transpile 段をインメモリ API で実行） |
| `check_all_target_sample_parity.py` | 全 target sample parity 確定 |
| `check_noncpp_backend_health.py` | non-C++ backend health gate |
| `export_backend_test_matrix.py` | backend test matrix 再生成 |

### selfhost

旧 selfhost ツール群（`build_selfhost.py`, `prepare_selfhost_source.py`, `check_selfhost_*.py` 等）は `tools/unregistered/` に退避済み。

新パイプライン（`toolchain2/`）では selfhost は通常のビルドパイプライン（`pytra-cli2 -build --target=cpp`）で完結する設計とし、専用ツールを不要にする。詳細は `docs/ja/plans/plan-pipeline-redesign.md` を参照。
