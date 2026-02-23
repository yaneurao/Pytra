# TASK GROUP: TG-P0-SH

最終更新: 2026-02-23

関連 TODO:
- `docs-jp/todo.md` の `ID: P0-SH-04`（`P0-SH-04-S1` 〜 `P0-SH-04-S3`）
- `docs-jp/todo.md` の `ID: P0-SH-05`

背景:
- selfhost の変換・ビルド・実行が不安定だと、回帰検出と改善サイクル全体が止まる。

目的:
- selfhost を日次で再現可能な最小経路に固定し、エラー再発時に即座に再検出できる状態を作る。

対象:
- selfhost `.py` 経路の復旧
- `selfhost/py2cpp.out` 最小経路の安定化
- selfhost コンパイルエラーの段階削減
- `tools/prepare_selfhost_source.py` スタブ整理
- selfhost 暴走時に早期停止できるガード上限制御の導入（CLI オプション化）

非対象:
- C++ 以外ターゲットの最適化
- selfhost と無関係な文法追加

受け入れ基準:
- selfhost の入力/生成/実行が再現可能
- 回帰時に再検出手順が残っている
- スタブ依存が段階的に減る

確認コマンド:
- `python3 tools/build_selfhost.py`
- `python3 tools/check_selfhost_cpp_diff.py`
- `python3 tools/verify_selfhost_end_to_end.py --skip-build --cases sample/py/01_mandelbrot.py sample/py/17_monte_carlo_pi.py test/fixtures/control/if_else.py`
- `python3 tools/check_selfhost_direct_compile.py --cases sample/py/*.py`

サブタスク実行順（todo 同期）:

1. `P0-SH-04-S1`: `tools/prepare_selfhost_source.py` の残存スタブを棚卸しし、恒久機能化対象と削除対象に分類する。
2. `P0-SH-04-S2`: 恒久化対象を compiler/runtime 側へ移し、prepare スクリプト固有分岐を段階削減する。
   - `P0-SH-04-S2-S1`: `CodeEmitter` 本体へ dynamic hooks の有効/無効フラグを追加する。
   - `P0-SH-04-S2-S2`: `_patch_code_emitter_hooks_for_selfhost` をフラグ設定方式へ縮退する。
   - `P0-SH-04-S2-S3`: `load_cpp_hooks` fallback を compiler 側へ移し、`_patch_load_cpp_hooks_for_selfhost` を撤去する。
3. `P0-SH-04-S3`: 通常 selfhost と guard profile 付き selfhost の回帰を再計測し、prepare 依存の再流入を防ぐ。
4. `P0-SH-05`: fail-fast ガード（`--guard-profile` / `--max-*`）の導入済み状態を維持し、回帰時は同導線で再検証する。

`P0-SH-04-S1` 棚卸し結果（`tools/prepare_selfhost_source.py`）:

- 恒久機能化対象（S2 で compiler/runtime 側へ移す）:
  - `_patch_code_emitter_hooks_for_selfhost`: `CodeEmitter._call_hook` の dynamic callable を selfhost だけ `return None` 化しており、現状の最大スタブ。selfhost 用パッチではなく `CodeEmitter` 本体の「hooks 無効モード」へ昇格させる。
  - `_patch_load_cpp_hooks_for_selfhost`: `load_cpp_hooks` 内の `hooks = build_cpp_hooks()` を `hooks = {}` へ差し替えている。`load_cpp_hooks` 側で「フックなし初期化」を正規機能として持たせ、差し替え依存を除去する。
- 削除対象（S2 完了後に prepare から外す）:
  - `_remove_import_line` の `build_cpp_hooks` import 除去分岐: 上記恒久機能化により selfhost 側で import 抜き差しする必要がなくなるため削除。
  - `_patch_load_cpp_hooks_for_selfhost`: `load_cpp_hooks` 正規化後は置換関数自体を削除。
- 維持対象（スタブではなく selfhost 生成基盤）:
  - `_extract_support_blocks` / `_insert_code_emitter`: selfhost 単一ソース化の基盤であり、S1 時点では削除対象にしない。

決定ログ:
- 2026-02-22: 初版作成（todo から文脈分離）。
- 2026-02-23: selfhost 実行の暴走対策として、構文木深さ/ノード数/スコープ深さ/シンボル数/import graph 規模/生成量の上限を CLI オプションで指定できるガード設計を `P0-SH-05` として追加。`guard_profile`（`off/default/strict`）と個別上限（`--max-ast-depth` など）を段階導入対象にした。
- 2026-02-23: `P0-SH-05` を実装完了。`src/pytra/compiler/transpile_cli.py::parse_py2cpp_argv` に `--guard-profile` / `--max-*` を追加し、`src/py2cpp.py` で profile 解決（`off/default/strict`）+ 個別上書き + stage 別 fail-fast を導入した。`parse`（`max-ast-depth`, `max-parse-nodes`）、`analyze`（`max-symbols-per-module`, `max-scope-depth`, `max-import-graph-nodes`, `max-import-graph-edges`）、`emit`（`max-generated-lines`）で超過時に `input_invalid(kind=limit_exceeded, stage=..., limit=..., value=..., max=...)` を返す。`python3 test/unit/test_py2cpp_features.py Py2CppFeatureTest.test_parse_py2cpp_argv_guard_options Py2CppFeatureTest.test_guard_limit_exceeded_in_parse_stage Py2CppFeatureTest.test_guard_limit_exceeded_in_analyze_stage Py2CppFeatureTest.test_guard_limit_exceeded_in_emit_stage`、`python3 tools/build_selfhost.py`、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）で回帰を確認した。
- 2026-02-23: `P0-SH-04` の継続として `tools/prepare_selfhost_source.py` から `build_cpp_hooks` 同梱スタブを再削除し、`_patch_load_cpp_hooks_for_selfhost` を復活。`load_cpp_hooks(...)` ブロックの `hooks = build_cpp_hooks()` 1行だけを `hooks = {}` へ置換する方式に統一した。置換境界は 1 行に限定しつつ selfhost 専用スタブを削減できる。`test/unit/test_prepare_selfhost_source.py` に正常系/異常系を追加して `python3 test/unit/test_prepare_selfhost_source.py`（7件成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 既知維持）、`python3 tools/check_transpiler_version_gate.py`（`[OK] no transpiler-related changes detected`）を確認した。
- 2026-02-23: `tools/prepare_selfhost_source.py::_patch_code_emitter_hooks_for_selfhost` の dynamic call 無効化を、固定 7 文字列置換から `_call_hook` ブロック内の `return fn(...)` 行検出ベースへ変更した。これにより `_call_hook` 本体の軽微な整形変更に追従しつつ、無効化対象が想定 7 行からずれた場合は `replaced=<count>` で fail-fast する。`python3 test/unit/test_prepare_selfhost_source.py`（6件成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）、`python3 tools/check_transpiler_version_gate.py`（`[OK] no transpiler-related changes detected`）を確認した。
- 2026-02-23: `tools/prepare_selfhost_source.py::_patch_code_emitter_hooks_for_selfhost` のパッチ境界をさらに縮小し、`_call_hook` 関数ブロック全置換をやめて `return fn(...)` 7行のみを `return None` へ置換する方式へ変更した。これにより `fn = self._lookup_hook(name)` や `argc` 分岐の正本ロジックを selfhost 側へ残しつつ、C++ で失敗する dynamic callable 式だけを無効化できる。`test/unit/test_prepare_selfhost_source.py` で `return fn(self` 非存在と異常系（dynamic call 行欠落）を固定化し、`python3 test/unit/test_prepare_selfhost_source.py`（6件成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）、`python3 tools/check_transpiler_version_gate.py`（`[OK] no transpiler-related changes detected`）を確認した。
- 2026-02-23: `tools/prepare_selfhost_source.py` の `load_cpp_hooks` 向け 1 行置換（`_patch_load_cpp_hooks_for_selfhost`）を撤去し、`_extract_support_blocks` 側で `build_cpp_hooks() -> dict[str, Any]` の最小スタブ（`return {}`）を同梱する方式へ変更した。これにより `load_cpp_hooks(...)` 本体を正本のまま selfhost 展開できるようになり、selfhost 専用パッチ境界を `CodeEmitter._call_hook` no-op 化のみに限定できる。`test/unit/test_prepare_selfhost_source.py` を更新してスタブ同梱と merged source 内の `hooks = build_cpp_hooks()` 維持を固定化し、`python3 test/unit/test_prepare_selfhost_source.py`（6件成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）、`python3 tools/check_transpiler_version_gate.py`（`[OK] no transpiler-related changes detected`）を確認した。
- 2026-02-22: `build_selfhost` は通るが、`check_selfhost_cpp_diff --mode allow-not-implemented` は `mismatches=3`（`if_else.py`, `01_mandelbrot.py`, `17_monte_carlo_pi.py`）を再確認。`verify_selfhost_end_to_end --skip-build` では `17_monte_carlo_pi.py` の checksum 不一致のみ失敗。
- 2026-02-22: 差分調査で、`selfhost/py2cpp.out` 生成結果は `if` / `for` のネスト本文が欠落する一方、`PYTHONPATH=src python3 selfhost/py2cpp.py` では本文が維持されることを確認。原因は selfhost binary 側 parser/runtime 経路（`core.cpp` 系）を優先調査対象とする。
- 2026-02-22: 原因を `CodeEmitter` 既定の `emit_scoped_stmt_list` / `emit_scoped_block` 呼び出しが selfhost C++ で base 実装へ静的束縛される点に訂正。`src/py2cpp.py` の `CppEmitter` 側へ同名 override を追加してネスト本文欠落を解消し、`verify_selfhost_end_to_end --skip-build --cases sample/py/01_mandelbrot.py sample/py/17_monte_carlo_pi.py test/fixtures/control/if_else.py` で `failures=0` を確認。
- 2026-02-22: `CppEmitter.__init__` の import 解決テーブル再初期化を削除し、selfhost C++ の base/derived メンバ分離で `math.*` 解決が失敗する経路を修正。`verify_selfhost_end_to_end --skip-build --cases sample/py/02_raytrace_spheres.py sample/py/06_julia_parameter_sweep.py sample/py/10_plasma_effect.py sample/py/11_lissajous_particles.py sample/py/14_raymarching_light_cycle.py sample/py/16_glass_sculpture_chaos.py` で `failures=0`、`python3 tools/check_selfhost_direct_compile.py --cases sample/py/*.py` で `failures=0` を確認。
- 2026-02-22: `tools/prepare_selfhost_source.py` から `dump_codegen_options_text` 置換パスと `main guard` 置換パスを削除し、正本 `transpile_cli.py` / `py2cpp.py` 実装をそのまま selfhost へ展開。`python3 tools/build_selfhost.py`、`./selfhost/py2cpp.out -h`（exit=0）、`./selfhost/py2cpp.out sample/py/01_mandelbrot.py --dump-options -o /tmp/selfhost_dump_opts.cpp`、`python3 tools/verify_selfhost_end_to_end.py --skip-build --cases sample/py/01_mandelbrot.py sample/py/17_monte_carlo_pi.py test/fixtures/control/if_else.py` で回帰なしを確認。
- 2026-02-22: `tools/prepare_selfhost_source.py` から `exception/help` 置換パス（`_patch_selfhost_exception_paths`）と補助関数 `is_help_requested` を削除し、CLI の正本分岐をそのまま selfhost へ展開。`python3 tools/build_selfhost.py`、`./selfhost/py2cpp.out -h`（exit=0）、`./selfhost/py2cpp.out sample/py/01_mandelbrot.py --dump-options -o /tmp/selfhost_dump_opts3.cpp`、`python3 tools/verify_selfhost_end_to_end.py --skip-build --cases test/fixtures/control/if_else.py`、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）で回帰なしを確認。
- 2026-02-22: `CodeEmitter` hooks no-op 置換の除去可否を確認。`out = _patch_code_emitter_hooks_for_selfhost(out)` を外すと selfhost C++ で `CodeEmitter::hook_on_*` 内の `fn(*this, ...)` 呼び出しが `object` callable 解決できず多数コンパイルエラーになることを確認し、置換を復帰。`python3 tools/build_selfhost.py` と `python3 tools/verify_selfhost_end_to_end.py --skip-build --cases test/fixtures/control/if_else.py` で安定状態へ戻した。
- 2026-02-23: selfhost parser の import 誤検知を修正。`src/pytra/std/re.py` の `^import\\s+(.+)$` 実装が `startswith("import")` 判定で `import_modules` を誤認していたため、キーワード直後の空白必須へ厳密化した。`test/unit/test_pylib_re.py` と `test/unit/test_east_core.py::test_identifier_prefixed_with_import_is_not_import_stmt` を追加し、`python3 src/py2cpp.py selfhost/py2cpp.py -o /tmp/selfhost_repro.cpp` の通過を確認した。
- 2026-02-23: selfhost transpile の次段ブロッカーとして `object receiver` 制約を 1 件修正。`src/py2cpp.py::_node_contains_call_name` の `Any` 直接 `node.get(...)` を `dict` 正規化経由へ変更し、selfhost source transpile を継続可能にした。`python3 tools/build_selfhost.py` は C++ compile 段階で失敗し、先頭エラーは `for (object ... : dict/list[str])` 由来の型不整合（`selfhost/py2cpp.cpp:3354,6074,9413` など）へ更新された。
- 2026-02-23: 上記ブロッカーを `src/py2cpp.py` 側で段階解消。`for` 走査の selfhost-safe 置換（`range(len(...))` / `items()`）、`_analyze_import_graph` の `graph_adj[cur_key]` append 再代入化、`_format_graph_list_section` の `list[str]` 厳格化、`build_module_symbol_index` / `_module_export_table` の `Assign.targets` を `_dict_any_get_dict_list` へ統一し、`python3 tools/build_selfhost.py` を再通過させた。合わせて `python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）と `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）を確認し、`src/pytra/compiler/transpiler_versions.json` の `cpp` を `0.56.0 -> 0.57.0` へ更新して `python3 tools/check_transpiler_version_gate.py` を通過させた。
- 2026-02-23: `tools/prepare_selfhost_source.py` の hook no-op 置換を縮退。従来は `hook_on_*` 11 メソッドを個別置換していたが、`src/pytra/compiler/east_parts/code_emitter.py` 側で hook 呼び出しを `_call_hook` / `_call_hook1..6` へ集約し、selfhost では当該ヘルパ群のみを no-op 化する方式へ変更した。`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）、`python3 tools/verify_selfhost_end_to_end.py --skip-build --cases sample/py/01_mandelbrot.py sample/py/17_monte_carlo_pi.py test/fixtures/control/if_else.py`（`failures=0`）で回帰なしを確認。併せて shared gate 対応として `src/pytra/compiler/transpiler_versions.json` の `shared` を `0.2.0 -> 0.3.0` に更新し、`python3 tools/check_transpiler_version_gate.py` を通過させた。
- 2026-02-23: 置換境界をさらに縮小し、`tools/prepare_selfhost_source.py::_patch_code_emitter_hooks_for_selfhost` は `CodeEmitter._call_hook` 本体のみ no-op 置換する構成へ変更。`_call_hook1..6` は正本実装を selfhost 側へ残せるようにした。`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）、`python3 tools/check_transpiler_version_gate.py`（`[OK] no transpiler-related changes detected`）を確認した。
- 2026-02-23: `tools/prepare_selfhost_source.py` の置換境界回帰を固定するため `test/unit/test_prepare_selfhost_source.py` を追加。変換結果で `_call_hook` のみが no-op 置換され、`_call_hook1..6` と `hook_on_emit_stmt` が正本ロジック（`return self._call_hook(...)` / bool 判定）を維持していることを検証する。`python3 test/unit/test_prepare_selfhost_source.py` の通過を確認した。
- 2026-02-23: `tools/prepare_selfhost_source.py::_patch_code_emitter_hooks_for_selfhost` の失敗検出を強化。`_call_hook` / `_call_hook1` マーカー未検出時に `RuntimeError` を送出するよう変更し、置換が静かにスキップされる回帰を防止した。`test/unit/test_prepare_selfhost_source.py` に異常系2ケース（ブロック欠落・終端マーカー欠落）を追加し、`python3 test/unit/test_prepare_selfhost_source.py`（2件成功）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）を確認した。
- 2026-02-23: `tools/prepare_selfhost_source.py::_extract_support_blocks` の `build_cpp_hooks` スタブを最小化し、`pass` と中間変数 `out` を削除して `return {}` のみへ整理した。`test/unit/test_prepare_selfhost_source.py::test_extract_support_blocks_does_not_inline_build_cpp_hooks` を追加し、`python3 test/unit/test_prepare_selfhost_source.py`（3件成功）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）を確認した。
- 2026-02-23: `_patch_code_emitter_hooks_for_selfhost` の `_call_hook` no-op スタブをさらに最小化し、不要な `pass` を削除して `return None` のみへ整理した。`test/unit/test_prepare_selfhost_source.py` の既存検証を更新し、`_call_hook` ブロックに `pass` が残らないことを固定化した。`python3 test/unit/test_prepare_selfhost_source.py`（3件成功）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）を確認した。
- 2026-02-23: `build_cpp_hooks` の selfhost 専用スタブ関数を削除し、`_patch_load_cpp_hooks_for_selfhost` を追加して `load_cpp_hooks(...)` 本体を selfhost 生成時だけ `return {}` へ置換する方式に変更した。`test/unit/test_prepare_selfhost_source.py` に `load_cpp_hooks` 置換の正常系/異常系テストを追加し、`python3 test/unit/test_prepare_selfhost_source.py`（5件成功）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）を確認した。
- 2026-02-23: `tools/prepare_selfhost_source.py::_remove_import_line` を fail-fast 化し、`CodeEmitter`/`transpile_cli`/`build_cpp_hooks` の import 行が見つからない場合に `RuntimeError` を送出するよう変更した。`test/unit/test_prepare_selfhost_source.py` に import 除去の正常系/異常系テストを追加し、`python3 test/unit/test_prepare_selfhost_source.py`（7件成功）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）を確認した。
- 2026-02-23: `_patch_load_cpp_hooks_for_selfhost` の置換境界を縮小し、`load_cpp_hooks(...)` 関数ブロック全体の差し替えを廃止して `hooks = build_cpp_hooks()` の1行だけを `hooks = {}` へ置換する方式へ変更した。`test/unit/test_prepare_selfhost_source.py` の `load_cpp_hooks` 置換テストを更新し、`python3 test/unit/test_prepare_selfhost_source.py`（7件成功）、`python3 tools/build_selfhost.py`（成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=129 ok=129 fail=0 skipped=6`）、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）を確認した。
- 2026-02-23: docs-jp/todo.md の P0-SH-04 を -S1 〜 -S3 に分割したため、本 plan の関連 TODO と実行順を同粒度に同期した。
- 2026-02-23: `P0-SH-04-S1` を完了。`tools/prepare_selfhost_source.py` の残存 selfhost 専用パッチを棚卸しし、`_patch_code_emitter_hooks_for_selfhost` / `_patch_load_cpp_hooks_for_selfhost` を恒久機能化対象、`build_cpp_hooks` import 除去分岐を削除対象、`_extract_support_blocks` 系を維持対象に分類した。
- 2026-02-23: `P0-SH-04-S2` を `S2-S1` 〜 `S2-S3` に分割した。先行して `S2-S1` を完了し、`src/pytra/compiler/east_parts/code_emitter.py` に `dynamic_hooks_enabled` と `set_dynamic_hooks_enabled()` を追加して、dynamic hooks 無効化を prepare 固有置換ではなく本体機能として表現できる土台を導入した。`python3 test/unit/test_code_emitter.py`（34件成功）、`python3 test/unit/test_prepare_selfhost_source.py`（7件成功）、`python3 tools/check_py2cpp_transpile.py`（`checked=131 ok=131 fail=0 skipped=6`）で回帰なしを確認した。
