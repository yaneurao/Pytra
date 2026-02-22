# TASK GROUP: TG-P1-COMP-SHARED

最終更新: 2026-02-22

関連 TODO:
- `docs-jp/todo.md` の `ID: P1-COMP-01` 〜 `P1-COMP-08`

背景:
- import グラフ解析や module index 構築など全言語共通処理が `py2cpp.py` に偏在している。

目的:
- 共通解析を `src/pytra/compiler/` の API へ抽出し、各 `py2*` CLI で再利用可能にする。

対象:
- import グラフ解析
- module EAST map / symbol index / type schema 構築
- deps dump API
- `CodeEmitter` と parser の責務境界明文化

非対象:
- 言語固有のコード生成最適化
- runtime 出力形式の変更

受け入れ基準:
- 共通解析 API が `py2cpp` 以外から利用可能
- `py2cpp.py` は C++ 固有責務中心に縮退
- 境界定義（CodeEmitter / parser / compiler共通層）が文書化される

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 test/unit/test_py2cpp_features.py`

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-22: `P1-COMP-06` / `P1-COMP-07` として、`docs-jp/spec-dev.md` に `CodeEmitter`・EAST parser・compiler共通層の責務境界を明文化した。
