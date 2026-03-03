# P1: `test/unit` レイアウト再編と未使用テスト整理

最終更新: 2026-03-04

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-TEST-UNIT-LAYOUT-PRUNE-01`

背景:
- `test/unit/` に言語別・IR・tooling・selfhost関連テストが混在しており、探索性と保守性が低下している。
- `test_py2*_smoke.py` のような backend 系テストと、`test_east*` / `test_code_emitter.py` のような共通層テストが同一階層に並び、責務境界が読み取りづらい。
- 過去の移行で残置されたテストの中に、現行運用で参照されない（discover対象外・個別実行導線なし）候補がある。

目的:
- `test/unit` を責務別ディレクトリへ再編し、テスト探索コストを下げる。
- 「未使用テスト候補」を機械的に棚卸しし、削除/統合/維持を根拠付きで決定する。
- 再編後も既存の unit/transpile/selfhost 回帰導線を維持する。

対象:
- `test/unit/` 配下の再配置（例: `common`, `backends/<lang>`, `ir`, `tooling`, `selfhost`）
- `tools/` / `docs/` の test path 参照更新
- 未使用候補テストの判定・整理（削除または統合）
- 再流入防止の検査追加（任意）

非対象:
- backend 生成品質の改善
- fixture の意味変更
- parity test 仕様変更

受け入れ基準:
- `test/unit` が責務別フォルダ構成へ再編され、トップレベル直下の混在が解消される。
- 主要実行導線（`unittest discover`, `tools/check_py2*_transpile.py`, selfhost check）が新パスで通る。
- 未使用テスト整理について「削除/統合/維持」の判断根拠（参照有無・実行実績）を残す。
- 誤削除防止のため、削除対象は少なくとも 1 回の全体 discover と参照スキャンで未使用確認を満たす。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test*.py'`
- `rg -n \"test/unit/|test_py2.*smoke\" tools docs/ja docs/en -g '*.py' -g '*.md'`
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
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2php_transpile.py`
- `python3 tools/check_py2nim_transpile.py`

## 分解

- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-01] `test/unit` の現行テストを責務分類（common/backends/ir/tooling/selfhost）で棚卸しし、移動マップを確定する。
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S1-02] 目標ディレクトリ規約を定義し、命名・配置ルールを決定する。
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-01] テストファイルを新ディレクトリへ移動し、`tools/` / `docs/` の参照パスを一括更新する。
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S2-02] `unittest discover` と個別実行導線が新構成で通るように CI/ローカルスクリプトを更新する。
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-01] 未使用テスト候補を抽出し、`削除/統合/維持` を判定する監査メモを作成する。
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S3-02] 判定済みの未使用テストを削除または統合し、再発防止チェック（必要なら新規）を追加する。
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-01] 主要 unit/transpile/selfhost 回帰を実行し、再編・整理後の非退行を確認する。
- [ ] [ID: P1-TEST-UNIT-LAYOUT-PRUNE-01-S4-02] `docs/ja/spec`（必要なら `docs/en/spec`）へ新しいテスト配置規約と運用手順を反映する。

決定ログ:
- 2026-03-04: ユーザー指示により、`test/unit` の責務別フォルダ再編と未使用テスト整理を P1 タスクとして起票した。削除は必ず監査根拠付きで段階実施する方針を採用。
