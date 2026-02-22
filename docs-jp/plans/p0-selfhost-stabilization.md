# TASK GROUP: TG-P0-SH

最終更新: 2026-02-22

関連 TODO:
- `docs-jp/todo.md` の `ID: P0-SH-01` 〜 `P0-SH-04`

背景:
- selfhost の変換・ビルド・実行が不安定だと、回帰検出と改善サイクル全体が止まる。

目的:
- selfhost を日次で再現可能な最小経路に固定し、エラー再発時に即座に再検出できる状態を作る。

対象:
- selfhost `.py` 経路の復旧
- `selfhost/py2cpp.out` 最小経路の安定化
- selfhost コンパイルエラーの段階削減
- `tools/prepare_selfhost_source.py` スタブ整理

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
- `python3 tools/verify_selfhost_end_to_end.py --skip-build --cases sample/py/01_mandelbrot.py sample/py/04_monte_carlo_pi.py test/fixtures/control/if_else.py`
- `python3 tools/check_selfhost_direct_compile.py --cases sample/py/*.py`

決定ログ:
- 2026-02-22: 初版作成（todo から文脈分離）。
- 2026-02-22: `build_selfhost` は通るが、`check_selfhost_cpp_diff --mode allow-not-implemented` は `mismatches=3`（`if_else.py`, `01_mandelbrot.py`, `04_monte_carlo_pi.py`）を再確認。`verify_selfhost_end_to_end --skip-build` では `04_monte_carlo_pi.py` の checksum 不一致のみ失敗。
- 2026-02-22: 差分調査で、`selfhost/py2cpp.out` 生成結果は `if` / `for` のネスト本文が欠落する一方、`PYTHONPATH=src python3 selfhost/py2cpp.py` では本文が維持されることを確認。原因は selfhost binary 側 parser/runtime 経路（`core.cpp` 系）を優先調査対象とする。
- 2026-02-22: 原因を `CodeEmitter` 既定の `emit_scoped_stmt_list` / `emit_scoped_block` 呼び出しが selfhost C++ で base 実装へ静的束縛される点に訂正。`src/py2cpp.py` の `CppEmitter` 側へ同名 override を追加してネスト本文欠落を解消し、`verify_selfhost_end_to_end --skip-build --cases sample/py/01_mandelbrot.py sample/py/04_monte_carlo_pi.py test/fixtures/control/if_else.py` で `failures=0` を確認。
- 2026-02-22: `CppEmitter.__init__` の import 解決テーブル再初期化を削除し、selfhost C++ の base/derived メンバ分離で `math.*` 解決が失敗する経路を修正。`verify_selfhost_end_to_end --skip-build --cases sample/py/02_raytrace_spheres.py sample/py/06_julia_parameter_sweep.py sample/py/10_plasma_effect.py sample/py/11_lissajous_particles.py sample/py/14_raymarching_light_cycle.py sample/py/16_glass_sculpture_chaos.py` で `failures=0`、`python3 tools/check_selfhost_direct_compile.py --cases sample/py/*.py` で `failures=0` を確認。
- 2026-02-22: `tools/prepare_selfhost_source.py` から `dump_codegen_options_text` 置換パスと `main guard` 置換パスを削除し、正本 `transpile_cli.py` / `py2cpp.py` 実装をそのまま selfhost へ展開。`python3 tools/build_selfhost.py`、`./selfhost/py2cpp.out -h`（exit=0）、`./selfhost/py2cpp.out sample/py/01_mandelbrot.py --dump-options -o /tmp/selfhost_dump_opts.cpp`、`python3 tools/verify_selfhost_end_to_end.py --skip-build --cases sample/py/01_mandelbrot.py sample/py/04_monte_carlo_pi.py test/fixtures/control/if_else.py` で回帰なしを確認。
- 2026-02-22: `tools/prepare_selfhost_source.py` から `exception/help` 置換パス（`_patch_selfhost_exception_paths`）と補助関数 `is_help_requested` を削除し、CLI の正本分岐をそのまま selfhost へ展開。`python3 tools/build_selfhost.py`、`./selfhost/py2cpp.out -h`（exit=0）、`./selfhost/py2cpp.out sample/py/01_mandelbrot.py --dump-options -o /tmp/selfhost_dump_opts3.cpp`、`python3 tools/verify_selfhost_end_to_end.py --skip-build --cases test/fixtures/control/if_else.py`、`python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`（`mismatches=3` 維持）で回帰なしを確認。
- 2026-02-22: `CodeEmitter` hooks no-op 置換の除去可否を確認。`out = _patch_code_emitter_hooks_for_selfhost(out)` を外すと selfhost C++ で `CodeEmitter::hook_on_*` 内の `fn(*this, ...)` 呼び出しが `object` callable 解決できず多数コンパイルエラーになることを確認し、置換を復帰。`python3 tools/build_selfhost.py` と `python3 tools/verify_selfhost_end_to_end.py --skip-build --cases test/fixtures/control/if_else.py` で安定状態へ戻した。
