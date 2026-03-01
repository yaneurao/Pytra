# P0: EAST3 主導の安全 `reserve` ヒント導入（無条件 append + 確定ループのみ）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EAST3-SAFE-RESERVE-01`

背景:
- 現行 C++ emitter には、`if i % k == 0: append(...)` 形を `next-capture` へ書き換える際に `reserve` を自動挿入する経路がある。
- この見積もりは `ceil(stop/k)` ベースで、同じ配列に無条件 `append` が混在するケースで過小/過大推定を起こし得る。
- ユーザー要件として「`reserve` は `if` 条件付き append では行わない」「無条件 append かつループ回数がループ前に確定する場合のみ行う」が明示された。

目的:
- `reserve` 出力判定を emitter の場当たり推定から外し、EAST3 側で安全に確定できる場合のみヒントを付与する。
- C++ emitter は EAST3 ヒントがあるときだけ `reserve` を出力し、ヒント不在時は出力しない。

対象:
- EAST3 optimizer pass による `ForCore(StaticRangeForPlan)` 解析
- `reserve` ヒントのノードメタ設計（`iter_plan` 付帯 or stmt-level metadata）
- C++ emitter の `reserve` 出力経路をヒント依存へ切り替え
- `sample/18` を含む回帰テスト更新

非対象:
- `if` 条件付き append の確率推定（ヒューリスティック）
- EAST3 以外 backend の `reserve` 最適化
- append 以外（dict/set）の事前容量最適化

受け入れ基準:
- 条件付き append (`if ...: xs.append(...)`) では `reserve` が一切出力されないこと。
- 無条件 append かつループ回数が事前確定可能な `StaticRangeForPlan` のみ `reserve` が出力されること。
- `sample/cpp/18_mini_language_interpreter.cpp` で不適切 `reserve` が消えること。
- `test_py2cpp_codegen_issues.py` と `tools/check_py2cpp_transpile.py` が通過すること。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --stems 18_mini_language_interpreter --force --verbose`

決定ログ:
- 2026-03-01: ユーザー指示により、`reserve` は「無条件 append + ループ回数事前確定」条件でのみ有効化し、判定責務を EAST3 側へ移す `P0` 計画を起票した。
- 2026-03-01: S1-01/S1-02 として `SafeReserveHintPass` の適格条件を「StaticRangeForPlan + 単純不変境界 + top-level 無条件 append 1件 + 制御フローなし」に固定し、ヒント形を stmt-level `reserve_hints`（kind/owner/count_kind/safe/safety）へ確定した。
- 2026-03-01: S2-01/S2-02 として EAST3 optimizer に `SafeReserveHintPass` を追加し、C++ emitter の capture 由来 `reserve` 自動挿入を撤去して `reserve_hints` 依存へ切り替えた。
- 2026-03-01: S3-01/S3-02 として sample/cpp 08/18 再生成、`test_east3_optimizer.py`・`test_py2cpp_codegen_issues.py`・`check_py2cpp_transpile.py` を通過させ、条件付き append 由来 `reserve` 非出力を確認した。

## 分解

- [x] [ID: P0-EAST3-SAFE-RESERVE-01-S1-01] EAST3 で `reserve` 対象とする ForCore 条件（無条件 append / 静的 range / loop内で stop不変）を仕様化する。
- [x] [ID: P0-EAST3-SAFE-RESERVE-01-S1-02] `reserve` ヒントのデータ形（owner名・推定件数式・安全性フラグ）を EAST3 ノードに定義する。
- [x] [ID: P0-EAST3-SAFE-RESERVE-01-S2-01] EAST3 optimizer pass を追加し、適格ループにのみ `reserve` ヒントを付与する。
- [x] [ID: P0-EAST3-SAFE-RESERVE-01-S2-02] C++ emitter の現行 `capture` 由来 `reserve` 推定を撤去し、EAST3 ヒント参照に切り替える。
- [x] [ID: P0-EAST3-SAFE-RESERVE-01-S3-01] `sample/18` の再生成で不適切 `reserve` 非出力を固定し、回帰テストを更新する。
- [x] [ID: P0-EAST3-SAFE-RESERVE-01-S3-02] `test_py2cpp_codegen_issues.py` / `check_py2cpp_transpile.py` で非退行を確認する。
