# P2: Scala 負例fixtureの「skip」撤廃と失敗期待テスト化

最終更新: 2026-03-01

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-SCALA-NEGATIVE-ASSERT-01`

背景:
- `tools/check_py2scala_transpile.py` は `DEFAULT_EXPECTED_FAILS` に含まれる fixture を `skipped` 扱いで除外しており、負例が「失敗すること」自体を検証していない。
- その結果、失敗理由の変化や負例の不整合（例: 既に通る fixture が残存）を検知しづらく、品質保証として弱い。
- ユーザー要件として「skip ではなく、負例はコンパイルエラーになることを明示テストする」方針を採用する。

目的:
- Scala 変換の負例 fixture を「除外」ではなく「失敗期待のテスト対象」として運用する。
- 失敗種別（parser制約/型制約/object receiver 制約など）を固定し、失敗メッセージの逸脱を回帰検知できる状態にする。

対象:
- `tools/check_py2scala_transpile.py` の expected-fail 運用見直し
- Scala 向け負例チェック経路（失敗期待）
- 負例 fixture の棚卸しと stale エントリ削除
- CI/ローカル手順の更新（正例チェック + 負例チェック）

非対象:
- Scala backend 自体の機能追加（`*args`/`**kwargs`/positional-only の新規実装）
- C++/Rust など他 backend の負例運用統一
- 負例fixtureの大量追加（最小限の代表ケースに留める）

受け入れ基準:
- `tools/check_py2scala_transpile.py` 実行時に、既知負例が単純 `skip` ではなく「失敗期待として評価」されること。
- 既知負例が予期せず成功した場合は失敗（unexpected pass）として検知されること。
- 既知負例が失敗しても、期待した失敗分類と不一致なら失敗として検知されること。
- 正例 fixture / sample は従来通り成功を維持すること。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2scala_transpile.py --include-expected-failures`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2scala_smoke.py' -v`

決定ログ:
- 2026-03-01: ユーザー指示により、Scala の負例 fixture を `skip` で除外する運用を終了し、「失敗することを期待値として検証する」方針で P2 起票。

## 分解

- [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S1-01] Scala 負例 fixture の現行失敗理由を棚卸しし、期待する失敗分類（parser/type/object制約）を固定する。
- [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S1-02] `DEFAULT_EXPECTED_FAILS` の stale エントリ（通過済みfixture）を除外し、負例集合を最新化する。
- [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S2-01] `check_py2scala_transpile.py` を「正例成功 + 負例失敗期待」両検証モードへ再構成する。
- [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S2-02] 負例の `unexpected pass` / `unexpected error category` を fail-closed で失敗させる。
- [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S3-01] unit テストを追加し、負例運用が `skip` に戻らないことを固定する。
- [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S3-02] `docs/ja/how-to-use.md` と `docs/en/how-to-use.md` の Scala 検証手順を更新し、実行順（正例/負例）を明文化する。
