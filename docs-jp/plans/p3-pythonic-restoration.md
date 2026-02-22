# TASK GROUP: TG-P3-PYTHONIC

最終更新: 2026-02-22

関連 TODO:
- `docs-jp/todo.md` の `ID: P3-PY-*`, `P3-CE-*`, `P3-RULE-*`

背景:
- selfhost 安定化のため平易化した記法が増え、可読性が低下している。

目的:
- selfhost 安定を維持したまま、段階的に Pythonic 記法へ戻す。

対象:
- `src/py2cpp.py` のループ/比較/リテラル/式簡潔化
- `code_emitter.py` の重複判定・分岐整理
- 小パッチ運用（1〜3関数）

非対象:
- 大規模一括リファクタ

受け入れ基準:
- 可読性向上と selfhost 安定を両立
- 既定の検証コマンドを毎回通す

確認コマンド:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`

決定ログ:
- 2026-02-22: 初版作成。
- 2026-02-22: `P3-PY-02` の小パッチとして `src/py2cpp.py::_render_set_literal_repr` の `[:1]` / `[-1:]` 判定を `startswith` / `endswith` へ戻した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- 2026-02-22: `P3-PY-02` の継続として `src/py2cpp.py::_emit_target_unpack` の型文字列判定（`list[` / `set[` / `tuple[` / `dict[`）をスライス比較から `startswith` / `endswith` に統一した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- 2026-02-22: `P3-PY-01` の小パッチとして `src/py2cpp.py::_sanitize_module_label` の手動インデックス `while` ループを `for ch in s` へ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- 2026-02-22: `P3-PY-02` 周辺の後続整理として `src/py2cpp.py::_cpp_type_text` と `_header_cpp_type_from_east` のクラス名推定で `leaf[:1]` を廃止し、空文字チェック + `leaf[0]` 参照へ統一した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- 2026-02-22: `P3-PY-01` の継続として `src/py2cpp.py::_path_parent_text`（区切り探索）と `_make_user_error`（details 連結）の手動インデックス `while` を `for` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- 2026-02-22: `P3-PY-01` の継続として `src/py2cpp.py::_module_tail_to_cpp_header_path`、`_parse_user_error`、`_header_guard_from_path` の手動インデックス走査を `for` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
- 2026-02-22: `src/py2cpp.py` 全体で `[:1]` / `[-1:]` / `[0:1]` 系の1文字スライス比較パターンが検出ゼロになったため、`P3-PY-02` を完了扱いにした。
- 2026-02-22: `P3-CE-01` の小パッチとして `src/pytra/compiler/east_parts/code_emitter.py` の `escape_string_for_literal`、`render_compare_chain_common`、`load_import_bindings_from_meta` を `for` ベースへ置換した。`python3 tools/check_py2cpp_transpile.py`（`checked=117 ok=117 fail=0 skipped=5`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）を確認。
