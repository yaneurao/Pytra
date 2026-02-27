# TASK GROUP: TG-P3-MISC-CONV

最終更新: 2026-02-25

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P3-MISC-01`

背景:
- `test/misc/` に追加した 100 件の Python サンプルで `py2cpp.py` 変換を通せる状態を再確立する。
- 現時点では変換未完了の可能性があるため、超低優先で再現可能なレベルから着手する。

対象:
- `test/misc/*.py` 全 100 件（`01_*` 〜 `100_*`）

非対象:
- 変換後の実行速度改善
- 変換結果のコード品質最適化（重複排除、整形改善）

受け入れ基準:
- 各対象ファイルで `python3 src/py2cpp.py test/misc/<file>.py <tmp>.cpp` が成功する。
- 将来 `--targets` 全言語の smoke テストに繋ぐ際の前提として、変換不能例外を解消している。
- 各タスク完了時、該当ファイルの失敗ログを決定ログへ追記。

制約:
- `test/misc/*.py` は元ソースの回帰検証データであり、タスク実行時に内容を改変しない。
- 変換器側（py2cpp/east/code-emitter）または共通処理の追加で対応する。
- 個別変換が難しい場合は、`難易度保留` としてログに理由を残し、容易なものから後回しで再挑戦する。

決定ログ:
- 2026-02-25: `P3-MISC-01-S002` を対象 ID として、`01_prime_reporter.py` の属性アクセス失敗を回避。
  `CppEmitter._render_attribute_expr` で `class_field_owner_unique` / `class_method_owner_unique` により所有クラスが確定できる場合は
  `object` 系受け手例外をスキップし、`py2cpp.py test/misc/01_prime_reporter.py /tmp/01_prime_reporter.cpp` を成功させた。
- 2026-02-25: P3-MISC-01-S002 の失敗は `collections` の import_graph 未解決による missing_module だったため、
  `is_known_non_user_import` に `collections` を追加。`py2cpp.py test/misc/02_text_analyzer.py /tmp/02_text_analyzer.cpp` が成功し、以後
  `docs/ja/todo/index.md` の該当チェックを完了済みに更新。
- 2026-02-25: P3-MISC-01-S003 の失敗は `statistics` import の missing_module と `object receiver` 制約で発生しており、`is_known_non_user_import` に
  `statistics` を追加、加えて `CppEmitter.validate_call_receiver_or_raise` で `Class` 固有メソッドの属性名解決を先行許可する形へ調整した後、
  `py2cpp.py test/misc/03_gradebook.py /tmp/03_gradebook.cpp` を成功させた。
- 2026-02-25: P3-MISC-01-S004 対象の `test/misc/04_maze_solver.py` は `py2cpp.py test/misc/04_maze_solver.py /tmp/04_maze_solver.cpp` に成功し、
  `For` タプルターゲットの `resolved_type` 反映と `enumerate` の要素型推論補正を導入した。
- 2026-02-25: P3-MISC-01-S005 対象の `test/misc/05_sales_report.py` は `py2cpp.py test/misc/05_sales_report.py /tmp/05_sales_report.cpp` で成功。
  `core.py` の `for` ループで `Name` ターゲットへ `resolved_type` を反映し、`str` 組み込みメソッド
  (`strip`/`split`/`splitlines` 等) の簡易戻り型推論を追加した。
- 2026-02-25: P3-MISC-01-S006 対象の `test/misc/06_ascii_chart.py` は `py2cpp.py test/misc/06_ascii_chart.py /tmp/06_ascii_chart.cpp` で成功。
  `core.py` の self-hosted 式パーサで list comprehension のターゲット解析を `Name` 固定から
  `_parse_comp_target()` を経由する形へ変更し、`for curr, prev in zip(...)` の tuple target を許容した。
- 2026-02-25: P3-MISC-01-S007 対象の `test/misc/07_task_scheduler.py` は `py2cpp.py test/misc/07_task_scheduler.py /tmp/07_task_scheduler.cpp` で成功。
  異常なく変換できたため、当該タスクを完了扱いにした。
- 2026-02-25: P3-MISC-01-S008 対象の `test/misc/08_bank_account.py` は `py2cpp.py test/misc/08_bank_account.py /tmp/08_bank_account.cpp` で成功。
  追加のコード修正なしで完了。
- 2026-02-25: P3-MISC-01-S009 対象の `test/misc/09_weather_simulator.py` は
  `py2cpp.py test/misc/09_weather_simulator.py /tmp/09_weather_simulator.cpp` で成功。
  追加の回避策は不要で完了。
- 2026-02-25: P3-MISC-01-S010 対象の `test/misc/100_pipeline_flow.py` は
  `py2cpp.py test/misc/100_pipeline_flow.py /tmp/100_pipeline_flow.cpp` で成功。
  追加の変換修正を要さず完了。
- 2026-02-25: P3-MISC-01-S011 対象の `test/misc/10_battle_simulation.py` は
  `py2cpp.py test/misc/10_battle_simulation.py /tmp/10_battle_simulation.cpp` で成功。
  失敗原因は `any(...)` の self-hosted 正規化時に `lowered_kind` が欠ける点で、`_sh_parse_expr_lowered` の
  any/all 正規化 branch を `BuiltinCall` 付与で修正した（`runtime_call` は `py_any`）。
- 2026-02-25: P3-MISC-01-S012 対象の `test/misc/11_oceanic_timeseries.py` は
  `py2cpp.py test/misc/11_oceanic_timeseries.py /tmp/11_oceanic_timeseries.cpp` で成功。
  追加の修正は不要で完了。
- 2026-02-25: P3-MISC-01-S013 対象の `test/misc/12_token_grammar.py` は
  `py2cpp.py test/misc/12_token_grammar.py /tmp/12_token_grammar.cpp` で成功。
  追加の修正は不要で完了。
- 2026-02-25: P3-MISC-01-S014 対象の `test/misc/13_route_graph.py` は
  `py2cpp.py test/misc/13_route_graph.py /tmp/13_route_graph.cpp` で成功。
  `any/all` を除き、`_parse_call_arg_expr` の generator 引数解析を複数 `for` 対応に拡張し、
  `max((...) for ... for ...)` 系を EAST 生成できるようにした。
- 2026-02-25: P3-MISC-01-S015 対象の `test/misc/14_ledger_trace.py` は
  `py2cpp.py test/misc/14_ledger_trace.py /tmp/14_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S016 対象の `test/misc/15_pipeline_flow.py` は
  `py2cpp.py test/misc/15_pipeline_flow.py /tmp/15_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S017 対象の `test/misc/16_oceanic_timeseries.py` は
  `py2cpp.py test/misc/16_oceanic_timeseries.py /tmp/16_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S018 対象の `test/misc/17_token_grammar.py` は
  `py2cpp.py test/misc/17_token_grammar.py /tmp/17_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S019 対象の `test/misc/18_route_graph.py` は
  `py2cpp.py test/misc/18_route_graph.py /tmp/18_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S020 対象の `test/misc/19_ledger_trace.py` は
  `py2cpp.py test/misc/19_ledger_trace.py /tmp/19_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S021 対象の `test/misc/20_pipeline_flow.py` は
  `py2cpp.py test/misc/20_pipeline_flow.py /tmp/20_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S022 対象の `test/misc/21_oceanic_timeseries.py` は
  `py2cpp.py test/misc/21_oceanic_timeseries.py /tmp/21_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S023 対象の `test/misc/22_token_grammar.py` は
  `py2cpp.py test/misc/22_token_grammar.py /tmp/22_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S024 対象の `test/misc/23_route_graph.py` は
  `py2cpp.py test/misc/23_route_graph.py /tmp/23_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S025 対象の `test/misc/24_ledger_trace.py` は
  `py2cpp.py test/misc/24_ledger_trace.py /tmp/24_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S026 対象の `test/misc/25_pipeline_flow.py` は
  `py2cpp.py test/misc/25_pipeline_flow.py /tmp/25_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S027 対象の `test/misc/26_oceanic_timeseries.py` は
  `py2cpp.py test/misc/26_oceanic_timeseries.py /tmp/26_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S028 対象の `test/misc/27_token_grammar.py` は
  `py2cpp.py test/misc/27_token_grammar.py /tmp/27_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S029 対象の `test/misc/28_route_graph.py` は
  `py2cpp.py test/misc/28_route_graph.py /tmp/28_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S030 対象の `test/misc/29_ledger_trace.py` は
  `py2cpp.py test/misc/29_ledger_trace.py /tmp/29_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S031 対象の `test/misc/30_pipeline_flow.py` は
  `py2cpp.py test/misc/30_pipeline_flow.py /tmp/30_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S032 対象の `test/misc/31_oceanic_timeseries.py` は
  `py2cpp.py test/misc/31_oceanic_timeseries.py /tmp/31_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S033 対象の `test/misc/32_token_grammar.py` は
  `py2cpp.py test/misc/32_token_grammar.py /tmp/32_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S034 対象の `test/misc/33_route_graph.py` は
  `py2cpp.py test/misc/33_route_graph.py /tmp/33_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S035 対象の `test/misc/34_ledger_trace.py` は
  `py2cpp.py test/misc/34_ledger_trace.py /tmp/34_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S036 対象の `test/misc/35_pipeline_flow.py` は
  `py2cpp.py test/misc/35_pipeline_flow.py /tmp/35_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S037 対象の `test/misc/36_oceanic_timeseries.py` は
  `py2cpp.py test/misc/36_oceanic_timeseries.py /tmp/36_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S038 対象の `test/misc/37_token_grammar.py` は
  `py2cpp.py test/misc/37_token_grammar.py /tmp/37_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S039 対象の `test/misc/38_route_graph.py` は
  `py2cpp.py test/misc/38_route_graph.py /tmp/38_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S040 対象の `test/misc/39_ledger_trace.py` は
  `py2cpp.py test/misc/39_ledger_trace.py /tmp/39_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S041 対象の `test/misc/40_pipeline_flow.py` は
  `py2cpp.py test/misc/40_pipeline_flow.py /tmp/40_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S042 対象の `test/misc/41_oceanic_timeseries.py` は
  `py2cpp.py test/misc/41_oceanic_timeseries.py /tmp/41_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S043 対象の `test/misc/42_token_grammar.py` は
  `py2cpp.py test/misc/42_token_grammar.py /tmp/42_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S044 対象の `test/misc/43_route_graph.py` は
  `py2cpp.py test/misc/43_route_graph.py /tmp/43_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S045 対象の `test/misc/44_ledger_trace.py` は
  `py2cpp.py test/misc/44_ledger_trace.py /tmp/44_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S046 対象の `test/misc/45_pipeline_flow.py` は
  `py2cpp.py test/misc/45_pipeline_flow.py /tmp/45_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S047 対象の `test/misc/46_oceanic_timeseries.py` は
  `py2cpp.py test/misc/46_oceanic_timeseries.py /tmp/46_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S048 対象の `test/misc/47_token_grammar.py` は
  `py2cpp.py test/misc/47_token_grammar.py /tmp/47_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S049 対象の `test/misc/48_route_graph.py` は
  `py2cpp.py test/misc/48_route_graph.py /tmp/48_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S050 対象の `test/misc/49_ledger_trace.py` は
  `py2cpp.py test/misc/49_ledger_trace.py /tmp/49_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S051 対象の `test/misc/50_pipeline_flow.py` は
  `py2cpp.py test/misc/50_pipeline_flow.py /tmp/50_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S052 対象の `test/misc/51_oceanic_timeseries.py` は
  `py2cpp.py test/misc/51_oceanic_timeseries.py /tmp/51_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S053 対象の `test/misc/52_token_grammar.py` は
  `py2cpp.py test/misc/52_token_grammar.py /tmp/52_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S054 対象の `test/misc/53_route_graph.py` は
  `py2cpp.py test/misc/53_route_graph.py /tmp/53_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S055 対象の `test/misc/54_ledger_trace.py` は
  `py2cpp.py test/misc/54_ledger_trace.py /tmp/54_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S056 対象の `test/misc/55_pipeline_flow.py` は
  `py2cpp.py test/misc/55_pipeline_flow.py /tmp/55_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S057 対象の `test/misc/56_oceanic_timeseries.py` は
  `py2cpp.py test/misc/56_oceanic_timeseries.py /tmp/56_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S058 対象の `test/misc/57_token_grammar.py` は
  `py2cpp.py test/misc/57_token_grammar.py /tmp/57_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S059 対象の `test/misc/58_route_graph.py` は
  `py2cpp.py test/misc/58_route_graph.py /tmp/58_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S060 対象の `test/misc/59_ledger_trace.py` は
  `py2cpp.py test/misc/59_ledger_trace.py /tmp/59_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S061 対象の `test/misc/60_pipeline_flow.py` は
  `py2cpp.py test/misc/60_pipeline_flow.py /tmp/60_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S062 対象の `test/misc/61_oceanic_timeseries.py` は
  `py2cpp.py test/misc/61_oceanic_timeseries.py /tmp/61_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S063 対象の `test/misc/62_token_grammar.py` は
  `py2cpp.py test/misc/62_token_grammar.py /tmp/62_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S064 対象の `test/misc/63_route_graph.py` は
  `py2cpp.py test/misc/63_route_graph.py /tmp/63_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S065 対象の `test/misc/64_ledger_trace.py` は
  `py2cpp.py test/misc/64_ledger_trace.py /tmp/64_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S066 対象の `test/misc/65_pipeline_flow.py` は
  `py2cpp.py test/misc/65_pipeline_flow.py /tmp/65_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S067 対象の `test/misc/66_oceanic_timeseries.py` は
  `py2cpp.py test/misc/66_oceanic_timeseries.py /tmp/66_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S068 対象の `test/misc/67_token_grammar.py` は
  `py2cpp.py test/misc/67_token_grammar.py /tmp/67_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S069 対象の `test/misc/68_route_graph.py` は
  `py2cpp.py test/misc/68_route_graph.py /tmp/68_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S070 対象の `test/misc/69_ledger_trace.py` は
  `py2cpp.py test/misc/69_ledger_trace.py /tmp/69_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S071 対象の `test/misc/70_pipeline_flow.py` は
  `py2cpp.py test/misc/70_pipeline_flow.py /tmp/70_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S072 対象の `test/misc/71_oceanic_timeseries.py` は
  `py2cpp.py test/misc/71_oceanic_timeseries.py /tmp/71_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S073 対象の `test/misc/72_token_grammar.py` は
  `py2cpp.py test/misc/72_token_grammar.py /tmp/72_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S074 対象の `test/misc/73_route_graph.py` は
  `py2cpp.py test/misc/73_route_graph.py /tmp/73_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S075 対象の `test/misc/74_ledger_trace.py` は
  `py2cpp.py test/misc/74_ledger_trace.py /tmp/74_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S076 対象の `test/misc/75_pipeline_flow.py` は
  `py2cpp.py test/misc/75_pipeline_flow.py /tmp/75_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S077 対象の `test/misc/76_oceanic_timeseries.py` は
  `py2cpp.py test/misc/76_oceanic_timeseries.py /tmp/76_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S078 対象の `test/misc/77_token_grammar.py` は
  `py2cpp.py test/misc/77_token_grammar.py /tmp/77_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S079 対象の `test/misc/78_route_graph.py` は
  `py2cpp.py test/misc/78_route_graph.py /tmp/78_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S080 対象の `test/misc/79_ledger_trace.py` は
  `py2cpp.py test/misc/79_ledger_trace.py /tmp/79_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S081 対象の `test/misc/80_pipeline_flow.py` は
  `py2cpp.py test/misc/80_pipeline_flow.py /tmp/80_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S082 対象の `test/misc/81_oceanic_timeseries.py` は
  `py2cpp.py test/misc/81_oceanic_timeseries.py /tmp/81_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S083 対象の `test/misc/82_token_grammar.py` は
  `py2cpp.py test/misc/82_token_grammar.py /tmp/82_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S084 対象の `test/misc/83_route_graph.py` は
  `py2cpp.py test/misc/83_route_graph.py /tmp/83_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S085 対象の `test/misc/84_ledger_trace.py` は
  `py2cpp.py test/misc/84_ledger_trace.py /tmp/84_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S086 対象の `test/misc/85_pipeline_flow.py` は
  `py2cpp.py test/misc/85_pipeline_flow.py /tmp/85_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S087 対象の `test/misc/86_oceanic_timeseries.py` は
  `py2cpp.py test/misc/86_oceanic_timeseries.py /tmp/86_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S088 対象の `test/misc/87_token_grammar.py` は
  `py2cpp.py test/misc/87_token_grammar.py /tmp/87_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S089 対象の `test/misc/88_route_graph.py` は
  `py2cpp.py test/misc/88_route_graph.py /tmp/88_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S090 対象の `test/misc/89_ledger_trace.py` は
  `py2cpp.py test/misc/89_ledger_trace.py /tmp/89_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S091 対象の `test/misc/90_pipeline_flow.py` は
  `py2cpp.py test/misc/90_pipeline_flow.py /tmp/90_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S092 対象の `test/misc/91_oceanic_timeseries.py` は
  `py2cpp.py test/misc/91_oceanic_timeseries.py /tmp/91_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S093 対象の `test/misc/92_token_grammar.py` は
  `py2cpp.py test/misc/92_token_grammar.py /tmp/92_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S094 対象の `test/misc/93_route_graph.py` は
  `py2cpp.py test/misc/93_route_graph.py /tmp/93_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S095 対象の `test/misc/94_ledger_trace.py` は
  `py2cpp.py test/misc/94_ledger_trace.py /tmp/94_ledger_trace.cpp` で成功。
- 2026-02-25: P3-MISC-01-S096 対象の `test/misc/95_pipeline_flow.py` は
  `py2cpp.py test/misc/95_pipeline_flow.py /tmp/95_pipeline_flow.cpp` で成功。
- 2026-02-25: P3-MISC-01-S097 対象の `test/misc/96_oceanic_timeseries.py` は
  `py2cpp.py test/misc/96_oceanic_timeseries.py /tmp/96_oceanic_timeseries.cpp` で成功。
- 2026-02-25: P3-MISC-01-S098 対象の `test/misc/97_token_grammar.py` は
  `py2cpp.py test/misc/97_token_grammar.py /tmp/97_token_grammar.cpp` で成功。
- 2026-02-25: P3-MISC-01-S099 対象の `test/misc/98_route_graph.py` は
  `py2cpp.py test/misc/98_route_graph.py /tmp/98_route_graph.cpp` で成功。
- 2026-02-25: P3-MISC-01-S100 対象の `test/misc/99_ledger_trace.py` は
  `py2cpp.py test/misc/99_ledger_trace.py /tmp/99_ledger_trace.cpp` で成功。

### 分解
