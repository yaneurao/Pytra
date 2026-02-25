# P2: C++ selfhost virtual ディスパッチ簡略化

## 背景

`virtual`/`override` の扱いを現在のクラスモデルへ寄せたため、`cpp` selfhost 生成コードの一部で使われていた手作り分岐（`type_id` 判定 + switch 相当）を簡素化できる余地があります。
このままでも動作は維持できますが、簡略化すれば selfhost 出力の可読性・保守性・デバッグ性が向上します。

## 受け入れ基準

- selfhost 生成 C++ 側（`sample/` 系の再変換含む）で、同一メソッド呼び出しを `virtual` 経由へ置換して、`type_id` 分岐が不要な箇所を減らせること。
- `py2cpp.py` と `CppEmitter` が、`override` が付与される基底メソッドと同名呼び出しを前提に最小限の分岐で生成できること。
- `tools/check_selfhost_cpp_diff.py` / `tools/verify_selfhost_end_to_end.py` で回帰が発生しないこと。

## 子タスク

### S1: 事前スコーピング

1. `P2-CPP-SELFHOST-VIRTUAL-01-S1-01`: `src`/`sample`/`test` を対象に、`type_id` 判定付きの class method 呼び出し生成（`if (...) >= ... && ... <= ...` や `switch`）を `rg` と簡易 AST で抽出する。
2. `P2-CPP-SELFHOST-VIRTUAL-01-S1-02`: 抽出結果を「基底クラス呼び出し」「再帰呼び出し」「共通ユーティリティ呼び出し」に分類し、対象外ケースを明文化する。
3. `P2-CPP-SELFHOST-VIRTUAL-01-S1-03`: `virtual` 適用対象として `override` 付き系メソッド呼び出しに限定できる候補を優先順（安全性・影響範囲）で並べる。

`P2-CPP-SELFHOST-VIRTUAL-01-S1-01` 確定内容（2026-02-25）:
- `rg` 走査:
  - `rg -n "type_id\\(\\).*>=.*&&.*type_id\\(\\).*<=" sample src test`
  - `rg -n "switch \\(.*type_id\\(" sample src test`
  - `rg --count-matches "type_id\\(\\)\\s*[<>=!]+" sample/cpp src/runtime/cpp/pytra-gen src/runtime/cpp/pytra-core src/runtime/cpp/pytra`
- 簡易 AST（`if (...)` / `switch (...)` の条件抽出）で `sample/cpp` と `src/runtime/cpp/pytra-gen/{compiler,std,utils}` を走査し、`type_id` 条件を含む class method 生成由来分岐は 0 件だった。
- `type_id` 条件分岐の残存は `src/runtime/cpp/pytra-gen/built_in/type_id.cpp` の registry 管理・型順序管理ロジックに限定され、今回タスク対象の class method dispatch 分岐は既に消失している。

`P2-CPP-SELFHOST-VIRTUAL-01-S1-02` 確定内容（2026-02-25）:
- S1-01 の抽出結果を以下 3 区分へ分類した。
  - 基底クラス呼び出し: 0 件（`type_id` 条件分岐なし）
  - 再帰呼び出し: 0 件（`type_id` 条件分岐なし）
  - 共通ユーティリティ呼び出し: 0 件（dispatch 用 `type_id` 条件分岐なし）
- 非対象として残す項目:
  - `src/runtime/cpp/pytra-gen/built_in/type_id.cpp` の `type_id` registry/state 管理分岐（型登録順序・包含関係管理）。これは class method dispatch 分岐ではないため本タスク対象外。

`P2-CPP-SELFHOST-VIRTUAL-01-S1-03` 確定内容（2026-02-25）:
- S1-01/S1-02 で dispatch 用 `type_id` 分岐が 0 件だったため、`virtual` 置換候補リストは空と判定した。
- 優先順位は以下の no-op 方針で確定:
  - 優先1: 非対象理由の固定化（`type_id` registry 管理は対象外）を S2-03 へ接続
  - 優先2: 実コード改変より先に回帰検証・ドキュメント整備を優先

### S2: emit 側の置換準備

4. `P2-CPP-SELFHOST-VIRTUAL-01-S2-01`: `src/hooks/cpp/emitter` 内の `render` / `call` 系で、仮想呼び出しへ寄せる候補パスを 1 つずつ分解（まず `PyObj` メソッド類、次にユーザー定義 class method）。
5. `P2-CPP-SELFHOST-VIRTUAL-01-S2-02`: `src/py2cpp.py` の class method 呼び出し生成ロジックをテーブル化し、`type_id` 分岐の既定値と `virtual` 経由分岐を明示的に分離する。
6. `P2-CPP-SELFHOST-VIRTUAL-01-S2-03`: 置換対象を `P2-CPP-SELFHOST-VIRTUAL-01-S2-01` と整合し、既知非対象は fallback で保持する。

### S3: 置換実施

7. `P2-CPP-SELFHOST-VIRTUAL-01-S3-01`: `sample` 側 2〜3 件から着手し、`type_id` 分岐を除去して `virtual` 呼び出し化する。
8. `P2-CPP-SELFHOST-VIRTUAL-01-S3-02`: 置換範囲を 5 件程度ずつ拡張し、selfhost 再変換可能性を確認する。
9. `P2-CPP-SELFHOST-VIRTUAL-01-S3-03`: 置換不能ケース（`type_id` 区分が必要なケース）は理由付きで非対象候補に追加し、対象リストを更新する。

### S4: 回帰固定と仕様反映

10. `P2-CPP-SELFHOST-VIRTUAL-01-S4-01`: 差分固定のため `test/unit`（selfhost 関連）と `sample` 再生成 golden 的比較を追加/更新する。
11. `P2-CPP-SELFHOST-VIRTUAL-01-S4-02`: `tools/check_selfhost_cpp_diff.py` / `tools/verify_selfhost_end_to_end.py` を実行して回帰条件を更新し、再現性を検証する。
12. `P2-CPP-SELFHOST-VIRTUAL-01-S4-03`: 進捗を `docs-ja/spec/spec-dev.md`（必要なら `docs-ja/spec/spec-type_id.md`）へ短く反映し、次段の実施基準に接続する。

### S5: テスト追加（最優先）

13. `P2-CPP-SELFHOST-VIRTUAL-01-S5-01`: `test/unit/test_py2cpp_codegen_issues.py` に、`Child.f` から `Base.f` 呼び出し（`Base.f` 参照 + `super().f`）の 2 パターンで `virtual/override` と `type_id` 分岐除去を検証するケースを追加する。
14. `P2-CPP-SELFHOST-VIRTUAL-01-S5-02`: `test/unit/test_py2cpp_codegen_issues.py` か新規 selfhost 系テストに、`Base`/`Child` が混在する `test/unit` + `sample` 再変換で、`type_id` スイッチが残る/消える境界ケース（`staticmethod` 風・`cls` method・`object` レシーバ）を分離して検証する。
15. `P2-CPP-SELFHOST-VIRTUAL-01-S5-03`: `tools/verify_selfhost_end_to_end.py` が対象の `sample`（少なくとも 2 件）を再変換しても `sample` 本体の意味論を壊さないことを確認するテストを追加し、生成コードの簡略化が再帰呼び出しと衝突しないことを固定する。

## 決定ログ

- [2026-02-25] `virtual` が override 済み基底メソッドのみ付与される方向へ変更済み。上記タスクの起点として `selfhost` 側の簡略化余地を低優先で追加。
- 2026-02-25: `P2-CPP-SELFHOST-VIRTUAL-01-S1-01` として `sample/cpp` と `selfhost` 生成領域（`pytra-gen/compiler,std,utils`）の `type_id` 条件分岐を抽出し、class method dispatch 由来の `if/switch` は 0 件、残存は `pytra-gen/built_in/type_id.cpp` の registry 管理のみと確定した。
- 2026-02-25: `P2-CPP-SELFHOST-VIRTUAL-01-S1-02` として抽出結果を 3 区分へ分類したが、dispatch 用 `type_id` 分岐は 0 件だった。非対象は `pytra-gen/built_in/type_id.cpp` の registry 管理分岐のみに整理した。
- 2026-02-25: `P2-CPP-SELFHOST-VIRTUAL-01-S1-03` として `virtual` 置換候補の優先順を策定したが、対象は 0 件（no-op）で確定した。以降は非対象理由の固定化と回帰文書化を優先する。
