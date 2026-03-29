<a href="../../en/spec/spec-tools-update-rules.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# `tools/` — 更新ルール

[索引に戻る](./spec-tools.md)

- `tools/` に新しいスクリプトを追加した場合は、`docs/ja/spec/spec-tools.md`（索引）を同時に更新します。
- スクリプトの目的は「何を自動化するために存在するか」を 1 行で明記します。
- 破壊的変更（引数仕様の変更、廃止、統合）がある場合は、`docs/ja/tutorial/how-to-use.md` の関連コマンド例も同期更新します。
- sample 再生成は「変換器ソース差分」ではなく `src/toolchain/misc/transpiler_versions.json` の minor 以上の更新をトリガーにします。
- 変換器関連ファイル（`src/py2*.py`, `src/pytra/**`, `src/toolchain/emit/**`, `src/toolchain/emit/**/profiles/**`）を変更したコミットでは、`tools/check/check_transpiler_version_gate.py` を通過させる必要があります。
- バージョン更新で sample 再生成したときは、`tools/run/run_regen_on_version_bump.py --verify-cpp-on-diff` を使い、生成差分が出た C++ ケースを compile/run 検証します。
