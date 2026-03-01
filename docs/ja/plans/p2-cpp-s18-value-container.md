# P2: sample/18 C++ AST コンテナ値型化（`list<rc<T>>` -> `list<T>`）

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-CPP-S18-VALUE-CONTAINER-01`

背景:
- sample/18 の AST 保持は `list<rc<ExprNode>>` / `list<rc<StmtNode>>` で表現され、読み取り主体の経路でも `rc` 操作が発生している。
- non-escape 条件を満たす局所コンテナなら値型保持へ縮退できる余地があるが、現行は安全側で参照管理に寄っている。
- この改善は所有権/寿命判定が絡むため、即時 `P0` ではなく設計と段階導入が必要。

目的:
- EAST3 非escape情報を活用し、sample/18 の AST コンテナを値型へ段階的に縮退できる道筋を作る。

対象:
- EAST3 non-escape メタと container ownership hint の連携設計
- C++ emitter のコンテナ型選択規則（`rc`/値型の分岐）
- sample/18 先行導入と回帰固定

非対象:
- 全 backend への同時展開
- `PyObj` / `rc` ランタイムモデルの全面置換

受け入れ基準:
- sample/18 の `expr_nodes` / `stmts` で値型化可能条件が仕様化される。
- 条件を満たさない経路は従来どおり `rc` を維持し、fail-closed で後退しない。
- 段階導入後に unit/transpile/parity で非退行が確認できる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

決定ログ:
- 2026-03-01: ユーザー指示により、sample/18 の AST コンテナ値型化を `P2` 計画として起票した。

## 分解

- [ ] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S1-01] sample/18 の AST コンテナ利用点を棚卸しし、値型化可能な non-escape 条件を定義する。
- [ ] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S1-02] EAST3 メタ（ownership hint / non-escape）と C++ emitter 連携仕様を設計する。
- [ ] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S2-01] sample/18 先行で `expr_nodes` / `stmts` の値型出力を実装する。
- [ ] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S2-02] 逸脱ケースでは `rc` へ自動フォールバックする fail-closed 条件を実装する。
- [ ] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S3-01] 回帰テスト（型出力断片 + 実行整合）を追加し、再発検知を固定する。
