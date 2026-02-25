# TASK GROUP: TG-P3-MISC-CONV

最終更新: 2026-02-25

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P3-MISC-01`

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
  `docs-ja/todo/index.md` の該当チェックを完了済みに更新。
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

### 分解
