# P0: `range(len-1, -1, -1)` 多言語回帰（test追加 + 全backend通過）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-MULTILANG-DOWNRANGE-01`

背景:
- C# selfhost 化の文脈で、`range(len-1, -1, -1)`（ダウンカウント range）が正しく動作しないケースが確認された。
- 追加調査で、同型不具合が `js/ts/rs` にも存在することを確認した（`ForCore -> ForRange` 変換時の mode 解決不整合）。
- 現状このケースを固定する共通回帰テストが `test/` に存在せず、再発検知ができない。

目的:
- `test/` にダウンカウント range の共通ケースを追加し、全バックエンドで変換・実行（可能な範囲）を通す。
- `ForCore(StaticRangeForPlan)` の mode 解決を backend 間で統一し、`range(len-1, -1, -1)` を正しく処理する。

対象:
- `test/fixtures/*`（新規ケース追加）
- `test/unit/test_py2cs_smoke.py`
- `test/unit/test_py2js_smoke.py`
- `test/unit/test_py2ts_smoke.py`
- `test/unit/test_py2rs_smoke.py`
- `src/hooks/cs/emitter/cs_emitter.py`
- `src/hooks/js/emitter/js_emitter.py`
- `src/hooks/rs/emitter/rs_emitter.py`
- `src/pytra/compiler/east_parts/code_emitter.py`（必要時: 共通 mode 解決 helper）
- `tools/runtime_parity_check.py`（必要時: 新規fixture導線）

非対象:
- 既存 sample 全件の性能最適化
- `range` 以外の loop 仕様変更
- backend ごとのスタイル最適化（括弧/整形）

受け入れ基準:
- `range(len-1, -1, -1)` を含む共通 fixture が `test/` に追加される。
- `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua` の各変換器で当該 fixture の transpile が成功する。
- 実行対象 backend（CI/ローカルで toolchain があるもの）で期待値一致（例: `sum_rev([1,2,3]) == 6`）を確認する。
- `cs/js/ts/rs` で生成されるループ条件が誤った ascending 条件（`i < -1`）にならない。
- 既存の transpile/smoke/parity 導線が非退行で通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/check_py2lua_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2*smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root fixture --targets cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua <new_case> --ignore-unstable-stdout`

分解:
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S1-01] `range(len-1, -1, -1)` の最小 fixture を `test/fixtures` に追加し、期待出力を固定する。
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S1-02] 現状の失敗バックエンド（`cs/js/ts/rs`）と成功バックエンドを再現ログとして記録する。
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S2-01] `ForCore(StaticRangeForPlan)` の range mode 解決を共通化し、`iter_plan` 非保持時は `step` から descending/ascending/dynamic を導出する。
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S2-02] `cs/js/rs` emitter の `ForCore -> ForRange` 変換で `range_mode='ascending'` 固定フォールバックを撤去し、共通解決結果を使う。
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S2-03] `ts`（JS preview経路）に同ケース回帰を追加し、`js` 修正が確実に反映されることを固定する。
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S3-01] 各 backend smoke/transpile テストへ当該 fixture ケースを追加し、再発検知を常時化する。
- [x] [ID: P0-MULTILANG-DOWNRANGE-01-S3-02] runtime parity（実行可能ターゲット）で期待値一致を確認し、結果を決定ログへ記録する。

決定ログ:
- 2026-03-01: ユーザー指示により、`range(len-1, -1, -1)` の多言語回帰を P0 として起票し、test追加 + 全backend通過を最優先で進める方針を確定した。
- 2026-03-01: 最小 fixture `test/fixtures/control/range_downcount_len_minus1.py` を追加し、`py_assert_stdout` 依存を除いた単純出力ケース（期待値 `10`）へ固定した。
- 2026-03-01: `CodeEmitter.resolve_forcore_static_range_mode()` を追加し、`iter_plan.range_mode` 欠落時も `step` 定数から `ascending/descending/dynamic` を決定する共通経路を実装した。
- 2026-03-01: `cs/js/rs` の `ForCore -> ForRange` 変換で `range_mode='ascending'` 固定を撤去し、共通 mode 解決結果を利用するよう変更した。`dynamic` 時は `step` 符号分岐条件を生成する。
- 2026-03-01: `ts`（JS preview）に downcount 回帰を追加し、`for (...; i > -1; ... )` が出ることを固定した。
- 2026-03-01: parity 実行で Lua に負 step の stop 境界 off-by-one（`stop-1`）が見つかったため、Lua emitter の `static_fastpath` を `descending => stop+1` に修正し、`dynamic` step 分岐も追加した。
- 2026-03-01: 検証結果
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2js_smoke.py' -v` pass（22）
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2ts_smoke.py' -v` pass（15）
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cs_smoke.py' -v` pass（44）
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs_smoke.py' -v` pass（29）
  - `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua_smoke.py' -v` pass（19）
  - `python3 tools/runtime_parity_check.py --case-root fixture --targets cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua range_downcount_len_minus1` pass（ok=10, swift=toolchain_missing）
