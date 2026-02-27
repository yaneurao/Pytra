# P0: EAST3最適化層の強化（sample C++ 出力改善）

最終更新: 2026-02-27

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-EAST3-OPT-SAMPLE-CPP-01`

背景:
- `sample/cpp` の出力には、EAST3 段で吸収可能な冗長パターン（`object` 経由反復、冗長 `py_to<T>`、汎用 `range` 条件式、`make_object(py_repeat(...))` 等）が残っている。
- 現行 optimizer v1 は fail-closed で適用範囲が狭く、`sample/18` などで可読性と実行時コストに直結するノイズが十分に削れていない。
- C++ emitter 側だけで都度対処すると backend 依存ロジックが肥大化するため、共通化可能な部分は EAST3 最適化層へ寄せる必要がある。

目的:
- `sample/cpp` の主要ケースで目立つ冗長変換を EAST3 段で前処理し、C++ emitter 出力の可読性・効率を改善する。

対象:
- `src/pytra/compiler/east_parts/east3_opt_passes/*.py`
- `src/pytra/compiler/east_parts/east3_optimizer.py`（pass 登録/順序）
- EAST3 optimizer 単体テスト・CLIテスト
- 必要最小限の `sample/cpp` 生成確認

非対象:
- C++ emitter 固有の最終整形（括弧整形、命名スタイル変更）
- 意味変化を伴う aggressive 最適化
- C++ 以外 backend 固有のコードスタイル改善

受け入れ基準:
- 7サブタスクそれぞれについて、対応 pass（または既存 pass 拡張）が実装され、無効化可能な形で optimizer 管理下に入る。
- `sample/05,06,07,09,13,14,16,18` の再変換で、対象パターンの少なくとも一部が縮退していることを確認できる。
- `--east3-opt-level 0/1/2` の切替で意味差が発生しない（既存 parity 手順で回帰なし）。

確認コマンド:
- `python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`
- `python3 -m unittest discover -s test/unit -p 'test_east3_optimizer_cli.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --all-samples --ignore-unstable-stdout`

決定ログ:
- 2026-02-27: `sample/cpp` 実出力レビューに基づき、EAST3最適化層で先に吸収すべき7項目（range正規化拡張、typed enumerate、cast-chain縮退、loop invariant hoist拡張、typed repeat、dict key cast削減、tuple unpack直展開）を P0 として起票。

## 分解

- [ ] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-01] `RangeForCanonicalizationPass` 拡張（`stop` 非定数 + `step` 定数対応）を実装し、`for (...; N>0 ? ... : ...)` 形の発生を抑制する。
- [ ] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-02] `enumerate(list[T])` の typed 反復正規化を実装し、`object + py_at + py_to` 連鎖を縮退する。
- [ ] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-03] 数値 cast-chain 縮退 pass を追加し、型既知 `py_to<T>` の連鎖を削減する。
- [ ] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-04] ループ不変な型変換/分母の hoist を実装し、内側ループの反復処理を軽量化する。
- [ ] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-05] 型既知 `py_repeat` 初期化の typed materialization 正規化を実装する。
- [ ] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-06] `dict<str, V>` キー経路の不要 `to_string` 縮退を実装する。
- [ ] [ID: P0-EAST3-OPT-SAMPLE-CPP-01-S1-07] tuple unpack 一時変数の消し込み（`TupleTarget` 直展開）を実装する。
