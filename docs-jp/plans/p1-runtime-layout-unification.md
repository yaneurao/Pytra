# TASK GROUP: TG-P1-RUNTIME-LAYOUT

最終更新: 2026-02-22

関連 TODO:
- `docs-jp/todo.md` の `ID: P1-RUNTIME-01` 〜 `P1-RUNTIME-06`

背景:
- 言語ごとに runtime 配置規約が分断され、保守責務と探索規則が揺れている。

目的:
- `src/runtime/<lang>/pytra/` へ配置規約を統一し、runtime 資産の責務境界を揃える。

対象:
- Rust: `src/rs_module/` から `src/runtime/rs/pytra/` への移行
- 他言語: `src/*_module/` 依存資産の `src/runtime/<lang>/pytra/` への移行計画
- `py2*` / hooks の解決パス統一

非対象:
- 各言語 runtime の機能追加そのもの

受け入れ基準:
- ランタイム参照先が `src/runtime/<lang>/pytra/` へ統一
- `src/*_module/` 直下への新規 runtime 追加が止まる

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- 言語別 smoke tests（`test/unit/test_py2*_smoke.py`）

決定ログ:
- 2026-02-22: 初版作成。
