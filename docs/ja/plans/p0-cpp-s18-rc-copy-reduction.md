# P0: sample/18 C++ `rc` 不要コピー削減

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-CPP-S18-RC-COPY-02`

背景:
- `sample/cpp/18_mini_language_interpreter.cpp` では `for (rc<StmtNode> stmt : stmts)` や `rc<ExprNode> node = expr_nodes[idx]` が残り、`rc` の参照カウント増減が過剰に発生している。
- これらの多くは読み取り専用経路で、`const rc<T>&`（または `const auto&`）に置換可能。
- ループ/再帰評価ホットパスのため、可読性と実行効率の両方に影響する。

目的:
- sample/18 の読み取り専用 `rc` 経路を参照受けへ寄せ、不要な `rc` コピーと refcount churn を削減する。

対象:
- C++ emitter の range-for 出力規則（`rc` 要素時の参照受け）
- 添字アクセス後の一時 `rc` 束縛規則（読み取り専用推定時）
- sample/18 固有の回帰テスト

非対象:
- 所有権移動（move）を伴う書き換え
- `rc` モデル自体の変更（値型化）

受け入れ基準:
- sample/18 で `for (rc<StmtNode> stmt : stmts)` が `const` 参照形に縮退する。
- `eval_expr` 系の読み取り専用ノード束縛で不要な `rc` コピーが削減される。
- 既存の意味（寿命・参照整合）を壊さず、unit/transpile 回帰が通る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/regenerate_samples.py --langs cpp --stems 18_mini_language_interpreter --force --verbose`

決定ログ:
- 2026-03-01: ユーザー指示により、sample/18 の `rc` 不要コピー削減を `P0` で起票した。

## 分解

- [ ] [ID: P0-CPP-S18-RC-COPY-02-S1-01] sample/18 の `rc` コピー発生点（range-for / 添字一時束縛）を棚卸しし、参照化可能条件を定義する。
- [ ] [ID: P0-CPP-S18-RC-COPY-02-S2-01] C++ emitter の for/一時束縛出力を更新し、読み取り専用経路を `const` 参照へ縮退する。
- [ ] [ID: P0-CPP-S18-RC-COPY-02-S2-02] 回帰テストを追加し、`rc` 値コピー再発を検知する。
- [ ] [ID: P0-CPP-S18-RC-COPY-02-S3-01] sample/18 再生成と transpile 回帰で非退行を確認する。
