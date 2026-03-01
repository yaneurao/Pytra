# P0: sample/cpp/08 出力品質改善（可読性 + ホットパス縮退）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S08-QUALITY-01`

背景:
- `sample/cpp/08_langtons_ant.cpp` は動作は成立しているが、生成コード品質に改善余地が残る。
- 具体的には以下。
  - `grid` 初期化が IIFE + `py_repeat` で冗長。
  - `capture` で `bytes(frame)` 変換を行っており、`bytes` alias（`bytearray`）前提では不要な表現が残る。
  - 60万ステップのホットループで `%` を多用している。
  - `elif` 由来の分岐が深い入れ子 `if` になっている。
  - `frames` に `reserve` がなく、再確保コストが読めない。

目的:
- `sample/cpp/08` の生成コードを、同一意味を維持したまま可読性とホットパス効率の両面で改善する。

対象:
- `src/hooks/cpp/emitter/*`（stmt/expr/forcore/call 周辺）
- `src/pytra/compiler/east_parts/east3_opt_passes/*`（必要時）
- `test/unit/test_py2cpp_codegen_issues.py`
- `sample/cpp/08_langtons_ant.cpp`（再生成確認）

非対象:
- `sample/08` のアルゴリズム変更
- runtime ABI の破壊的変更
- `sample/08` 以外の全件一括最適化

受け入れ基準:
- `sample/cpp/08_langtons_ant.cpp` で次の5点が確認できる。
  1. `grid` 初期化が IIFE + `py_repeat` から簡潔な typed 初期化へ縮退する。
  2. `capture` の戻り値生成で不要な `bytes(frame)` 表現を削減する。
  3. ホットループの `%` 多用を削減する（少なくとも capture 判定の `%` をカウンタ方式へ置換）。
  4. 方向分岐が入れ子 `if` 連鎖から `else if`/`switch` 相当へ簡素化される。
  5. `frames` に事前 `reserve` を入れ、再確保を抑制する。
- `check_py2cpp_transpile` と関連 unit が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 src/py2cpp.py sample/py/08_langtons_ant.py -o sample/cpp/08_langtons_ant.cpp`

分解:
- [x] [ID: P0-CPP-S08-QUALITY-01-S1-01] `sample/cpp/08` の品質差分（初期化/変換/分岐/ループ/capacity）をコード断片で固定する。
- [x] [ID: P0-CPP-S08-QUALITY-01-S2-01] `grid` 初期化を IIFE + `py_repeat` から typed 直接初期化へ縮退する。
- [x] [ID: P0-CPP-S08-QUALITY-01-S2-02] `capture` 返却時の `bytes(frame)` を不要変換削減ルールで簡素化する。
- [ ] [ID: P0-CPP-S08-QUALITY-01-S2-03] capture 判定の `%` を next-capture カウンタ方式へ置換する fastpath を導入する。
- [x] [ID: P0-CPP-S08-QUALITY-01-S2-04] `if/elif/elif/else` 由来の入れ子分岐を `else if`/`switch` 相当の出力へ縮退する。
- [ ] [ID: P0-CPP-S08-QUALITY-01-S2-05] 事前に推定可能な `list` に `reserve` を出力する最小規則を追加し、`frames` へ適用する。
- [x] [ID: P0-CPP-S08-QUALITY-01-S3-01] 回帰テストを追加し、`sample/cpp/08` 再生成差分を固定する。
- [x] [ID: P0-CPP-S08-QUALITY-01-S3-02] transpile / unit / sample再生成確認を実施し、非退行を確認する。

決定ログ:
- 2026-03-01: ユーザー指示により、`sample/cpp/08` の改善項目を P0 計画として分解し TODO へ追加する方針を確定した。
- 2026-03-01: S1-01 として `sample/cpp/08_langtons_ant.cpp` の品質差分を固定した。主要断片: `grid` 初期化は `list<list<int64>> grid = [&]() -> ... py_repeat(...)`（冗長）、`capture` は `return bytes(frame);`（不要変換）、方向分岐は `else { if (...) { ... } else { if (...) ... } }`（入れ子）、`frames` は `list<bytes> frames = list<bytes>{};`（reserveなし）。
- 2026-03-01: S2-02 として `src/hooks/cpp/emitter/runtime_expr.py` の `bytes_ctor` に `bytes/bytearray` 既知経路の縮退を追加し、`bytes(x)` を `x` に簡素化した。
- 2026-03-01: S2-04 として `src/hooks/cpp/emitter/stmt.py` の If 出力を改善し、`else: if ...` 連鎖を `else if (...)` へ平坦化した。
- 2026-03-01: S2-01 として `src/hooks/cpp/emitter/collection_expr.py` に `[[seed] * cols for _ in range(rows)]` の typed fill ctor fastpath を追加し、`sample/cpp/08` の `grid` 初期化を `list<list<int64>>(h, list<int64>(w, 0))` へ縮退した（`sample13` の同型初期化にも適用）。
- 2026-03-01: S3-01 として `test/unit/test_py2cpp_codegen_issues.py` に `sample08` 回帰2件（`else if` 連鎖、`return frame;`）を追加した。
- 2026-03-01: S3-02 として `python3 src/py2cpp.py sample/py/08_langtons_ant.py -o sample/cpp/08_langtons_ant.cpp`、`PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`（91 tests, OK）、`python3 tools/check_py2cpp_transpile.py`（checked=135, ok=135）を確認した。
