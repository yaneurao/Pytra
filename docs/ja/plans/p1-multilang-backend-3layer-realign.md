# P1: 非C++ backend の 3層再整列（`Lower` / `Optimizer` / `Emitter`）

最終更新: 2026-03-02

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-MULTILANG-BACKEND-3LAYER-01`

背景:
- C++ backend は `lower/optimizer/emitter` の3段構成へ移行済みだが、非C++ backend は `emitter` 中心で、責務が混在している。
- 言語ごとに `hooks` / helper / 出力補助の置き場所が不統一で、同種改修時の横展開コストが高い。
- 生成品質改善・selfhost・runtime分離などのタスクが、構成不統一により個別最適化へ寄りやすい。

目的:
- 非C++ backend を順次 `Lower -> Optimizer -> Emitter` に再整列し、実装責務を統一する。
- `Emitter` は「最終レンダラ」に縮退し、意味決定・正規化は `Lower/Optimizer` へ寄せる。
- backend 間で再利用可能な移行テンプレート（命名規約・契約・回帰ガード）を確立する。

対象:
- `src/backends/{rs,cs,js,ts,go,java,kotlin,swift,ruby,lua,scala}/`
- 各 `py2*.py` bridge（必要最小限の配線変更）
- 関連 unit / transpile check / sample regeneration

非対象:
- EAST1/EAST2/EAST3 の意味仕様変更
- 各言語 runtime API の仕様刷新
- C++ backend の追加再編（別 P0 で実施中）

受け入れ基準:
- 対象 backend で `lower/optimizer/emitter` の3層ディレクトリが揃う。
- `Emitter` 側の EAST3 直接分岐（意味決定）が段階的に縮退し、`Lower/Optimizer` 側に移設される。
- 既存の transpile check / unit / sample 再生成で非退行を維持する。
- 「新規 backend は3層前提」の規約が `docs/ja/spec` と検査に反映される。

実施方針:
1. まず共通契約（IR最小契約、責務境界、命名規約）を固定する。
2. 1〜2言語でパイロット移行し、移行テンプレートを固める。
3. 残り言語へ同テンプレートを水平展開する。
4. 旧構成依存（旧 import / emitter 側意味決定）の再発ガードを追加する。

推奨移行順:
- Wave 1: `rs`, `scala`（既存品質・型情報活用が比較的進んでいる）
- Wave 2: `js`, `ts`, `cs`
- Wave 3: `go`, `java`, `kotlin`, `swift`
- Wave 4: `ruby`, `lua`, `php`（runtime/補助層差分を伴う）

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rs_transpile.py`
- `python3 tools/check_py2scala_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_py2cs_transpile.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 tools/check_py2lua_transpile.py`
- `python3 tools/check_py2php_transpile.py`

## 分解

- [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-01] 非C++ backend 現状の責務棚卸し（どこで意味決定/正規化/描画しているか）を作成する。
- [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-02] 3層契約（LangIR最小契約、失敗時 fail-closed、層ごとの禁止事項）を定義する。
- [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-03] ディレクトリ・命名規約（`lower/*`, `optimizer/*`, `emitter/*`）と import 規約を文書化する。
- [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-01] Wave 1（`rs`）で `lower/optimizer` 骨格を導入し、`py2rs` を3層配線へ切り替える。
- [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-02] Wave 1（`scala`）で `lower/optimizer` 骨格を導入し、`py2scala` を3層配線へ切り替える。
- [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-03] Wave 1の回帰（unit/transpile/sample）を固定し、移行テンプレートを確定する。
- [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-01] Wave 2（`js/ts/cs`）へ同テンプレートを展開する。
- [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-02] Wave 3（`go/java/kotlin/swift`）へ同テンプレートを展開する。
- [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-03] Wave 4（`ruby/lua/php`）へ同テンプレートを展開する。
- [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-01] 旧構成再発防止チェック（旧 import / emitter責務逆流）を追加する。
- [ ] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-02] `docs/ja/spec` / `docs/en/spec` を更新し、3層を backend 標準構成として明文化する。

決定ログ:
- 2026-03-02: ユーザー指示により、「C++以外も `Lower/Optimizer/Emitter` に統一」を P1 として起票。
- 2026-03-02: 一括同時移行は避け、Wave 方式（2言語パイロット -> 横展開）を前提にする方針を採用。
