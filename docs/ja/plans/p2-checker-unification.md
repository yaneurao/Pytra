# P2: `check_py2*` checker の単一化（`--target` + プロファイル化）

最終更新: 2026-03-05

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-CHECKER-UNIFY-01`

背景:
- `tools/check_py2cpp_transpile.py` など言語別 checker が多数存在し、CI・計画書・テストが個別ファイル名へ強く依存している。
- 役割は本質的に共通（`py2x --target <lang>` で fixture/sample を変換し、成功/既知失敗契約を検証）であり、分割ファイル維持は重複実装と運用コストを増やす。
- ユーザー方針として、checker も単一入口へ統一し、言語差分は設定で扱う構成が望ましい。

目的:
- checker を `tools/check_py2x_transpile.py --target <lang>` の単一入口へ統一する。
- 言語差分（ケース集合、expected-fail、追加アサーション）はプロファイル定義へ移し、スクリプト本体の分岐を縮小する。
- 既存 `check_py2*.py` は段階移行後に削除する（移行期間は互換ラッパ許容）。

対象:
- `tools/check_py2*.py` 群
- 新規統一 checker（`tools/check_py2x_transpile.py`）
- checker 設定（target別プロファイル）
- 呼び出し元（`tools/run_local_ci.py`, 契約検証スクリプト, docs/plan のコマンド例）

非対象:
- backend 生成品質の改善
- parity ロジックそのものの変更
- selfhost 実行経路の再設計

受け入れ基準:
- 単一 checker で `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala/php/nim` を `--target` 指定で実行できる。
- 言語別 expected-fail/追加検証は設定ファイルで管理される。
- `run_local_ci.py` と関連スクリプトは単一 checker 呼び出しへ移行済み。
- 旧 `check_py2*.py` は最終的に削除される（中間段階では薄い互換ラッパのみ許容）。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m py_compile tools/check_py2x_transpile.py`
- `python3 tools/check_py2x_transpile.py --target cpp`
- `python3 tools/check_py2x_transpile.py --target java`
- `python3 tools/check_py2x_transpile.py --target scala`
- `python3 tools/run_local_ci.py`

## 分解

- [ ] [ID: P2-CHECKER-UNIFY-01-S1-01] 既存 `check_py2*.py` の差分（ケース選定・expected-fail・追加品質検証）を棚卸しして統一仕様を定義する。
- [ ] [ID: P2-CHECKER-UNIFY-01-S1-02] target別プロファイル形式（ケース集合、許容失敗、追加検証フック）を設計する。
- [ ] [ID: P2-CHECKER-UNIFY-01-S2-01] `tools/check_py2x_transpile.py` を実装し、`--target` で全言語の共通検証を実行可能にする。
- [ ] [ID: P2-CHECKER-UNIFY-01-S2-02] 既存 `check_py2*.py` を互換ラッパ化し、新checkerへ委譲させる。
- [ ] [ID: P2-CHECKER-UNIFY-01-S2-03] `run_local_ci.py` / 契約検証スクリプト / docs の呼び出しを単一 checker に置換する。
- [ ] [ID: P2-CHECKER-UNIFY-01-S3-01] 互換期間終了後に `check_py2*.py` を削除し、再導入防止ガードを追加する。
- [ ] [ID: P2-CHECKER-UNIFY-01-S3-02] unit/CI 回帰を実行し、単一化後の非退行を固定する。

決定ログ:
- 2026-03-05: ユーザー指示により、言語別 checker 群は将来削除前提とし、`--target` 駆動の単一 checker へ統合する方針を確定。
