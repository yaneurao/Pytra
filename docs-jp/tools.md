# `tools/` スクリプト一覧

<a href="../docs/tools.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>


`tools/` は、Pytra の開発運用を自動化するための補助スクリプト群です。  
目的は次の 3 つです。

- 回帰確認を短時間で繰り返せるようにする。
- selfhost の調査・比較・ビルドを定型化する。
- `src/pytra/` 正本から C++ ランタイム生成物を更新・検証する。

## 1. 日常運用で使うもの

- `tools/run_local_ci.py`
  - 目的: ローカル最小 CI（transpile 回帰 + unit + selfhost build + diff）を一括実行する。
- `tools/check_py2cpp_transpile.py`
  - 目的: `test/fixtures/` を `py2cpp.py` で一括変換し、失敗ケースを検出する。
  - 主要オプション: `--check-yanesdk-smoke`（Yanesdk の縮小ケースを同時確認）
- `tools/check_py2rs_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `py2rs.py` で一括変換し、失敗ケースを検出する。
- `tools/check_py2js_transpile.py`
  - 目的: `test/fixtures/` と `sample/py` を `py2js.py` で一括変換し、失敗ケースを検出する。
- `tools/check_yanesdk_py2cpp_smoke.py`
  - 目的: Yanesdk canonical 対象（`library 1本 + game 7本`）が `py2cpp.py` を通るか確認する。
- `tools/verify_sample_outputs.py`
  - 目的: `sample/py` の Python 実行結果と C++ 実行結果（stdout/画像）を比較する。
  - 主要オプション: `--samples`, `--compile-flags`, `--ignore-stdout`
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
- `tools/check_selfhost_stage2_cpp_diff.py`
  - 目的: Python 版と 2段自己変換版（`selfhost/py2cpp_stage2.out`）の生成 C++ 差分を比較する。
  - 主要オプション: `--skip-build`, `--mode`, `--show-diff`
- `tools/summarize_selfhost_errors.py`
  - 目的: selfhost ビルドログのエラーをカテゴリ別に集計する。
- `tools/selfhost_error_hotspots.py`
  - 目的: エラー集中箇所を関数単位で集約する。
- `tools/selfhost_error_report.py`
  - 目的: selfhost エラー解析結果のレポートを整形出力する。

## 3. 言語間確認
- `tools/runtime_parity_check.py`
  - 目的: 複数ターゲット言語でのランタイム平準化チェックを実行する。

## 4. 更新ルール

- `tools/` に新しいスクリプトを追加した場合は、この `docs-jp/tools.md` を同時に更新します。
- スクリプトの目的は「何を自動化するために存在するか」を 1 行で明記します。
- 破壊的変更（引数仕様の変更、廃止、統合）がある場合は、`docs-jp/how-to-use.md` の関連コマンド例も同期更新します。
