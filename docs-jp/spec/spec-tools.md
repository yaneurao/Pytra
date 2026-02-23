# `tools/` スクリプト一覧

<a href="../../docs/spec/spec-tools.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


`tools/` は、Pytra の開発運用を自動化するための補助スクリプト群です。  
目的は次の 3 つです。

- 回帰確認を短時間で繰り返せるようにする。
- selfhost の調査・比較・ビルドを定型化する。
- `src/pytra/` 正本から C++ ランタイム生成物を更新・検証する。

## 1. 日常運用で使うもの

- `tools/run_local_ci.py`
  - 目的: ローカル最小 CI（version gate + 条件付き sample 再生成 + transpile 回帰 + unit + selfhost build + diff）を一括実行する。
- `tools/check_py2cpp_transpile.py`
  - 目的: `test/fixtures/` を `py2cpp.py` で一括変換し、失敗ケースを検出する。
  - 主要オプション: `--check-yanesdk-smoke`（Yanesdk の縮小ケースを同時確認）
- `tools/check_py2rs_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `py2rs.py` で一括変換し、失敗ケースを検出する。
- `tools/check_py2js_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `py2js.py` で一括変換し、失敗ケースを検出する。
- `tools/check_py2cs_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `py2cs.py` で一括変換し、失敗ケースを検出する。
- `tools/check_py2go_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `py2go.py` で一括変換し、失敗ケースを検出する。
- `tools/check_py2java_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `py2java.py` で一括変換し、失敗ケースを検出する。
- `tools/check_py2ts_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `py2ts.py` で一括変換し、失敗ケースを検出する。
- `tools/check_py2swift_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `py2swift.py` で一括変換し、失敗ケースを検出する。
- `tools/check_py2kotlin_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `py2kotlin.py` で一括変換し、失敗ケースを検出する。
- `tools/check_yanesdk_py2cpp_smoke.py`
  - 目的: Yanesdk canonical 対象（`library 1本 + game 7本`）が `py2cpp.py` を通るか確認する。
- `tools/check_microgpt_original_py2cpp_regression.py`
  - 目的: 原本 `materials/refs/microgpt/microgpt-20260222.py` を固定入力にし、`py2cpp` の失敗ステージ（A〜F）または成功を検査して再発を検知する。
- `tools/build_multi_cpp.py`
  - 目的: `py2cpp.py --multi-file` が出力した `manifest.json` を読み、関連 `*.cpp` と runtime をまとめてビルドする。
- `tools/verify_multi_file_outputs.py`
  - 目的: `sample/py` の multi-file 出力をビルド・実行し、単一ファイル出力との実行結果一致を確認する。
- `tools/check_transpiler_version_gate.py`
  - 目的: 変換器関連ファイルが変更されたとき、`src/pytra/compiler/transpiler_versions.json` の対応コンポーネント（`shared` / 言語別）で minor 以上のバージョン更新が行われているかを検証する。
- `tools/regenerate_samples.py`
  - 目的: `sample/py` から各 `sample/<lang>` を再生成し、`src/pytra/compiler/transpiler_versions.json` のバージョン・トークンが変わらない限り再生成を skip する。
  - 主要オプション: `--verify-cpp-on-diff`（C++ 生成差分が出たケースだけ `verify_sample_outputs.py` で compile/run 検証）
- `tools/run_regen_on_version_bump.py`
  - 目的: `transpiler_versions.json` の minor 以上の更新を検出したときだけ `regenerate_samples.py` を起動し、影響言語のみ再生成する。
- `tools/sync_todo_history_translation.py`
  - 目的: `docs-jp/todo-history` を正本として `docs/todo-history` の日付ファイル雛形と index を同期し、`--check` で同期漏れを検出する。
- `tools/verify_sample_outputs.py`
  - 目的: `sample/golden/manifest.json` のゴールデン基準と C++ 実行結果（stdout/生成物）を比較し、通常検証で Python 実行を省略する。
  - 主要オプション: `--samples`, `--compile-flags`, `--ignore-stdout`, `--golden-manifest`, `--refresh-golden`, `--refresh-golden-only`
- `tools/verify_image_runtime_parity.py`
  - 目的: 画像ランタイム（PNG/GIF）の Python 正本と C++ 側の一致を確認する。

## 2. selfhost 関連

- `tools/build_selfhost.py`
  - 目的: selfhost 用 `selfhost/py2cpp.out` を生成する（生成 C++ への手動 main パッチなし）。
- `tools/build_selfhost_stage2.py`
  - 目的: `selfhost/py2cpp.out` で `selfhost/py2cpp.py` を再変換し、2段自己変換バイナリ `selfhost/py2cpp_stage2.out` を生成する。
- `tools/prepare_selfhost_source.py`
  - 目的: `CodeEmitter` などを selfhost 用ソースへ展開し、自己完結化する。
- `tools/selfhost_transpile.py`
  - 目的: 暫定ブリッジとして `.py -> EAST JSON -> selfhost` 経路を実行する。
- `tools/check_selfhost_cpp_diff.py`
  - 目的: Python 版と selfhost 版の生成 C++ 差分を比較する。
  - 主要オプション: `--mode allow-not-implemented`, `--show-diff`, `--selfhost-driver`
- `tools/check_selfhost_direct_compile.py`
  - 目的: selfhost の `.py` 直入力経路を `sample/py` で一括変換し、`g++ -fsyntax-only` でコンパイル回帰を即時検出する。
- `tools/check_selfhost_stage2_cpp_diff.py`
  - 目的: Python 版と 2段自己変換版（`selfhost/py2cpp_stage2.out`）の生成 C++ 差分を比較する。
  - 主要オプション: `--skip-build`, `--mode`, `--show-diff`
- `tools/summarize_selfhost_errors.py`
  - 目的: selfhost ビルドログのエラーをカテゴリ別に集計する。
- `tools/selfhost_error_hotspots.py`
  - 目的: エラー集中箇所を関数単位で集約する。
- `tools/selfhost_error_report.py`
  - 目的: selfhost エラー解析結果のレポートを整形出力する。

### 2.1 selfhost 暴走ガード（実装済み）

selfhost の調査時に、深い再帰・巨大構文木・シンボル爆発で実行が長時間化するケースを早期停止できるよう、以下のガードを `py2cpp.py` / 共通 CLI へ段階導入する。

- `--guard-profile {off,default,strict}`
  - 既定は `default`。`off` は制限無効、`strict` は調査向けに低い上限を適用する。
  - `default` の既定値:
    - `max-ast-depth=800`
    - `max-parse-nodes=2000000`
    - `max-symbols-per-module=200000`
    - `max-scope-depth=400`
    - `max-import-graph-nodes=5000`
    - `max-import-graph-edges=20000`
    - `max-generated-lines=2000000`
  - `strict` の既定値:
    - `max-ast-depth=200`
    - `max-parse-nodes=200000`
    - `max-symbols-per-module=20000`
    - `max-scope-depth=120`
    - `max-import-graph-nodes=1000`
    - `max-import-graph-edges=4000`
    - `max-generated-lines=300000`
- 個別上限オプション（`guard_profile` より優先）
  - `--max-ast-depth`
  - `--max-parse-nodes`
  - `--max-symbols-per-module`
  - `--max-scope-depth`
  - `--max-import-graph-nodes`
  - `--max-import-graph-edges`
  - `--max-generated-lines`

失敗契約:

- いずれかの上限超過時は、`input_invalid(kind=limit_exceeded, stage=<parse|analyze|emit>, limit=<name>, value=<n>)` 形式で fail-fast する。
- `tools/build_selfhost.py` など selfhost 実行系ツールは、必要に応じて `--timeout-sec` 併用でプロセス時間上限を設定できるようにする。

## 3. 言語間確認
- `tools/runtime_parity_check.py`
  - 目的: 複数ターゲット言語でのランタイム平準化チェックを実行する。

## 4. 更新ルール

- `tools/` に新しいスクリプトを追加した場合は、この `docs-jp/spec/spec-tools.md` を同時に更新します。
- スクリプトの目的は「何を自動化するために存在するか」を 1 行で明記します。
- 破壊的変更（引数仕様の変更、廃止、統合）がある場合は、`docs-jp/how-to-use.md` の関連コマンド例も同期更新します。
- sample 再生成は「変換器ソース差分」ではなく `src/pytra/compiler/transpiler_versions.json` の minor 以上の更新をトリガーにします。
- 変換器関連ファイル（`src/py2*.py`, `src/pytra/**`, `src/hooks/**`, `src/profiles/**`）を変更したコミットでは、`tools/check_transpiler_version_gate.py` を通過させる必要があります。
- バージョン更新で sample 再生成したときは、`tools/run_regen_on_version_bump.py --verify-cpp-on-diff` を使い、生成差分が出た C++ ケースを compile/run 検証します。
