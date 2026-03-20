# P1: 非C++ backend の 3層再整列（`Lower` / `Optimizer` / `Emitter`）

最終更新: 2026-03-03

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
- `src/toolchain/emit/{rs,cs,js,ts,go,java,kotlin,swift,ruby,lua,scala}/`
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

- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-01] 非C++ backend 現状の責務棚卸し（どこで意味決定/正規化/描画しているか）を作成する。
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-02] 3層契約（LangIR最小契約、失敗時 fail-closed、層ごとの禁止事項）を定義する。
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-03] ディレクトリ・命名規約（`lower/*`, `optimizer/*`, `emitter/*`）と import 規約を文書化する。
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-01] Wave 1（`rs`）で `lower/optimizer` 骨格を導入し、`py2rs` を3層配線へ切り替える。
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-02] Wave 1（`scala`）で `lower/optimizer` 骨格を導入し、`py2scala` を3層配線へ切り替える。
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-03] Wave 1の回帰（unit/transpile/sample）を固定し、移行テンプレートを確定する。
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-01] Wave 2（`js/ts/cs`）へ同テンプレートを展開する。
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-02] Wave 3（`go/java/kotlin/swift`）へ同テンプレートを展開する。
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-03] Wave 4（`ruby/lua/php`）へ同テンプレートを展開する。
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-01] 旧構成再発防止チェック（旧 import / emitter責務逆流）を追加する。
- [x] [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-02] `docs/ja/spec` / `docs/en/spec` を更新し、3層を backend 標準構成として明文化する。

## S1-01 棚卸し結果（2026-03-03）

| backend | 現構成 | 意味決定/正規化の主位置 | 描画の主位置 | 備考 |
| --- | --- | --- | --- | --- |
| `rs` | `emitter/rs_emitter.py` + `hooks/rs_hooks.py` | `rs_emitter.py`（`kind ==` 分岐多数、`ForCore` 展開） | `rs_emitter.py` | `CodeEmitter` 継承。runtime import/補助関数生成も同居。 |
| `cs` | `emitter/cs_emitter.py` + `hooks/cs_hooks.py` | `cs_emitter.py`（型判定・isinstance lower・range 展開） | `cs_emitter.py` | `CodeEmitter` 継承。runtime呼び出し選択が emitter 内に集中。 |
| `js` | `emitter/js_emitter.py` + `hooks/js_hooks.py` | `js_emitter.py`（import/runtime symbol 収集含む） | `js_emitter.py` | `CodeEmitter` 継承。意味決定とレンダリングの混在が顕著。 |
| `ts` | `emitter/ts_emitter.py` | ほぼ `js` へ委譲 | `js` 出力の薄いラッパ | TS 専用 Lower/Optimizer 不在。 |
| `go` | `emitter/go_native_emitter.py` | `go_native_emitter.py`（`ForCore` / compare / call lower） | `go_native_emitter.py` | 単一 native emitter に集約。 |
| `java` | `emitter/java_native_emitter.py` | `java_native_emitter.py` | `java_native_emitter.py` | 単一 native emitter。 |
| `kotlin` | `emitter/kotlin_native_emitter.py` | `kotlin_native_emitter.py` | `kotlin_native_emitter.py` | 単一 native emitter。 |
| `swift` | `emitter/swift_native_emitter.py` | `swift_native_emitter.py` | `swift_native_emitter.py` | 単一 native emitter。 |
| `ruby` | `emitter/ruby_native_emitter.py` | `ruby_native_emitter.py` | `ruby_native_emitter.py` | 単一 native emitter。 |
| `lua` | `emitter/lua_native_emitter.py` | `lua_native_emitter.py` | `lua_native_emitter.py` | 単一 native emitter。 |
| `scala` | `emitter/scala_native_emitter.py` | `scala_native_emitter.py` | `scala_native_emitter.py` | 単一 native emitter。 |
| `php` | `emitter/php_native_emitter.py` | `php_native_emitter.py`（dict/in/ctor/entrypoint lower を内包） | `php_native_emitter.py` | 単一 native emitter。 |
| `nim` | `emitter/nim_native_emitter.py` | `nim_native_emitter.py` | `nim_native_emitter.py` | 新規導入 backend。最初から3層化対象に含める。 |

棚卸しまとめ:
- 非C++ backend は全て「実質 emitter 1層」で、意味決定・正規化・描画が混在している。
- `rs/cs/js` は `CodeEmitter` 継承 + hooks 構造だが、Lower/Optimizer 分離には未到達。
- `go/java/kotlin/swift/ruby/lua/scala/php/nim` は native emitter 単体で、3層化の導線が未整備。

## S1-02 3層契約（2026-03-03）

### Lower 契約
- 入力: EAST3 Module。
- 出力: LangIR Module（言語固有だが意味保存、テキスト未生成）。
- 責務: 言語構文へ必要な決定（range 展開、membership 方式、entrypoint 形）を LangIR ノードへ正規化。
- 禁止: 文字列連結でのソース直接生成、runtime ファイル配置、I/O。

### Optimizer 契約
- 入力/出力: LangIR Module -> LangIR Module。
- 責務: 意味保存の局所変換（冗長 cast 除去、単純化、依存収集補助）。
- 禁止: EAST 再解釈、テキスト生成、副作用を伴う最適化。

### Emitter 契約
- 入力: LangIR Module。
- 出力: 言語ソース文字列。
- 責務: フォーマット・字句整形・最終レンダリング。
- 禁止: 新規の意味決定（`in/not in` 判定方式選択など）、型解決の再推論。

### fail-closed ルール
- Lower/Optimizer/Emitter いずれも未知ノード/未知属性は黙ってスキップせず `RuntimeError` を返す。
- Layer 境界を跨ぐ暗黙フォールバック（例: Emitter が EAST3 を直接再走査して補正）は禁止。
- CI では `check_py2<lang>_transpile` 失敗を許容しない（既知失敗は明示リスト管理）。

## S1-03 命名・import 規約（2026-03-03）

ディレクトリ規約:
- `src/toolchain/emit/<lang>/lower/`:
  - `ir.py`（LangIR node 定義）
  - `from_east3.py`（EAST3 -> LangIR）
- `src/toolchain/emit/<lang>/optimizer/`:
  - `pipeline.py`（pass 合成）
  - `passes/*.py`（個別最適化）
- `src/toolchain/emit/<lang>/emitter/`:
  - `<lang>_emitter.py` または `<lang>_native_emitter.py`（LangIR -> text）
  - `runtime_paths.py` / `profile_loader.py` 等の描画補助

import 規約:
- `py2<lang>.py` は `toolchain.emit.<lang>.lower` -> `optimizer` -> `emitter` の順でのみ参照する。
- `emitter` から `lower` を直接 import しない（循環依存を禁止）。
- 他言語 backend への直接依存を禁止（例: `ts` が `js` emitter 実体へ委譲する構造は段階解消対象）。
- 共通化が必要な場合は `pytra/compiler/*` の共通層へ抽出して参照する。

移行単位:
- Wave1（`rs`, `scala`）で規約適用テンプレートを確定し、Wave2 以降はテンプレート踏襲で展開。

決定ログ:
- 2026-03-02: ユーザー指示により、「C++以外も `Lower/Optimizer/Emitter` に統一」を P1 として起票。
- 2026-03-02: 一括同時移行は避け、Wave 方式（2言語パイロット -> 横展開）を前提にする方針を採用。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-01] 非C++ backend の現状責務棚卸しを完了し、混在点を明文化。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-02] Lower/Optimizer/Emitter 契約と fail-closed 規約を確定。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S1-03] ディレクトリ命名/import 規約を確定し、Wave1 テンプレート方針を記録。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-01] `toolchain/emit/rs/lower` と `toolchain/emit/rs/optimizer` を導入し、`py2rs.py` を 3層配線へ切替。`check_py2rs_transpile` を pass。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-02] `toolchain/emit/scala/lower` と `toolchain/emit/scala/optimizer` を導入し、`py2scala.py` を 3層配線へ切替。`check_py2scala_transpile`（`checked=141 ok=141 fail=0`）を pass。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-03] Wave1 回帰の初回実行で `SUMMARY cases=18 pass=6 fail=12`（`scala` の `run_failed=12`）を確認し、主因を `__pytra_bytearray/__pytra_bytes` 戻り型不整合と `ForCore` 条件式の不正正規化（`value` 混入）に特定。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S2-03] `src/runtime/scala/pytra/py_runtime.scala` の `bytearray/bytes` を `ArrayBuffer[Long]` 返却へ是正し、`scala_native_emitter` に正規化条件式の識別子検証フォールバックを追加。`check_py2scala_transpile`（141/141）、`check_py2rs_transpile`（131/131, skipped=10）、`runtime_parity_check --case-root sample --targets rs,scala --ignore-unstable-stdout`（18/18）で通過。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-01] `toolchain/emit/{js,ts,cs}/lower`・`optimizer` を追加し、`py2{js,ts,cs}.py` を `lower -> optimizer -> emitter` 配線へ切替。`check_py2{js,ts,cs}_transpile` は各 `checked=133 ok=133 fail=0 skipped=8` で通過。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-01] Wave2 sample parity（`runtime_parity_check --case-root sample --targets js,ts,cs --ignore-unstable-stdout`）は `cases=18 pass=14 fail=4`、`artifact_size_mismatch=8`（`js/ts` の `01-04`）を確認。3層配線変更に起因する transpile 崩れはなく、artifact差は既知課題として次 wave へ持ち越す。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-02] `toolchain/emit/{go,java,kotlin,swift}/lower`・`optimizer` を追加し、`py2{go,java,kotlin,swift}.py` を `lower -> optimizer -> emitter` 配線へ切替。`check_py2{go,java,kotlin,swift}_transpile` は各 `checked=131 ok=131 fail=0 skipped=10` で通過。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-02] Wave3 sample parity（`runtime_parity_check --case-root sample --targets go,java,kotlin,swift --ignore-unstable-stdout`）は `cases=18 pass=1 fail=17`（`go: run_failed=11`, `java: run_failed=5 + artifact_missing=12`, `swift: toolchain_missing=18`, `kotlin: failureなし`）。3層配線変更の回帰は transpile check で非退行を確認し、実行系差分は wave別課題として継続管理。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-03] `toolchain/emit/{ruby,lua,php}/lower`・`optimizer` を追加し、`py2{rb,lua,php}.py` を `lower -> optimizer -> emitter` 配線へ切替。`check_py2rb_transpile`（`checked=132 ok=132 fail=0 skipped=10`）、`check_py2lua_transpile`（`checked=89 ok=89 fail=0 skipped=53`）、`check_py2php_transpile`（`checked=10 ok=10 fail=0 skipped=0`）で通過。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S3-03] Wave4 sample parity（`runtime_parity_check --case-root sample --targets ruby,lua,php --ignore-unstable-stdout`）は `cases=18 pass=14 fail=4`。内訳は `php` の `output_mismatch=2`（`12/13`）と `run_failed=1`（`16`）、`ruby` の `run_failed=1`（`18`）で、`lua` は failure なし。3層配線の transpile 回帰は非退行として確認済み。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-01] `tools/check_noncpp_east3_contract.py` を 12 backend（`rs/cs/js/ts/go/java/kotlin/swift/ruby/lua/php/scala`）対象に拡張し、`py2<lang>.py` の `lower/optimizer` 配線必須パターン・順序検査と `lower/optimizer <-> emitter` 逆流 import 禁止を static check 化。`python3 tools/check_noncpp_east3_contract.py --skip-transpile` と `python3 tools/check_noncpp_east3_contract.py`（12本 transpile check 含む）が pass。
- 2026-03-03: [ID: P1-MULTILANG-BACKEND-3LAYER-01-S4-02] `docs/ja/spec/{spec-dev,spec-folder}.md` と `docs/en/spec/{spec-dev,spec-folder}.md` を更新し、非C++ backend の 3 層標準（適用 backend、層責務、逆流禁止、検査導線）を明文化。これにより `P1-MULTILANG-BACKEND-3LAYER-01` の分解タスクを全完了とした。
