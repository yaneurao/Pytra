# P0: EAST3式正規化ロールアウト（multi-backend共通化）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EAST3-EXPR-NORM-ROLL-01`

背景:
- 現状は各 backend emitter（`cpp/rs/cs/js/go/java/swift/kotlin/ruby/lua/scala`）が二項演算・比較・range 条件などの式を個別に文字列組み立てしている。
- その結果、同一意味の式でも backend ごとに冗長表現が混在し、簡約漏れ（不要括弧、identity cast、`start=0` / `step=1` の一般式残存）が発生しやすい。
- 既存の `P0-EAST3-RESERVE-COUNT-NORM-01` は `reserve` 件数式に限定した対策であり、同様の問題は他式カテゴリにも残っている。

目的:
- backend 共通で扱える式の意味決定を EAST3 側へ寄せ、emitter は言語固有表記の描画に集中させる。
- 「正規化責務はEAST3、表記責務はemitter」の境界を明文化し、冗長式の再発を抑止する。

対象:
- EAST3 optimizer / lowering の式正規化パス（新設含む）
- `src/hooks/*/emitter` の共通式組み立て経路（BinOp/Compare/ForRange条件/trip_count等）
- 回帰テスト（optimizer + 各backend codegen断片）
- `sample` 再生成での代表ケース差分確認（`01/08/18` を優先）

非対象:
- 各言語固有機能の表記最適化（例: `format!`, `Math.floor` の具体API選択）
- runtime API 再設計
- backend 全面同時切替（段階導入を前提）

受け入れ基準:
- EAST3 に「共通式正規化メタ/ノード」が導入され、少なくとも `BinOp/Compare/StaticRange条件` の共通形が保持される。
- emitter 側の共通式文字列組み立てロジックが段階的に縮小され、EAST3正規形描画へ置換される。
- `sample/cpp/18` を含む代表ケースで冗長式（不要括弧/identity cast/一般式残存）が減る。
- `check_*_transpile` と関連 unit が非退行で通る。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp,rs,scala --stems 01_mandelbrot,08_langtons_ant,18_mini_language_interpreter --force`

分解:
- [ ] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S1-01] backend 横断で式組み立て責務の棚卸し（BinOp/Compare/ForRange/trip_count）を行い、EAST3移管対象を確定する。
- [ ] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S1-02] 「EAST3が決める意味」と「emitterが決める表記」の境界仕様を策定する（fail-closed 条件含む）。
- [ ] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S1-03] 正規化対象カテゴリ（identity cast、不要括弧、range条件、trip_count、比較連鎖）の優先順位を固定する。
- [ ] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S2-01] EAST3に共通式正規化パスを追加し、正規化結果を構造化メタ（`normalized_expr` 系）として保持する。
- [ ] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S2-02] C++ emitter で `reserve` 以外の式カテゴリも EAST3正規形優先に切替え、文字列組み立て依存を縮小する。
- [ ] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S2-03] Rust/Scala を次段 pilot として同一正規形を参照する描画経路へ切替える。
- [ ] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S2-04] 旧経路との併存期間を最小化し、正規形欠落時の fail-closed / fallback 条件を固定する。
- [ ] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S3-01] unit テスト（optimizer + emitter）を追加し、冗長式再発を検知可能にする。
- [ ] [ID: P0-EAST3-EXPR-NORM-ROLL-01-S3-02] `sample` 再生成と transpile/parity を実施し、代表ケースでの品質改善と非退行を確認する。

決定ログ:
- 2026-03-02: ユーザー指示により、`reserve` 限定でなく式正規化全体を EAST3 側へ寄せる P0 計画を新規起票。
