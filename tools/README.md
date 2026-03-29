# tools/ 管理台帳

このファイルは `tools/` ディレクトリの管理台帳です。
**新規ファイルを追加するときは必ずこのファイルも同時に更新してください。**
台帳に記載のないファイルは CI チェック (`tools/check/check_tools_ledger.py`) で fail になります。

## ディレクトリ構成

```
tools/
├── check/          # 検証・ガードスクリプト
├── gen/            # 生成スクリプト
├── run/            # 実行・CI スクリプト
├── unittest/       # ユニットテスト（pytest）
├── unregistered/   # 旧ツール・実験的ツール（CI 対象外）
├── *.json / *.txt  # 設定・allowlist ファイル
└── README.md       # 本ファイル（管理台帳）
```

## ルール

- `tools/` 直下への新規 `.py` ファイル追加は**禁止**。必ずサブディレクトリに配置する。
- 新規スクリプトは `check/` / `gen/` / `run/` のいずれか適切なフォルダへ配置する。
- CI 非対象の実験的スクリプトは `unregistered/` に配置する。
- ファイルを追加・削除・移動したら **必ず本台帳を同時に更新する**。

---

## tools/check/ — 検証・ガードスクリプト

| ファイル | 目的 |
|---|---|
| `audit_image_runtime_sot.py` | 画像 runtime の正本ファイル監査 |
| `check_all_target_sample_parity.py` | 全 target sample parity 確定チェック |
| `check_east3_golden.py` | EAST3 golden スナップショットテスト |
| `check_east_stage_boundary.py` | EAST ステージ境界の依存チェック |
| `check_emitter_forbidden_runtime_symbols.py` | emitter 禁止 runtime 実装シンボルガード |
| `check_emitter_runtimecall_guardrails.py` | emitter runtime-call 直書きガード |
| `check_jsonvalue_decode_boundaries.py` | JSON artifact 境界の正本検証 |
| `check_jsonvalue_typeexpr_contract.py` | JSONValue 型式コントラクト検証 |
| `check_legacy_cli_references.py` | 旧 CLI 参照の混入チェック |
| `check_legacy_transpile_checkers_absent.py` | 廃止済み transpile チェッカー不在確認 |
| `check_mapping_json.py` | 全言語 mapping.json 妥当性チェック |
| `check_multilang_quality_regression.py` | 多言語品質回帰チェック |
| `check_noncpp_backend_health.py` | non-C++ backend health gate |
| `check_noncpp_east3_contract.py` | non-C++ EAST3 コントラクト検証 |
| `check_py2x_transpile.py` | 全言語統一 transpile チェック |
| `check_runtime2_references_absent.py` | runtime2 参照の混入チェック |
| `check_runtime_core_gen_markers.py` | generated marker 検証 |
| `check_runtime_legacy_shims.py` | legacy shim 混入チェック |
| `check_runtime_pytra_gen_naming.py` | generated 命名検証 |
| `check_runtime_special_generators_absent.py` | 特殊 generator 不在確認 |
| `check_runtime_std_sot_guard.py` | stdlib 正本ガード |
| `check_sample_regen_clean.py` | sample 再生成クリーン確認 |
| `check_todo_priority.py` | TODO 優先度逸脱の検証 |
| `check_tools_ledger.py` | tools/ 台帳突合チェック（CI 用） |
| `check_transpiler_version_gate.py` | バージョン更新検証 |
| `runtime_parity_check.py` | 多言語 runtime parity チェック |
| `runtime_parity_check_fast.py` | runtime parity チェック高速版 |
| `verify_image_runtime_parity.py` | 画像 runtime 一致確認 |

## tools/gen/ — 生成スクリプト

| ファイル | 目的 |
|---|---|
| `export_backend_test_matrix.py` | backend test matrix 再生成 |
| `gen_backend_progress.py` | バックエンド進捗ページ生成 |
| `gen_makefile_from_manifest.py` | manifest → Makefile 生成 |
| `gen_runtime_symbol_index.py` | runtime symbol index 生成 |
| `generate_golden.py` | golden file 一括生成 |
| `generate_golden_linked.py` | リンク済み golden file 生成 |
| `regenerate_golden.py` | golden file 再生成 |
| `regenerate_samples.py` | sample 再生成 |
| `strip_east1_type_info.py` | EAST1 型情報ストリップ |

## tools/run/ — 実行・CI スクリプト

| ファイル | 目的 |
|---|---|
| `run_local_ci.py` | ローカル最小 CI 一括実行 |
| `run_regen_on_version_bump.py` | バージョン bump 時の再生成 |
| `sync_todo_history_translation.py` | TODO アーカイブ翻訳同期 |

## tools/unittest/ — ユニットテスト

pytest で実行するテストファイル群。サブディレクトリ構成:

| サブディレクトリ | 内容 |
|---|---|
| `common/` | 言語横断・共通テスト |
| `compile/` | コンパイルフェーズテスト |
| `emit/` | emitter テスト（言語別サブディレクトリあり） |
| `ir/` | IR テスト |
| `link/` | リンクフェーズテスト |
| `selfhost/` | selfhost テスト |
| `toolchain2/` | toolchain2 テスト |
| `tooling/` | ツール系テスト |

トップレベルファイル:

| ファイル | 目的 |
|---|---|
| `comment_fidelity.py` | コメント保持テスト |
| `test_discovery_router.py` | テスト検出ルーターテスト |

## tools/ ルートの設定・データファイル

| ファイル | 目的 |
|---|---|
| `check_py2x_profiles.json` | check_py2x_transpile.py 用プロファイル設定 |
| `emitter_forbidden_runtime_symbols_allowlist.txt` | emitter 禁止シンボル allowlist |
| `emitter_runtimecall_guardrails_allowlist.txt` | emitter runtime-call guardrail allowlist |
| `runtime_core_gen_markers_allowlist.txt` | runtime core generated marker allowlist |
| `runtime_generation_manifest.json` | runtime 生成マニフェスト |
| `runtime_pytra_gen_naming_allowlist.txt` | runtime pytra-gen 命名 allowlist |
| `runtime_symbol_index.json` | runtime シンボルインデックス（gen_runtime_symbol_index.py が生成） |

## tools/unregistered/ — 旧ツール・実験的ツール

CI 対象外。旧 selfhost パイプライン・実験的チェッカー・調査スクリプト等を格納。
新しいスクリプトの置き場として使う場合は、正式採用時に適切なサブディレクトリへ昇格させること。
