# P0: C++ `rc_new` 同型 cast 冗長除去（最優先）

最終更新: 2026-02-28

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-RCNEW-SAMECAST-01`

背景:
- `sample/18` の C++ 生成コードで `tokens.append(rc<Token>(::rc_new<Token>(...)));` のような二重表現が出力され、可読性を悪化させている。
- `::rc_new<T>(...)` は runtime 定義上すでに `rc<T>` を返すため、外側 `rc<T>(...)` は同型 cast として冗長。
- 現状の同型 cast 省略判定は描画済み式の型推論に依存しており、`::rc_new<T>(...)` 形式の戻り型を十分に推論できない。

目的:
- C++ 出力で `rc<T>(::rc_new<T>(...))` を `::rc_new<T>(...)` へ簡約し、同型 cast を恒久的に除去する。
- 省略判定を局所パッチではなく emitter の共通規約として固定し、再発を防ぐ。

対象:
- `src/pytra/compiler/east_parts/code_emitter.py`（描画済み式の型推論補強）
- `src/hooks/cpp/emitter/analysis.py`（同型 cast 省略判定）
- `src/hooks/cpp/emitter/call.py`（append 経路の cast 適用）
- `test/unit/test_py2cpp_codegen_issues.py` / `test/unit/test_east3_cpp_bridge.py` の回帰テスト
- `sample/cpp/18_mini_language_interpreter.cpp`（再生成確認）

非対象:
- `Token::rc_new()` などクラス static builder API の追加
- `rc`/runtime メモリモデルの変更
- C++ backend 全体の可読性最適化（別タスク）

受け入れ基準:
- `sample/18` に `rc<Token>(::rc_new<Token>(` が残存しない。
- `::rc_new<T>(...)` の戻り型を `rc<T>` と扱える回帰テストを追加し、同型 cast が再発しない。
- `python3 tools/check_py2cpp_transpile.py` と対象 unit/smoke が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py' -v`
- `python3 tools/regenerate_samples.py --langs cpp --force`

決定ログ:
- 2026-02-28: ユーザー指示により、`Token::rc_new` 方式ではなく `rc<T>(::rc_new<T>(...))` の冗長同型 cast 除去を P0 で先行実施する方針を確定した。
- 2026-02-28: `infer_rendered_arg_type()` に `::rc_new<T>(...)` 形の推論を追加し、`should_skip_same_type_cast` は `rc<T>` ラッパ差分を正規化して同型判定するよう更新した。
- 2026-02-28: `list.append` の typed 経路で同型 cast 省略判定を適用し、`sample/18` の `tokens.append(rc<Token>(::rc_new<Token>(...)))` を `tokens.append(::rc_new<Token>(...))` へ簡約した。
- 2026-02-28: 実施検証 `test_py2cpp_codegen_issues.py` / `test_east3_cpp_bridge.py` / `tools/check_py2cpp_transpile.py` / `tools/regenerate_samples.py --langs cpp --force` / `tools/runtime_parity_check.py --targets cpp 18_mini_language_interpreter` を通過した。

## 分解

- [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S1-01] `infer_rendered_arg_type()` で `::rc_new<T>(...)` を `rc<T>` と推論できる規約を追加する。
- [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S1-02] 同型 cast 省略判定（`should_skip_same_type_cast`）が上記推論結果を利用して `rc<T>(::rc_new<T>(...))` を no-op 判定できるようにする。
- [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S2-01] C++ cast 適用経路（`apply_cast` 周辺）で `rc_new` 起点の同型 cast が実際に落ちることを回帰テストで固定する。
- [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S2-02] `sample/cpp` を再生成し、`sample/18` の該当断片が `::rc_new<Token>(...)` へ簡約されることを確認する。
- [x] [ID: P0-CPP-RCNEW-SAMECAST-01-S3-01] `check_py2cpp_transpile` と smoke を実行して非退行を確認し、決定ログへ結果を記録する。
