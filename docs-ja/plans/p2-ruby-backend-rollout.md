# P2: Ruby backend 追加

最終更新: 2026-02-27

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P2-RUBY-BACKEND-01`

背景:
- ユーザー要望として、変換先バックエンドへ Ruby を追加する方針が示されている。
- 現状の対応言語は `cpp/rs/cs/js/ts/go/java/swift/kotlin` で、Ruby backend は未実装。
- 追加時に責務境界（EAST3 入力・fail-closed・runtime 境界）を先に固定しないと、既存 backend と同様の肥大化リスクがある。

目的:
- `py2rb.py` を入口として `EAST3 -> Ruby` の native 直生成経路を追加し、`sample/py` の主要ケースを Ruby で実行可能にする。

言語展開順（決定）:
1. Ruby（本計画で実施）
2. Lua（Ruby backend 完了後に `P2` として起票）
3. PHP（Lua backend 完了後に `P2` として起票）

対象:
- `src/py2rb.py`
- `src/hooks/ruby/emitter/`
- `src/runtime/ruby/pytra/`（必要最小限）
- `tools/check_py2rb_transpile.py` / `test/unit/test_py2rb_smoke.py` / parity 導線
- `sample/ruby` と関連ドキュメント

非対象:
- PHP backend の同時追加
- Ruby backend の高度最適化（まず正しさと回帰導線を優先）
- 既存 backend（cpp/rs/cs/js/ts/go/java/swift/kotlin）の大規模設計変更

受け入れ基準:
- `py2rb.py` で EAST3 から Ruby コードを生成できる。
- 最小 fixture（`add` / `if_else` / `for_range`）の変換・実行が通る。
- `tools/check_py2rb_transpile.py` と smoke/parity 回帰導線が用意される。
- `sample/ruby` と `docs-ja/docs` の利用手順・対応表が同期される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --all-samples --ignore-unstable-stdout`

決定ログ:
- 2026-02-27: ユーザー指示により、Ruby backend 追加タスクを `P2` 優先度で TODO 管理する方針を確定した。
- 2026-02-27: ユーザー指示により、追加言語の実装順を `Ruby -> Lua -> PHP` として固定した。

## 分解

- [ ] [ID: P2-RUBY-BACKEND-01-S1-01] Ruby backend の契約（入力 EAST3、fail-closed、runtime 境界、非対象）を文書化する。
- [ ] [ID: P2-RUBY-BACKEND-01-S1-02] `src/py2rb.py` と `src/hooks/ruby/emitter/` の骨格を追加し、最小 fixture を通す。
- [ ] [ID: P2-RUBY-BACKEND-01-S2-01] 式/文の基本 lower（代入、分岐、ループ、呼び出し、組み込み最小）を実装する。
- [ ] [ID: P2-RUBY-BACKEND-01-S2-02] class/instance/isinstance/import（`math`・画像runtime含む）対応を段階実装する。
- [ ] [ID: P2-RUBY-BACKEND-01-S3-01] `check_py2rb_transpile` と smoke/parity 回帰導線を追加する。
- [ ] [ID: P2-RUBY-BACKEND-01-S3-02] `sample/ruby` 再生成と README/How-to-use 同期を行う。
