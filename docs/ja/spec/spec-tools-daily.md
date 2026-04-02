<a href="../../en/spec/spec-tools-daily.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# `tools/` — 日常運用ツール

[索引に戻る](./spec-tools.md)

## 1. 回帰確認・検証

- `tools/run/run_local_ci.py`
  - 目的: ローカル最小 CI（version gate + todo 優先度ガード + runtime 層分離ガード + non-C++ emitter runtime-call 直書きガード + emitter 禁止 runtime 実装シンボルガード + non-C++ backend health gate + 条件付き sample 再生成 + transpile 回帰 + unit + selfhost build + diff）を一括実行する。
- `tools/check/check_tools_ledger.py`
  - 目的: `tools/check/`, `tools/gen/`, `tools/run/` のスクリプトが `tools/README.md` 台帳に全て記載されているかを検証し、台帳に載っていないファイルを fail させる。`tools/` 直下への `.py` ファイル直置きも fail。
- `tools/check/check_mapping_json.py`
  - 目的: 全言語の `src/runtime/<lang>/mapping.json` を検証する（valid JSON・`calls` キー存在・`builtin_prefix` 存在・必須エントリ `env.target` 存在・空文字エントリなし）。`run_local_ci.py` に組み込み済み。
- `tools/check/check_todo_priority.py`
  - 目的: `docs/ja/todo/index.md` / `docs/ja/plans/*.md` の差分に追加した進捗 `ID` が、未完了の最上位 `ID`（またはその子 `ID`）と一致するかを検証し、優先度逸脱を防止する。`plans` 側は `決定ログ`（`- YYYY-MM-DD: ...`）行のみを進捗判定対象にし、構造整理の ID 列挙は対象外とする。
- `tools/check/check_jsonvalue_decode_boundaries.py`
  - 目的: `pytra-cli.py` / `east2x.py` / `toolchain/compile/east_io.py` / `toolchain/link/*` の JSON artifact 境界で `json.loads_obj(...)` が正本であることを検証し、raw `json.loads(...)` への再侵入を fail-fast に止める。
- `tools/check/check_py2x_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `pytra-cli.py --target <lang>` で一括変換し、失敗ケースを検出する。全言語統一の transpile チェッカー。
  - 主要オプション: `--target <lang>`（`cpp`, `rs`, `js`, `cs`, `go`, `java`, `ts`, `swift`, `kotlin`, `scala` 等）
  - 補足: 旧言語別スクリプト（`check_py2cpp_transpile.py` 等 10 件）は廃止・削除済み。
- `tools/check/check_east3_golden.py`
  - 目的: EAST3 スナップショットテスト（`test/east3_fixtures/` の golden file と EAST3 出力の差分チェック）。`--check-runtime-east` で `src/runtime/east/` の `.east` ファイル鮮度チェック。`--update` で再生成。
- `tools/check/verify_image_runtime_parity.py`
  - 目的: 画像ランタイム（PNG/GIF）の Python 正本と C++ 側の一致を確認する。
- `tools/check/check_runtime_std_sot_guard.py`
  - 目的: `src/pytra/std/*.py` / `src/pytra/utils/*.py` を正本とする運用を検査し、`rs/cs` では `src/runtime/{rs,cs}/generated/**` を canonical generated lane として監査しつつ、legacy `pytra-gen` lane への手書き実装再流入（現行ガード対象: `json/assertions/re/typing`）を fail させる。あわせて C++ `std/utils` 全体の責務境界（`generated/native` ownership + required manual impl split）も検証する。
- `tools/check/check_runtime_core_gen_markers.py`
  - 目的: `rs/cs` では `src/runtime/<lang>/generated/**` を canonical generated lane として `source/generated-by` marker を強制し、legacy `pytra-gen/pytra-core` は未移行 backend 向けの scan target としてのみ扱う。加えて C++ では `src/runtime/cpp/generated/core/**` の marker 必須、`src/runtime/cpp/native/core/**` の marker 禁止と legacy `src/runtime/cpp/core/**` 再出現時の marker 混入も監査する（`tools/runtime_core_gen_markers_allowlist.txt` 基準）。
  - 補足: C++ `generated/built_in` / `generated/std` / `generated/utils` も同じ marker 契約で監査し、`generated/core` を low-level pure helper lane として扱う前提を壊す増分を止める。
- `tools/check/check_runtime_pytra_gen_naming.py`
  - 目的: canonical generated lane（`rs/cs` は `src/runtime/<lang>/generated/**`、未移行 backend は `pytra-gen/**`）の `std|utils` 配置と素通し命名（`<module>.py -> <module>.<ext>`）を検査し、`image_runtime.*` / `runtime/*.php` などの命名・配置違反増分を fail させる（`tools/runtime_pytra_gen_naming_allowlist.txt` 基準）。
- `tools/check/check_emitter_runtimecall_guardrails.py`
  - 目的: non-C++ emitter の `if/elif` 文字列分岐における runtime/stdlib 関数名直書きの増分を検知し、allowlist 外を fail させる（`tools/emitter_runtimecall_guardrails_allowlist.txt` 基準）。
- `tools/check/check_emitter_forbidden_runtime_symbols.py`
  - 目的: `src/toolchain/emit/*/emitter/*.py` における禁止 runtime 実装シンボル（`__pytra_write_rgb_png` / `__pytra_save_gif` / `__pytra_grayscale_palette`）の混入増分を検知し、allowlist 外を fail させる（`tools/emitter_forbidden_runtime_symbols_allowlist.txt` 基準）。

## 2. Emitter 変更 Stop-Ship チェックリスト（必須）

- 対象: `src/toolchain/emit/*/emitter/*.py` を変更したコミット。
- コミット前に次の 3 コマンドを必ず実行する。
  - `python3 tools/check/check_emitter_runtimecall_guardrails.py`
  - `python3 tools/check/check_emitter_forbidden_runtime_symbols.py`
  - `python3 tools/check/check_noncpp_east3_contract.py`
- 3 コマンドのいずれかが `FAIL` の場合は Stop-Ship 扱いとし、コミット/プッシュ/レビュー依頼を禁止する。
- レビュー時は次の 3 項目を checklist として確認する。
  - [ ] 上記 3 コマンドの実行ログがある。
  - [ ] `src/toolchain/emit/*/emitter/*.py` に禁止 runtime 実装シンボルの増分がない。
  - [ ] runtime/stdlib 呼び出し解決が EAST3 正本（`runtime_call` / `resolved_runtime_call` / `resolved_runtime_source`）のみを利用している。

## 3. ビルド・生成

- `tools/gen/gen_makefile_from_manifest.py`
  - 目的: `manifest.json` を受け取り、`all`, `run`, `clean` を含む `Makefile` を生成する。
- `tools/gen/regenerate_samples.py`
  - 目的: `sample/py` から各 `sample/<lang>` を再生成する。
  - 主要オプション: `--verify-cpp-on-diff`（C++ 生成差分が出たケースだけ `runtime_parity_check.py --targets cpp` で compile/run 検証）
- `tools/run/run_regen_on_version_bump.py`
  - 目的: sample を再生成し、影響言語のみ再生成する。
- `tools/run/sync_todo_history_translation.py`
  - 目的: `docs/ja/todo/archive` を正本として `docs/en/todo/archive` の日付ファイル雛形と index を同期し、`--check` で同期漏れを検出する。

## 4. golden file 生成

- `tools/gen/generate_golden.py`
  - 目的: 現行 `toolchain/` を使って各段（east1 / east2 / east3 / east3-opt）の golden file を `test/` に一括生成する。`toolchain2/` の自前実装が golden file と一致するかを検証するための正解データ。
  - 主要オプション: `--stage={east1,east2,east3,east3-opt}`, `-o OUTPUT_DIR`, `--from=python`, `--sample-dir`
  - 設計文書: `docs/ja/plans/plan-pipeline-redesign.md` §6.1
  - 注意: golden file 生成は本ツールに一元化する。各 agent が独自スクリプトで golden file を作ることを禁止する。
