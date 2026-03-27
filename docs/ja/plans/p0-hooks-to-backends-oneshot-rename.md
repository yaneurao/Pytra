<a href="../../en/plans/p0-hooks-to-backends-oneshot-rename.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P0: `src/hooks` -> `src/backends` 一括改名（最優先の最優先）

最終更新: 2026-03-03

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P0-HOOKS-TO-BACKENDS-RENAME-01`

背景:
- 現在の `src/hooks/` は実態として hook 断片ではなく、各言語 backend 実装本体（lower/optimizer/emitter/extensions）を保持している。
- 命名と実体の不一致により、`hooks/<lang>/hooks` のような二重表現や責務誤解が発生している。
- ユーザー指示により、段階移行ではなく一括で `src/toolchain/emit/` へ改名し、最優先で収束させる。

目的:
- backend 実装の正規ルートを `src/toolchain/emit/<lang>/` に統一し、`hooks` 名の曖昧さを解消する。
- 既存 import/CLI/テスト/ドキュメントを同一変更で更新し、改名起因の破断を残さない。

対象:
- ディレクトリ移動: `src/hooks/** -> src/toolchain/emit/**`
- import 参照更新: `src/py2*.py`, `src/pytra/**`, `tools/**`, `test/**`
- 仕様/利用文書更新: `docs/ja/spec/*`, `docs/en/spec/*`, `docs/ja/how-to-use.md`, `docs/en/how-to-use.md`
- 必要に応じた暫定互換レイヤ（`src/hooks` 側 re-export）※短期限定

非対象:
- backend の機能追加・最適化内容変更
- EAST 仕様変更
- runtime API の意味変更

受け入れ基準:
- `src/toolchain/emit/<lang>/` が backend 実装の唯一の正規配置になる。
- リポジトリ内の import は原則 `toolchain.emit.*` を参照し、`hooks.*` 直参照が残らない（意図的互換層を除く）。
- `py2*.py` 主要 CLI と `check_py2*_transpile.py` が非退行で通る。
- 仕様書でフォルダ責務が `backends` 名へ更新され、`hooks` は互換/退役対象として明記される。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `rg -n "from hooks\\.|import hooks\\." src test tools`
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

## 分解

- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S1-01] `src/hooks/**` の現行構成を棚卸しし、`src/toolchain/emit/**` への 1:1 移動マップを確定する。
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S1-02] 改名時に影響する import 参照点（`src/`, `tools/`, `test/`）を全列挙し、更新順序を固定する。
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S2-01] `src/hooks` を `src/backends` へ一括移動し、パッケージ初期化ファイルを維持する。
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S2-02] `src/py2*.py` と compiler/utility 側 import を `hooks.*` から `toolchain.emit.*` へ一括更新する。
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S2-03] `tools/**` / `test/**` の import を `toolchain.emit.*` へ一括更新し、テスト実行導線を復旧する。
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S2-04] 必要最小限の互換層（`src/hooks` re-export）を設置し、当面の外部参照破断を防ぐ（不要なら設置しない）。
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S3-01] `docs/ja` / `docs/en` の仕様・手順書で `src/hooks` 表記を `src/backends` へ更新する。
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S3-02] `spec-folder` / `spec-dev` の責務記述を `backends` 名へ更新し、`hooks` を互換・退役扱いへ明記する。
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S4-01] 全 target の transpile チェックを再実行し、改名起因の import 崩れがないことを確認する。
- [x] [ID: P0-HOOKS-TO-BACKENDS-RENAME-01-S4-02] `rg` による残存 `hooks.*` 参照監査を実施し、残存理由を明示して収束させる。

決定ログ:
- 2026-03-02: ユーザー指示により、`src/hooks` 名称の不整合を解消するため、`src/backends` への一括改名を「最優先の最優先（P0最上位）」として起票。
- 2026-03-03: `src/hooks` ディレクトリを `src/backends` へ一括移動し、`src/py2*.py`/`src/toolchain/emit/**`/`tools/**`/`test/**` の import を `toolchain.emit.*` 参照へ更新した。
- 2026-03-03: 一括置換で `hooks.to_dict()` が `toolchain.emit.to_dict()` 化された副作用を `cpp/cs/rs hooks` 実装と `code_emitter.py` で修正した。
- 2026-03-03: 現行ドキュメント（`docs/ja|en/spec/*.md`, `docs/ja|en/how-to-use.md`）の `src/hooks` 表記を `src/backends` に更新した（archiveは対象外）。
- 2026-03-03: 主要チェック結果は `check_py2cpp_transpile: checked=136 ok=136 fail=0 skipped=6`、`check_py2rs_transpile: checked=131 ok=131 fail=0 skipped=10`。`check_py2cs_transpile` は `checked=135 ok=133 fail=2 skipped=6`（`yield_generator_min.py`, `tuple_assign.py` の既知失敗）で、改名起因の import 崩れは観測されなかった。
- 2026-03-03: `check_py2go/swift/kotlin/lua/scala/php` は通過。`check_py2js/check_py2ts` の失敗は `test_east3_cpp_bridge` の既存アサーション失敗（tuple loop header）、`check_py2java/check_py2rb` の失敗は `control/finally` 系既知失敗で、いずれも `hooks -> backends` 改名由来の import エラーではないことを確認した。
- 2026-03-03: 互換層（`src/hooks` re-export）は設置しない方針を採用。理由は、リポジトリ内参照を `toolchain.emit.*` へ一括更新済みであり、互換層が残ると `src/backends` 正規化の収束を遅らせるため。
- 2026-03-03: `src/test/tools` 監査で `from hooks.` / `import hooks.` / `src/hooks/` / `src.hooks.` の残存は 0 件。`docs/*/spec/archive` の `src/hooks` は履歴保持のため意図的に残置。
