# TODO（未完了）

> `docs-ja/` が正（source of truth）です。`docs/` はその翻訳です。

<a href="../../docs/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-25

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs-ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs-ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs-ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs-ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs-ja/todo/index.md` / `docs-ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。



## P0: サンプル計測の再有効化（最優先）

### 文脈
- `docs-ja/plans/p0-sample-all-language-benchmark.md`
- 進捗: [ID: P0-SAMPLE-BENCH-01] `runtime_parity_check` を全言語対象で再実行し、`cpp` はPASS。`rs/cs/js/ts/go/java/swift/kotlin` は `import`/型/構文の根本混入により失敗、`swiftc` は導入済み。

### タスク（S1〜S3）

1. [x] [ID: P0-SAMPLE-BENCH-01] 必要ツールチェイン（Rust/C#/Go/Java/Swift/Kotlin 等）を環境に導入し、`runtime_parity_check --targets cpp,rs,cs,js,ts,go,java,swift,kotlin` が skip せずに実行される状態にする（Swift は `swiftc` 実行可を必須化）。
2. [x] [ID: P0-SAMPLE-BENCH-02] `sample/py` 全件（01〜18）を全言語ターゲットで実行し、全言語サンプル実行を優先して通す（差分がある場合は言語別で対処）。
   1. [x] [ID: P0-SAMPLE-BENCH-02-S1] `01_mandelbrot` の全言語実行結果を再収集し、失敗カテゴリ（`import` / 型不一致 / 構文混入 / ツール欠如）を確定する。
   2. [x] [ID: P0-SAMPLE-BENCH-02-S2] `02〜18` を全言語ターゲットで再実行し、言語別原因へ紐づける。
      - `docs-ja/plans/p0-sample-all-language-benchmark.md` に `07~18` の再実行結果を追加し、失敗カテゴリを言語別に記録。
   3. [x] [ID: P0-SAMPLE-BENCH-02-S3] `07〜18` を全言語ターゲットで再実行し、`docs-ja/plans/p0-sample-all-language-benchmark.md` の `決定ログ` を更新する。
3. [x] [ID: P0-SAMPLE-BENCH-03] `python3 tools/verify_sample_outputs.py --refresh-golden` を実行し、全言語計測結果を再取得して `readme-ja.md`（必要に応じて `readme.md`）を更新する。


## P1: C++ Emitter Reduction

### 文脈
- `docs-ja/plans/p1-cpp-emitter-reduce.md`

### タスク（S1〜S8, 小粒度）

1. [x] [ID: P1-CPP-EMIT-01] `CppEmitter` の責務分類を確定し、`expression/render/statement/runtime_call/cast/control_flow/misc` の移管対象を固定する。
2. [x] [ID: P1-CPP-EMIT-01-S1] `CppEmitter` の expression rendering のヘルパ群を `src/hooks/cpp/emitter/expr.py` 相当へ移譲し、呼び出し元を最小差分で切り替える。
3. [x] [ID: P1-CPP-EMIT-01-S2] statement rendering のうち `For`/`While`/`If`/`Try` 系を `src/hooks/cpp/emitter/stmt.py` 側に移譲する。
4. [x] [ID: P1-CPP-EMIT-01-S3] cast / runtime-call / import の分岐を専用ヘルパへ整理し、重複分岐を削減する。
5. [x] [ID: P1-CPP-EMIT-01-S4] `temp` 名生成（`__tmp`）と一時変数生存域管理を 1 モジュールへ集約し、同名ロジックの重複を除去する。
6. [x] [ID: P1-CPP-EMIT-01-S5] `fallback_tuple_target_names_from_repr` 系の変換ロジックを共通処理に集約し、`code_emitter` 側互換を壊さずに移管する。
7. [x] [ID: P1-CPP-EMIT-01-S6] `cast`/`object receiver` 周辺の分岐を 1 ハンドラに寄せ、`emit_binary_op` 系の条件分岐重複を 1/3 以下に抑える。
8. [x] [ID: P1-CPP-EMIT-01-S7] `render_trivia` とコメント/ディレクティブ処理を切り出し、`docs-ja/plans/p1-codeemitter-dispatch-redesign.md` との責務整合を確認する。
9. [x] [ID: P1-CPP-EMIT-01-S8] `py2cpp.py` から CppEmitter 本体ロジック参照をなくし、CLI/配線だけに絞る。
10. [x] [ID: P1-CPP-EMIT-01-S9] 上位 API 互換を保ったまま `check_py2cpp_transpile` / `test_py2cpp_smoke` を回して回帰検証を固定する。

### 対応方針
- 1 つの `S*` は原則 1〜3 関数単位で着手し、1 タスクあたり 1 コミット以内で完了可能な粒度にする。
- 各 `S*` の終端で `git diff` を確認し、受け入れ基準を `docs-ja/plans/p1-cpp-emitter-reduce.md` の決定ログに追記する。


## P3: test/misc 変換復旧（超低優先）

### 文脈
- `docs-ja/plans/p3-test-misc-transpile.md`
P3-MISC-01-S004 対象の `test/misc/04_maze_solver.py` は `py2cpp.py test/misc/04_maze_solver.py /tmp/04_maze_solver.cpp` が成功し、処理済み化の最終確認済み。

- 運用制約: `test/misc` 側の改変はしない。変換器/共通基盤の改善で対応し、難所は超低優先で後ろへ回す。

### タスク（S001〜S100）

1. [x] [ID: P3-MISC-01-S001] `test/misc/01_prime_reporter.py` を `py2cpp.py` で C++ 変換可能にする。
2. [x] [ID: P3-MISC-01-S002] `test/misc/02_text_analyzer.py` を `py2cpp.py` で C++ 変換可能にする。
3. [x] [ID: P3-MISC-01-S003] `test/misc/03_gradebook.py` を `py2cpp.py` で C++ 変換可能にする。
4. [x] [ID: P3-MISC-01-S004] `test/misc/04_maze_solver.py` を `py2cpp.py` で C++ 変換可能にする。
5. [x] [ID: P3-MISC-01-S005] `test/misc/05_sales_report.py` を `py2cpp.py` で C++ 変換可能にする。
6. [x] [ID: P3-MISC-01-S006] `test/misc/06_ascii_chart.py` を `py2cpp.py` で C++ 変換可能にする。
7. [ ] [ID: P3-MISC-01-S007] `test/misc/07_task_scheduler.py` を `py2cpp.py` で C++ 変換可能にする。
8. [ ] [ID: P3-MISC-01-S008] `test/misc/08_bank_account.py` を `py2cpp.py` で C++ 変換可能にする。
9. [ ] [ID: P3-MISC-01-S009] `test/misc/09_weather_simulator.py` を `py2cpp.py` で C++ 変換可能にする。
10. [ ] [ID: P3-MISC-01-S010] `test/misc/100_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
11. [ ] [ID: P3-MISC-01-S011] `test/misc/10_battle_simulation.py` を `py2cpp.py` で C++ 変換可能にする。
12. [ ] [ID: P3-MISC-01-S012] `test/misc/11_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
13. [ ] [ID: P3-MISC-01-S013] `test/misc/12_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
14. [ ] [ID: P3-MISC-01-S014] `test/misc/13_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
15. [ ] [ID: P3-MISC-01-S015] `test/misc/14_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
16. [ ] [ID: P3-MISC-01-S016] `test/misc/15_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
17. [ ] [ID: P3-MISC-01-S017] `test/misc/16_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
18. [ ] [ID: P3-MISC-01-S018] `test/misc/17_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
19. [ ] [ID: P3-MISC-01-S019] `test/misc/18_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
20. [ ] [ID: P3-MISC-01-S020] `test/misc/19_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
21. [ ] [ID: P3-MISC-01-S021] `test/misc/20_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
22. [ ] [ID: P3-MISC-01-S022] `test/misc/21_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
23. [ ] [ID: P3-MISC-01-S023] `test/misc/22_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
24. [ ] [ID: P3-MISC-01-S024] `test/misc/23_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
25. [ ] [ID: P3-MISC-01-S025] `test/misc/24_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
26. [ ] [ID: P3-MISC-01-S026] `test/misc/25_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
27. [ ] [ID: P3-MISC-01-S027] `test/misc/26_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
28. [ ] [ID: P3-MISC-01-S028] `test/misc/27_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
29. [ ] [ID: P3-MISC-01-S029] `test/misc/28_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
30. [ ] [ID: P3-MISC-01-S030] `test/misc/29_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
31. [ ] [ID: P3-MISC-01-S031] `test/misc/30_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
32. [ ] [ID: P3-MISC-01-S032] `test/misc/31_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
33. [ ] [ID: P3-MISC-01-S033] `test/misc/32_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
34. [ ] [ID: P3-MISC-01-S034] `test/misc/33_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
35. [ ] [ID: P3-MISC-01-S035] `test/misc/34_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
36. [ ] [ID: P3-MISC-01-S036] `test/misc/35_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
37. [ ] [ID: P3-MISC-01-S037] `test/misc/36_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
38. [ ] [ID: P3-MISC-01-S038] `test/misc/37_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
39. [ ] [ID: P3-MISC-01-S039] `test/misc/38_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
40. [ ] [ID: P3-MISC-01-S040] `test/misc/39_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
41. [ ] [ID: P3-MISC-01-S041] `test/misc/40_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
42. [ ] [ID: P3-MISC-01-S042] `test/misc/41_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
43. [ ] [ID: P3-MISC-01-S043] `test/misc/42_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
44. [ ] [ID: P3-MISC-01-S044] `test/misc/43_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
45. [ ] [ID: P3-MISC-01-S045] `test/misc/44_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
46. [ ] [ID: P3-MISC-01-S046] `test/misc/45_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
47. [ ] [ID: P3-MISC-01-S047] `test/misc/46_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
48. [ ] [ID: P3-MISC-01-S048] `test/misc/47_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
49. [ ] [ID: P3-MISC-01-S049] `test/misc/48_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
50. [ ] [ID: P3-MISC-01-S050] `test/misc/49_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
51. [ ] [ID: P3-MISC-01-S051] `test/misc/50_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
52. [ ] [ID: P3-MISC-01-S052] `test/misc/51_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
53. [ ] [ID: P3-MISC-01-S053] `test/misc/52_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
54. [ ] [ID: P3-MISC-01-S054] `test/misc/53_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
55. [ ] [ID: P3-MISC-01-S055] `test/misc/54_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
56. [ ] [ID: P3-MISC-01-S056] `test/misc/55_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
57. [ ] [ID: P3-MISC-01-S057] `test/misc/56_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
58. [ ] [ID: P3-MISC-01-S058] `test/misc/57_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
59. [ ] [ID: P3-MISC-01-S059] `test/misc/58_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
60. [ ] [ID: P3-MISC-01-S060] `test/misc/59_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
61. [ ] [ID: P3-MISC-01-S061] `test/misc/60_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
62. [ ] [ID: P3-MISC-01-S062] `test/misc/61_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
63. [ ] [ID: P3-MISC-01-S063] `test/misc/62_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
64. [ ] [ID: P3-MISC-01-S064] `test/misc/63_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
65. [ ] [ID: P3-MISC-01-S065] `test/misc/64_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
66. [ ] [ID: P3-MISC-01-S066] `test/misc/65_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
67. [ ] [ID: P3-MISC-01-S067] `test/misc/66_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
68. [ ] [ID: P3-MISC-01-S068] `test/misc/67_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
69. [ ] [ID: P3-MISC-01-S069] `test/misc/68_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
70. [ ] [ID: P3-MISC-01-S070] `test/misc/69_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
71. [ ] [ID: P3-MISC-01-S071] `test/misc/70_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
72. [ ] [ID: P3-MISC-01-S072] `test/misc/71_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
73. [ ] [ID: P3-MISC-01-S073] `test/misc/72_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
74. [ ] [ID: P3-MISC-01-S074] `test/misc/73_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
75. [ ] [ID: P3-MISC-01-S075] `test/misc/74_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
76. [ ] [ID: P3-MISC-01-S076] `test/misc/75_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
77. [ ] [ID: P3-MISC-01-S077] `test/misc/76_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
78. [ ] [ID: P3-MISC-01-S078] `test/misc/77_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
79. [ ] [ID: P3-MISC-01-S079] `test/misc/78_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
80. [ ] [ID: P3-MISC-01-S080] `test/misc/79_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
81. [ ] [ID: P3-MISC-01-S081] `test/misc/80_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
82. [ ] [ID: P3-MISC-01-S082] `test/misc/81_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
83. [ ] [ID: P3-MISC-01-S083] `test/misc/82_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
84. [ ] [ID: P3-MISC-01-S084] `test/misc/83_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
85. [ ] [ID: P3-MISC-01-S085] `test/misc/84_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
86. [ ] [ID: P3-MISC-01-S086] `test/misc/85_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
87. [ ] [ID: P3-MISC-01-S087] `test/misc/86_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
88. [ ] [ID: P3-MISC-01-S088] `test/misc/87_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
89. [ ] [ID: P3-MISC-01-S089] `test/misc/88_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
90. [ ] [ID: P3-MISC-01-S090] `test/misc/89_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
91. [ ] [ID: P3-MISC-01-S091] `test/misc/90_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
92. [ ] [ID: P3-MISC-01-S092] `test/misc/91_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
93. [ ] [ID: P3-MISC-01-S093] `test/misc/92_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
94. [ ] [ID: P3-MISC-01-S094] `test/misc/93_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
95. [ ] [ID: P3-MISC-01-S095] `test/misc/94_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。
96. [ ] [ID: P3-MISC-01-S096] `test/misc/95_pipeline_flow.py` を `py2cpp.py` で C++ 変換可能にする。
97. [ ] [ID: P3-MISC-01-S097] `test/misc/96_oceanic_timeseries.py` を `py2cpp.py` で C++ 変換可能にする。
98. [ ] [ID: P3-MISC-01-S098] `test/misc/97_token_grammar.py` を `py2cpp.py` で C++ 変換可能にする。
99. [ ] [ID: P3-MISC-01-S099] `test/misc/98_route_graph.py` を `py2cpp.py` で C++ 変換可能にする。
100. [ ] [ID: P3-MISC-01-S100] `test/misc/99_ledger_trace.py` を `py2cpp.py` で C++ 変換可能にする。

- 上記 100 タスクは超低優先（P3）として、時間の許容があるものから順次着手する。

- 進捗メモ:
  - [ID: P3-MISC-01-S005] `test/misc/05_sales_report.py` を `py2cpp.py` で変換成功（出力 `/tmp/05_sales_report.cpp` 生成確認）。
  - [ID: P3-MISC-01-S006] `test/misc/06_ascii_chart.py` を `py2cpp.py` で変換成功（出力 `/tmp/06_ascii_chart.cpp` 生成確認）。


## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs-ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs-ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。
