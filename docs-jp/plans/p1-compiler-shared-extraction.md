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

`P1-COMP-08` 移行計画（他言語 CLI の共通解析 API 採用）:

1. Phase 0（API 固定化）
   - `src/pytra/compiler/` に共通解析 API の入口を定義する。
   - 最低限の提供単位は `import_graph` / `module_east_map` / `symbol_index` / `type_schema` / `deps_dump` とする。
   - CLI から見える戻り値型（dict スキーマ）を固定し、`py2cpp` 実装を参照実装として扱う。
2. Phase 1（`py2rs.py` 先行適用）
   - `py2rs.py` から `py2cpp.py` 固有 helper 直呼びを禁止し、共通 API 経由で module 解析結果を受け取る。
   - 既存出力との差分を `tools/check_py2rs_transpile.py` で確認する。
3. Phase 2（`py2cs.py` / `py2js.py` / `py2ts.py` へ展開）
   - 3 言語の CLI で同一 API を使い、import 解決の前段を共通化する。
   - `meta.import_bindings` 利用前の解析処理（FS 依存部分）を共通層へ移す。
4. Phase 3（preview 言語 `py2go.py` / `py2java.py` / `py2swift.py` / `py2kotlin.py` へ展開）
   - 失敗時の診断形式（解析失敗 / 変換失敗）を共通化し、言語別 CLI は表示責務に限定する。
   - 各 `tools/check_py2<lang>_transpile.py` が同一前処理 API を使う状態まで寄せる。
5. Phase 4（旧経路の縮退）
   - `py2cpp.py` を含む各 CLI から重複した project 解析コードを削除する。
   - 共通 API 層に回帰テストを追加し、CLI 層は配線テスト中心へ移行する。

完了条件:
- 非 C++ の各 CLI が、project 解析を `src/pytra/compiler/` 共通 API 経由で実行する。
- `py2cpp.py` 側に残る project 解析実装は C++ 固有補助を除き撤去される。
- 既存の transpile チェック（`tools/check_py2*.py`）が回帰なく通過する。

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-22: `P1-COMP-06` / `P1-COMP-07` として、`docs-jp/spec/spec-dev.md` に `CodeEmitter`・EAST parser・compiler共通層の責務境界を明文化した。
- 2026-02-22: `P1-COMP-08` として、`py2rs.py` を起点に他言語 CLI へ共通解析 API を段階適用する 5 フェーズ移行計画を追加した。
