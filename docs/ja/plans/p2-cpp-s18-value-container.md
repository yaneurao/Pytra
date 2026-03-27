<a href="../../en/plans/p2-cpp-s18-value-container.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: sample/18 C++ AST コンテナ値型化（`list<rc<T>>` -> `list<T>`）

最終更新: 2026-03-02

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
- 2026-03-02: S1-01 として sample/18 の AST コンテナ利用点を棚卸しし、`expr_nodes`/`stmts` は `append` + 読み取り専用（index/for）で使われ、`object/Any` 境界へ要素が流出しないことを確認した。
- 2026-03-02: S1-02 として EAST3→CppEmitter 連携仕様を設計。`container_ownership_hint_v1`（候補名）を `AnnAssign`/`FunctionDef` の list 型宣言点へ付与し、値型条件を満たすときのみ `list<T>` を選択、逸脱時は既存 `list<rc<T>>` へ fail-closed で戻す方針を確定した。
- 2026-03-02: S2-01/S2-02 として dataclass の保守的 value 候補判定を `core.py` に導入し、`cpp_list_model=pyobj` でも `list[ValueClass]` を typed container として維持する分岐を `type_bridge.py` に追加した。`sample/18` で `Token/ExprNode/StmtNode` が `list<T>` 出力へ縮退し、unsafe 条件は既存 `ref` fallback を維持する。
- 2026-03-02: S3-01 として `test_east_core.py`（dataclass value/ref 境界）および `test_py2cpp_codegen_issues.py`（sample18 の値型出力断片）を更新し、`check_py2cpp_transpile` と parity（case18, cpp）で非退行を確認した。

## S1-01 棚卸し結果（sample/18）

- `Parser.expr_nodes`:
  - 宣言: `self.expr_nodes: list[ExprNode]`
  - 書き込み: `add_expr()` の `append` のみ
  - 読み取り: `eval_expr()` の index 参照のみ
  - 逃避: `Parser` インスタンスのメンバとして保持し、`execute()` 呼び出し時に list 自体を引数で渡す（要素単位で object 化しない）
- `stmts`:
  - 宣言: `parse_program() -> list[StmtNode]`
  - 書き込み: `parse_program()` の `append` のみ
  - 読み取り: `execute()` の for-each 参照のみ
  - 逃避: list 自体を返却して即時利用（要素単位で object 化しない）
- 非値型化トリガ（fail-closed 条件）:
  - 要素型が `object/Any/union` を含む
  - 要素が `object` 文脈へ渡される（boxing/unboxing 必須）
  - list 要素参照が可変 alias として外部関数へ escape する
  - 宣言点型と実際の要素型が一致しない

## S1-02 連携仕様（設計）

- EAST3 側:
  - 宣言点に `container_ownership_hint_v1` を付与する。
  - 最小スキーマ案:
    - `version`: `"1"`
    - `owner_name`: 変数名
    - `container_type`: 例 `list[ExprNode]`
    - `element_storage`: `"value" | "ref"`
    - `safe`: `true|false`
    - `reason`: 判定理由（デバッグ用）
  - `safe=true` は non-escape 条件 + 型一致が成立したケースのみ。
- CppEmitter 側:
  - `safe=true` かつ `element_storage=value` のときだけ container 宣言型を `list<T>` に切替える。
  - hint 不在/不整合/`safe=false` は既存挙動（`list<rc<T>>`）へ戻す。
  - 関数引数/戻り値も同じ hint 契約で判定し、片側のみ値型化は行わない。
- 段階導入:
  - 先行対象は sample/18 の `expr_nodes` / `stmts` のみ。
  - 汎化は S2/S3 で回帰を積み上げてから実施する。

## 分解

- [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S1-01] sample/18 の AST コンテナ利用点を棚卸しし、値型化可能な non-escape 条件を定義する。
- [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S1-02] EAST3 メタ（ownership hint / non-escape）と C++ emitter 連携仕様を設計する。
- [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S2-01] sample/18 先行で `expr_nodes` / `stmts` の値型出力を実装する。
- [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S2-02] 逸脱ケースでは `rc` へ自動フォールバックする fail-closed 条件を実装する。
- [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S3-01] 回帰テスト（型出力断片 + 実行整合）を追加し、再発検知を固定する。
