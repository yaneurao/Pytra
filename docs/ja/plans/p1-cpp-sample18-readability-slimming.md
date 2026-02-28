# P1: sample/18 C++ 生成コード可読性縮退（選定: #2,#7,#8,#5,#1）

最終更新: 2026-02-27

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-CPP-S18-READ-01`

背景:
- `sample/18_mini_language_interpreter` の C++ 生成コードは、動作互換優先の fallback が重なり、`object` 経由や冗長変換が多く可読性が低い。
- 特にユーザー選定の改善項目 #2, #7, #8, #5, #1（cast 縮退、map key 変換縮退、timing 変換簡約、type decay 抑制、typed loop header）が優先対象。
- 既存 `P0-FORCORE-TYPE-01` は #1 の基盤タスクを扱っているため、本タスクではその成果を可読性改善セットへ接続する。

目的:
- `sample/18` の C++ 生成コードで、選定 5 項目の冗長性を段階的に削減する。
- 生成コードの読みやすさを上げつつ、コンパイル可否と parity を維持する。

対象:
- `src/hooks/cpp/emitter/stmt.py`
- `src/hooks/cpp/emitter/expr.py`
- `src/hooks/cpp/emitter/*`（必要な範囲）
- `test/unit/test_east3_cpp_bridge.py`
- `test/unit/test_py2cpp_smoke.py`
- `sample/cpp/18_mini_language_interpreter.cpp`（再生成結果確認）

非対象:
- C++ runtime の全面再設計
- EAST3 最適化層の新規導入
- `sample/18` 以外の全面的な出力最適化

受け入れ基準:
- 改善項目 #2, #7, #8, #5, #1 の各タスクが個別に検証可能な形で実装されている。
- `sample/18` 生成結果で対象箇所の冗長パターンが削減されている。
- `check_py2cpp_transpile.py` / 関連 unit test / `sample/18` コンパイルが通る。
- `P0-FORCORE-TYPE-01-S3-01` と競合せず、#1 の適用状態が文書で追跡できる。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_cpp_bridge.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 src/py2cpp.py sample/py/18_mini_language_interpreter.py -o /tmp/18.cpp`

決定ログ:
- 2026-02-27: ユーザー指定（`2,7,8,5,1`）に従い、`sample/18` C++ 可読性改善を `P1-CPP-S18-READ-01` として起票。
- 2026-02-27: 改善項目 #1 は既存 `P0-FORCORE-TYPE-01-S3-01` と整合管理し、重複実装を避ける方針を確定。
- 2026-02-28: `ForCore(RuntimeIterForPlan)+NameTarget` に typed iterable 経路を追加し、`list[T]` 既知時は `py_dyn_range + Unbox` ではなく typed loop header を採用する方針で `sample/18` の `for stmt in stmts` 冗長 cast を削減。
- 2026-02-28: `test_east3_cpp_bridge.py`（85件）、`check_py2cpp_transpile.py`（`checked=133 ok=133 fail=0 skipped=6`）、`runtime_parity_check.py --case-root sample 18_mini_language_interpreter --targets cpp`（pass）で回帰確認した。
- 2026-02-28: `dict_key_verified` の dict load/store 経路を `test_east3_cpp_bridge.py` に追加し、`sample/18` 再生成で `env[stmt->name]` が維持されることを確認して key 変換連鎖の再発を防止した。
- 2026-02-28: `core.py` の `BuiltinCall(perf_counter)` を `resolved_type=float64` で固定し、`sample/18` の `start/elapsed` で `py_to<float64>` が不要になることを `test_py2cpp_codegen_issues.py` / parity で確認した。
- 2026-02-28: return 経路に空 collection literal の型寄せ補正（`_rewrite_empty_collection_literal_for_typed_target`）を追加し、`new_expr_nodes() -> list[ExprNode]` で `list<object>{}` へ減衰しないことを回帰固定した。

## 分解

- [x] [ID: P1-CPP-S18-READ-01-S1-02] 改善項目 #2: tuple unpack / 一時変数周辺の冗長 cast を削減する。
- [x] [ID: P1-CPP-S18-READ-01-S1-07] 改善項目 #7: `map` キーアクセス時の不要な key 変換連鎖を縮退する。
- [x] [ID: P1-CPP-S18-READ-01-S1-08] 改善項目 #8: timing/elapsed 計算まわりの数値変換チェーンを簡約する。
- [x] [ID: P1-CPP-S18-READ-01-S1-05] 改善項目 #5: `unknown` 起点の過剰 default 初期化・型減衰を抑制する。
- [ ] [ID: P1-CPP-S18-READ-01-S1-01] 改善項目 #1: typed loop header 化の成果を `sample/18` 出力へ統合する（`P0-FORCORE-TYPE-01-S3-01` 依存）。
