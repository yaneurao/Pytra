# TASK GROUP: TG-P3-MISC-CONV

Last updated: 2026-02-25

Related TODO:
- `ID: P3-MISC-01` in `docs/ja/todo/index.md`

Background:
- Re-establish a state where `py2cpp.py` conversion succeeds for the newly added 100 Python samples under `test/misc/`.
- As conversion may still be incomplete at this point, start at a reproducible level with very low priority.

In scope:
- All 100 files in `test/misc/*.py` (`01_*` through `100_*`)

Out of scope:
- Post-conversion execution speed improvements
- Code-quality optimization for conversion results (deduplication, formatting improvements)

Acceptance criteria:
- For each target file, `python3 src/py2cpp.py test/misc/<file>.py <tmp>.cpp` succeeds.
- As a prerequisite for future all-target smoke expansion, transpile-failure exceptions are eliminated.
- At each task completion, append failure logs for the target files to the decision log.

Constraints:
- `test/misc/*.py` is regression input data; do not modify content during this task.
- Fixes must be done in transpiler-side logic (`py2cpp`/east/code-emitter) or shared processing.
- If a file is hard to convert immediately, log it as `deferred by difficulty` with reason and retry later from easier files.

Decision log:
- 2026-02-25: `P3-MISC-01-S002` targeted `01_prime_reporter.py`; bypassed attribute-access failure.
  In `CppEmitter._render_attribute_expr`, when owner class can be fixed via `class_field_owner_unique` / `class_method_owner_unique`, skip object-receiver exceptions.
  Confirmed `py2cpp.py test/misc/01_prime_reporter.py /tmp/01_prime_reporter.cpp` succeeds.
- 2026-02-25: `P3-MISC-01-S002` failure root cause for `02_text_analyzer.py` was unresolved `collections` import graph (`missing_module`).
  Added `collections` to `is_known_non_user_import` and confirmed successful conversion.
- 2026-02-25: `P3-MISC-01-S003` failure for `03_gradebook.py` came from `statistics` import (`missing_module`) and `object receiver` constraints.
  Added `statistics` to `is_known_non_user_import`, then adjusted `CppEmitter.validate_call_receiver_or_raise` to allow class-specific method-attribute resolution first.
  Confirmed `py2cpp.py test/misc/03_gradebook.py /tmp/03_gradebook.cpp` succeeds.
- 2026-02-25: `P3-MISC-01-S004` target `04_maze_solver.py` succeeded with `py2cpp.py test/misc/04_maze_solver.py /tmp/04_maze_solver.cpp`.
  Added `resolved_type` reflection for `For` tuple targets and corrected element-type inference for `enumerate`.
- 2026-02-25: `P3-MISC-01-S005` target `05_sales_report.py` succeeded.
  Reflected `resolved_type` to `Name` targets in `for` loops and added lightweight return-type inference for built-in `str` methods (`strip`/`split`/`splitlines`, etc.).
- 2026-02-25: `P3-MISC-01-S006` target `06_ascii_chart.py` succeeded.
  Updated self-hosted expression parser in `core.py`: list-comprehension target parsing now goes through `_parse_comp_target()` instead of fixed `Name`, allowing tuple targets like `for curr, prev in zip(...)`.
- 2026-02-25: `P3-MISC-01-S007` target `07_task_scheduler.py` succeeded with no additional code changes.
- 2026-02-25: `P3-MISC-01-S008` target `08_bank_account.py` succeeded with no additional code changes.
- 2026-02-25: `P3-MISC-01-S009` target `09_weather_simulator.py` succeeded with no additional workaround.
- 2026-02-25: `P3-MISC-01-S010` target `100_pipeline_flow.py` succeeded with no additional conversion changes.
- 2026-02-25: `P3-MISC-01-S011` target `10_battle_simulation.py` succeeded.
  Root cause was missing `lowered_kind` in self-hosted normalization of `any(...)`; fixed `_sh_parse_expr_lowered` any/all normalization branch to attach `BuiltinCall` (`runtime_call=py_any`).
- 2026-02-25: `P3-MISC-01-S012` target `11_oceanic_timeseries.py` succeeded with no additional fix.
- 2026-02-25: `P3-MISC-01-S013` target `12_token_grammar.py` succeeded with no additional fix.
- 2026-02-25: `P3-MISC-01-S014` target `13_route_graph.py` succeeded.
  Beyond any/all handling, expanded generator-argument parsing in `_parse_call_arg_expr` to multiple `for` clauses, enabling EAST generation for `max((...) for ... for ...)` style.
- 2026-02-25: `P3-MISC-01-S015` target `14_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S016` target `15_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S017` target `16_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S018` target `17_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S019` target `18_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S020` target `19_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S021` target `20_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S022` target `21_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S023` target `22_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S024` target `23_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S025` target `24_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S026` target `25_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S027` target `26_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S028` target `27_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S029` target `28_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S030` target `29_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S031` target `30_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S032` target `31_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S033` target `32_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S034` target `33_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S035` target `34_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S036` target `35_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S037` target `36_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S038` target `37_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S039` target `38_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S040` target `39_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S041` target `40_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S042` target `41_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S043` target `42_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S044` target `43_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S045` target `44_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S046` target `45_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S047` target `46_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S048` target `47_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S049` target `48_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S050` target `49_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S051` target `50_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S052` target `51_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S053` target `52_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S054` target `53_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S055` target `54_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S056` target `55_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S057` target `56_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S058` target `57_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S059` target `58_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S060` target `59_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S061` target `60_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S062` target `61_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S063` target `62_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S064` target `63_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S065` target `64_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S066` target `65_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S067` target `66_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S068` target `67_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S069` target `68_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S070` target `69_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S071` target `70_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S072` target `71_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S073` target `72_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S074` target `73_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S075` target `74_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S076` target `75_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S077` target `76_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S078` target `77_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S079` target `78_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S080` target `79_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S081` target `80_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S082` target `81_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S083` target `82_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S084` target `83_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S085` target `84_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S086` target `85_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S087` target `86_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S088` target `87_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S089` target `88_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S090` target `89_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S091` target `90_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S092` target `91_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S093` target `92_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S094` target `93_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S095` target `94_ledger_trace.py` succeeded.
- 2026-02-25: `P3-MISC-01-S096` target `95_pipeline_flow.py` succeeded.
- 2026-02-25: `P3-MISC-01-S097` target `96_oceanic_timeseries.py` succeeded.
- 2026-02-25: `P3-MISC-01-S098` target `97_token_grammar.py` succeeded.
- 2026-02-25: `P3-MISC-01-S099` target `98_route_graph.py` succeeded.
- 2026-02-25: `P3-MISC-01-S100` target `99_ledger_trace.py` succeeded.

### Breakdown
