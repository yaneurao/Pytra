# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-03

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs/ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs/ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs/ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs/ja/todo/index.md` / `docs/ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。
- 一時出力は既存 `out/`（または必要時のみ `/tmp`）を使い、リポジトリ直下に新規一時フォルダを増やさない。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs/ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs/ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs/ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。


## 未完了タスク

### P0: `src` レイアウト再編（`toolchain` / `pytra` / `runtime`）

文脈: [docs/ja/plans/p0-src-layout-toolchain-pytra-runtime-split.md](../plans/p0-src-layout-toolchain-pytra-runtime-split.md)

1. [x] [ID: P0-SRC-LAYOUT-SPLIT-01] `src` を責務別に再編し、`src/pytra` から変換プログラム本体を分離する（後方互換なし）。
2. [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S1-01] 現行 `src/pytra/{frontends,ir,compiler,std,utils,built_in}` の責務と参照点を棚卸しする。
3. [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S1-02] 新レイアウト規約（`toolchain` / `pytra` / `runtime`）と依存方向を `docs/ja/spec/spec-folder.md` に確定する。
4. [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S1-03] 旧 import 経路を禁止する移行ルール（後方互換なし）を明文化する。
5. [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-01] `src/toolchain/frontends` を作成し、`src/pytra/frontends` を一括移動する。
6. [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-02] `src/toolchain/ir` を作成し、`src/pytra/ir` を一括移動する。
7. [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-03] `src/toolchain/compiler` を作成し、`src/pytra/compiler` を一括移動する。
8. [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S2-04] `src/pytra` 配下の空ディレクトリ・不要残骸を除去し、`std/utils/built_in` 中心構成へ整理する。
9. [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S3-01] `src/`, `tools/`, `test/` の import を新経路へ一括更新する（shim 追加禁止）。
10. [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S3-02] CLI エントリ（`py2x.py`, `py2x-selfhost.py`, `py2*.py`）の import 経路を新構成に合わせる。
11. [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S3-03] 検査スクリプトを追加し、旧 `pytra.frontends|ir|compiler` 参照を fail-fast で検出する。
12. [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S4-01] 主要 unit/transpile 回帰を実行し、非退行を確認する。
13. [x] [ID: P0-SRC-LAYOUT-SPLIT-01-S4-02] `docs/ja/spec`（必要なら `docs/en/spec`）へ新ディレクトリ責務と導線を反映する。
- 進捗メモ: [ID: P0-SRC-LAYOUT-SPLIT-01-S1-01] `src/pytra` 6領域の責務/参照点を棚卸しし、`compiler` 依存集中と `frontends`↔`ir` 循環を確認。
- 進捗メモ: [ID: P0-SRC-LAYOUT-SPLIT-01-S1-02] `spec-folder` に `src/toolchain` 正規3層と `src/pytra` 参照ライブラリ専用境界、依存方向ルールを反映。
- 進捗メモ: [ID: P0-SRC-LAYOUT-SPLIT-01-S1-03] `spec-folder` に旧 import 経路禁止（`pytra.frontends|ir|compiler`）と shim 禁止、`rg` 検査手順を追記。
- 進捗メモ: [ID: P0-SRC-LAYOUT-SPLIT-01-S2-01] `frontends` を `src/toolchain/frontends` へ移動し、関連 import と層境界検査・bootstrap unit を更新。
- 進捗メモ: [ID: P0-SRC-LAYOUT-SPLIT-01-S2-02] `ir` を `src/toolchain/ir` へ移動し、関連 import と層境界検査・transpile smoke を更新。
- 進捗メモ: [ID: P0-SRC-LAYOUT-SPLIT-01-S2-03] `compiler` を `src/toolchain/compiler` へ移動し、CLI/emit/test/tooling の import・固定参照パスを更新。
- 進捗メモ: [ID: P0-SRC-LAYOUT-SPLIT-01-S2-04] `src/pytra` から `frontends/ir/compiler` 痕跡を除去し、`std/utils/built_in` と最小エントリのみの構成を確認。
- 進捗メモ: [ID: P0-SRC-LAYOUT-SPLIT-01-S3-01] `src/tools/test/selfhost` の import を一括更新し、旧 `pytra.(frontends|ir|compiler)` 参照が 0 件であることを確認。
- 進捗メモ: [ID: P0-SRC-LAYOUT-SPLIT-01-S3-02] `py2x.py` / `py2x-selfhost.py` / `py2*.py` / `ir2lang.py` の import を `toolchain.compiler.*` 基準へ統一。
- 進捗メモ: [ID: P0-SRC-LAYOUT-SPLIT-01-S3-03] `check_pytra_layer_boundaries.py` に旧 import 経路の全体スキャンを追加し、`legacy import path is forbidden` で fail-fast 検出可能化。
- 進捗メモ: [ID: P0-SRC-LAYOUT-SPLIT-01-S4-01] 主要 transpile 回帰（`cpp/rs/js/ts/go/java/kotlin/swift/ruby/lua/scala/php/nim`）と境界チェックを実行し、全件 pass を確認。
- 進捗メモ: [ID: P0-SRC-LAYOUT-SPLIT-01-S4-02] `docs/ja/spec` と `docs/en/spec`（archive 除く）の旧 `src/pytra/{frontends,ir,compiler}` 参照を新 `src/toolchain/*` へ更新。

### P0: PHP 画像 runtime 実装と sample/16 修復

文脈: [docs/ja/plans/p0-php-image-runtime-and-s16-repair.md](../plans/p0-php-image-runtime-and-s16-repair.md)

1. [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01] PHP の画像 runtime を実装し、`sample/16` 実行失敗を解消して parity の偽陽性を防ぐ。
2. [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S1-01] PHP 画像出力経路（runtime/emit）の no-op 依存箇所を棚卸しする。
3. [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-01] `src/runtime/php/pytra/runtime/png.php` に PNG 書き出し実装を追加する。
4. [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-02] `src/runtime/php/pytra/runtime/gif.php` に GIF 書き出し実装を追加する。
5. [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-03] PHP emitter/lower の画像保存経路を `__pytra_noop` から runtime 呼び出しへ切り替える。
6. [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-04] PHP emitter/lower の tuple 受け取りを修正し、`sample/16` の未束縛変数参照を解消する。
7. [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S3-01] `tools/runtime_parity_check.py` でケース実行前の既存 artifact 削除を強制する。
8. [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S3-02] `sample/01,06,16` を中心に Python vs PHP の stdout/artifact parity を再確認する。
- 進捗メモ: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S1-01] PHP 画像出力は `emitter->__pytra_noop->runtime stub` で無効化されており、`sample/16` は tuple 受け取り崩れで `DivisionByZeroError` まで再現。
- 進捗メモ: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-01] `png.php` に CRC32/Adler32/stored-deflate を含む pure PHP 実装を追加し、`1x1 RGB` で Python 実装との PNG バイト一致を確認。
- 進捗メモ: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-02] `gif.php` に GIF89a + Clear/Literal LZW 実装を追加し、`2x1x2frames` で Python 実装との GIF バイト一致を確認。
- 進捗メモ: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-03] PHP emitter の画像保存呼び出しを runtime 直呼びへ切替え、`sample/01` と `sample/06` の再変換実行で PNG/GIF 生成を確認。
- 進捗メモ: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-04] PHP emitter の tuple/list 代入を展開代入へ修正し、`sample/16` の未束縛変数を解消して正常完走を確認。
- 進捗メモ: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S3-01] `runtime_parity_check.py` の artifact purge がケース開始時と各ターゲット実行前に必ず走ることを確認。
- 進捗メモ: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S3-02] PHP の artifact 比較を有効化し、`sample/01,06,16` parity（stdout/artifact）が全件 pass（3/3）を確認。

### P0: Ruby `sample/18` parity 失敗（tokenize error）原因調査

文脈: [docs/ja/plans/p0-ruby-s18-tokenize-parity-investigation.md](../plans/p0-ruby-s18-tokenize-parity-investigation.md)

1. [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01] Ruby `sample/18` parity 失敗の根本原因を特定し、修正方針を確定する。
2. [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-01] parity 失敗を再現し、例外発生位置と入力トークン列を採取する。
3. [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-02] Python 版と Ruby 版の tokenize 結果を比較し、最初の乖離点を特定する。
4. [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-01] 乖離を生む変換規則（lower/emitter/runtime）を特定し、責務境界を明確化する。
5. [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-02] 最小再現ケース追加方針（fixture 化）を作成する。
6. [x] [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S3-01] 修正方針（実装箇所・回帰テスト）を確定し、次段修正タスクを起票する。
- 進捗メモ: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-01] `sample/18` Ruby失敗を再現し、`line=0 pos=6 ch==` と生成Ruby側 `single_char_token_tags = {}`（`=` 未登録）を採取。
- 進捗メモ: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S1-02] 同一入力 `let a = 10` で Python は `EQUAL` を生成する一方、Ruby は `pos=6 '='` で停止し、最初の乖離点を辞書初期化欠落に確定。
- 進捗メモ: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-01] Ruby emitter の `Dict` レンダリングが `entries` 非対応（旧 `keys/values` 前提）で、dict literal が `{}` に崩れることを根本原因として特定。
- 進捗メモ: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S2-02] 最小再現は「型注釈付き dict literal + `.get()`」で十分と判断し、fixture 化粒度を `tokenize` 全体ではなく dict literal 経路単体へ確定。
- 進捗メモ: [ID: P0-RUBY-S18-TOKENIZE-INVEST-01-S3-01] 修正方針を `Dict(entries) 対応 + fixture 回帰 + sample/18 parity` に固定し、次段実装 `P0-RUBY-DICT-ENTRY-EMIT-FIX-01` を起票。

### P0: Ruby Dict literal（EAST3 `entries`）emit 修正

文脈: [docs/ja/plans/p0-ruby-dict-entry-emit-fix.md](../plans/p0-ruby-dict-entry-emit-fix.md)

1. [x] [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01] Ruby emitter の dict literal 生成を EAST3 `entries` 形式へ対応させ、`sample/18` parity 失敗を解消する。
2. [x] [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S1-01] `ruby_native_emitter._render_dict_expr` を `entries` 優先でレンダリングし、旧 `keys/values` 形式も後方互換で扱う。
3. [x] [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S1-02] dict literal 最小再現 fixture と Ruby 変換回帰テストを追加する。
4. [x] [ID: P0-RUBY-DICT-ENTRY-EMIT-FIX-01-S2-01] `runtime_parity_check --case-root sample --targets ruby 18_mini_language_interpreter` を通し、失敗解消を確認する。

### P1: `py2x.py` 単一エントリ化（`py2*.py` 廃止、最終的に `py2cpp.py` 削除）

文脈: [docs/ja/plans/p1-py2x-single-entrypoint-remove-legacy-clis.md](../plans/p1-py2x-single-entrypoint-remove-legacy-clis.md)

1. [ ] [ID: P1-PY2X-SINGLE-ENTRY-01] `py2x.py` を唯一の正規入口へ統一し、最終的に `src/py2cpp.py` を削除する。
2. [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S1-01] `tools/` / `test/` / `docs/` / `src/pytra/cli.py` の `py2*.py` 依存箇所を棚卸しし、移行順序を確定する。
3. [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S1-02] `py2cpp.py` 固有機能（`--emit-runtime-cpp`, `--header-output`, `--multi-file` 等）の `py2x` 受け皿仕様を確定する。
4. [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S1-03] selfhost 導線（prepare/build/check）がどの entrypoint 契約に依存しているかを棚卸しし、置換方針を確定する。
5. [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-01] `py2x --target cpp` に `py2cpp` 固有機能を実装し、既存オプションと等価運用できるようにする。
6. [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-02] `tools/` の CLI 呼び出しを `py2x.py --target ...` へ一括置換する。
7. [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-03] `test/` の CLI 呼び出しと契約テストを `py2x` ベースへ移行する。
8. [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-04] `docs/ja` / `docs/en` の使用例と仕様表記を `py2x` 正規入口へ更新する。
9. [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] selfhost スクリプトを `py2cpp.py` 非依存へ移行し、`py2x-selfhost.py` 基準で再配線する。
10. [x] [ID: P1-PY2X-SINGLE-ENTRY-01-S3-01] legacy CLI 撤去前のガードを追加し、`py2*.py` 新規再流入を fail-fast で検出する。
11. [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S3-02] `src/py2cpp.py` を削除し、必要に応じて他 `py2*.py` も同時撤去する。
12. [ ] [ID: P1-PY2X-SINGLE-ENTRY-01-S3-03] 全 transpile/selfhost 回帰を実行し、`py2cpp.py` 削除後の非退行を確認する。
- 進捗メモ: [ID: P1-PY2X-SINGLE-ENTRY-01-S1-01] 依存棚卸しを実施し、`src/pytra/cli.py`・`tools`・`test`・`docs` の legacy CLI 参照分布と移行順（CLI/tools→test→docs→selfhost）を確定。
- 進捗メモ: [ID: P1-PY2X-SINGLE-ENTRY-01-S1-02] `py2cpp` 実利用オプション集合を抽出し、可搬オプションは layer-option マップ、出力モード変更系は `py2x --target cpp` 専用互換フラグで受ける方針を確定。
- 進捗メモ: [ID: P1-PY2X-SINGLE-ENTRY-01-S1-03] selfhost の prepare/build/check が `src/py2cpp.py` 連鎖に依存していることを特定し、通常は `py2x`・selfhost は `py2x-selfhost` へ統一する置換方針を確定。
- 進捗メモ: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-01] `py2x --target cpp` に `py2cpp` 互換委譲を追加し、`optimizer/emitter-option` の C++ キーを専用フラグへマップ。`test_py2x_cli` と single/multi/header 出力で動作確認。
- 進捗メモ: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-02] selfhost 系を除く `tools/` の `src/py2*.py` 直呼びを `src/py2x.py --target ...` へ置換し、`check_py2*_transpile.py` 全件実行で非退行を確認。
- 進捗メモ: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-03] `test/unit` の CLI 実行を `src/py2x.py --target ...` へ統一し、代表 15 ファイルの unittest pass を確認（`test_py2lua_smoke.py` は既知失敗7件を維持）。
- 進捗メモ: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-04] `docs/ja|en/how-to-use.md` の実行例を `py2x --target` + `-o` 基準へ統一し、`spec-user` の対応言語一覧も `py2x` 正規入口表記へ更新。
- 進捗メモ: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] selfhost 系 scripts から `src/py2cpp.py` 直参照を除去し `py2x-selfhost` 基準へ寄せたが、`build_selfhost.py` は生成 C++ コンパイル失敗が残るため本 ID は継続。
- 進捗メモ: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] `prepare_selfhost_source.py` 生成物の host transpile を再開通（`selfhost/py2cpp.py` の missing_module/未lower method 失敗を解消）し、`check_py2cpp_transpile.py`（137/137）で回帰なしを確認。
- 進捗メモ: [ID: P1-PY2X-SINGLE-ENTRY-01-S2-05] `py2x-selfhost.py` を runtime `ArgumentParser` 契約に合わせて再配線（help文字列連結・layer option 変数スコープ・引数定義の署名崩れを解消）し、`build_selfhost.py` の残件を `pytra::compiler::{transpile_cli,backend_registry_static}` 未実体化に絞り込んだ。
- 進捗メモ: [ID: P1-PY2X-SINGLE-ENTRY-01-S3-01] `tools/check_legacy_cli_references.py` を追加し、`src/tools/test` の `src/py2*.py` 直参照・`import py2*` 新規流入を fail-fast 検出できるようにした。

### P2: 多言語 runtime の C++ 同等化（API 契約・機能カバレッジ統一）

文脈: [docs/ja/plans/p2-runtime-parity-with-cpp.md](../plans/p2-runtime-parity-with-cpp.md)

1. [ ] [ID: P2-RUNTIME-PARITY-CPP-01] C++ runtime を基準に、他言語 runtime の API 契約と機能カバレッジを段階的に同等化する。
2. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] C++ runtime の必須 API カタログ（module/function/契約）を抽出する。
3. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] 各言語 runtime の実装有無マトリクスを作成し、欠落/互換/挙動差を分類する。
4. [x] [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] 同等化対象を `Must/Should/Optional` で優先度付けする。
5. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-01] Wave1（`go/java/kotlin/swift`）で `math/time/pathlib/json` 不足 API を実装する。
6. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-02] Wave1 の emitter 呼び出しを adapter 経由へ寄せ、API 名揺れを吸収する。
7. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S2-03] Wave1 の parity 回帰を追加し、runtime 差由来 fail を固定する。
8. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-01] Wave2（`ruby/lua/scala/php`）で不足 API を実装する。
9. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-02] Wave2 の emitter 呼び出しを adapter 経由へ寄せる。
10. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S3-03] Wave2 の parity 回帰を追加し、runtime 差由来 fail を固定する。
11. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-01] Wave3（`js/ts/cs/rs`）で不足 API を補完し、契約差を解消する。
12. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-02] runtime API 欠落検知チェックを追加し、CI/ローカル回帰へ組み込む。
13. [ ] [ID: P2-RUNTIME-PARITY-CPP-01-S4-03] `docs/ja/spec` / `docs/en/spec` に runtime 同等化ポリシーと進捗表を反映する。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S1-01] `docs/ja/spec/spec-runtime.md` に C++ runtime API 正本カタログ（Must/Should）を追加し、Wave 同等化の基準 API を固定。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S1-02] `src/runtime/<lang>/pytra` 棚卸し結果を `native/mono/compat/missing` でマトリクス化し、主要欠落（json/pathlib/gif）を分類。
- 進捗メモ: [ID: P2-RUNTIME-PARITY-CPP-01-S1-03] マトリクス差分を `Must/Should/Optional` へ優先度化し、Wave1/2/3 の着手順（json/pathlib/gif優先）を確定。

### P4: 全言語 selfhost 完全化（低低優先）

文脈: [docs/ja/plans/p4-multilang-selfhost-full-rollout.md](../plans/p4-multilang-selfhost-full-rollout.md)

1. [ ] [ID: P4-MULTILANG-SH-01] `cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua/scala` の selfhost を段階的に成立させ、全言語の multistage 監視を通過可能にする。
2. [ ] [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost の stage2 依存 transpile 失敗を解消し、multistage を通す。
3. [ ] [ID: P4-MULTILANG-SH-01-S3-01] TypeScript の preview-only 状態を解消し、selfhost 実行可能な生成モードへ移行する。
4. [ ] [ID: P4-MULTILANG-SH-01-S3-02] Go/Java/Swift/Kotlin の native backend 化タスクと接続し、selfhost 実行チェーンを有効化する。
5. [ ] [ID: P4-MULTILANG-SH-01-S3-03] Ruby/Lua/Scala3 を selfhost multistage 監視対象へ追加し、runner 未定義状態を解消する。
6. [ ] [ID: P4-MULTILANG-SH-01-S4-01] 全言語 multistage 回帰を CI 導線へ統合し、失敗カテゴリの再発を常時検知できるようにする。
7. [ ] [ID: P4-MULTILANG-SH-01-S4-02] 完了判定テンプレート（各言語の stage 通過条件と除外条件）を文書化し、運用ルールを固定する。
- 完了済み子タスク（`S1-01` 〜 `S2-02-S3`）および過去進捗メモは `docs/ja/todo/archive/20260301.md` へ移管済み。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] JS emitter の selfhost parser 制約違反（`Any` 受け `node.get()/node.items()`）と関数内 `FunctionDef` 未対応を解消し、先頭失敗を `stage1_dependency_transpile_fail` から `self_retranspile_fail (ERR_MODULE_NOT_FOUND: ./pytra/std.js)` まで前進。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost 準備に shim 生成・import 正規化・export 注入・構文置換を追加し、`ERR_MODULE_NOT_FOUND` を解消。先頭失敗は `SyntaxError: Unexpected token ':'`（`raw[qpos:]` 由来）へ遷移。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost 向けに slice/集合判定の source 側縮退、ESM shim 化、import 正規化再設計、`argparse`/`Path` 互換 shim、`.py -> EAST3(JSON)` 入力経路、`JsEmitter` profile loader の selfhost 互換化を段階適用。先頭失敗は `ReferenceError/SyntaxError` 群を解消して `TypeError: CodeEmitter._dict_copy_str_object is not a function` へ遷移。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] `CodeEmitter.load_type_map` と `js_emitter` 初期化の dict access を object-safe 化し、selfhost rewrite に `set/list/dict` polyfill と `CodeEmitter` static alias 補完を追加。先頭失敗は `dict is not defined` を解消して `TypeError: module.get is not a function` へ前進。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] selfhost rewrite を `.get -> __pytra_dict_get` 化し、`Path` shim に `parent/name/stem` property 互換と `mkdir(parents/exist_ok)` 既定冪等化を追加。`js` は `stage1 pass / stage2 pass` に到達し、先頭失敗は `stage3 sample output missing` へ遷移。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] `CodeEmitter/JsEmitter` の object-safe 変換（`startswith/strip/find` 依存除去、`next_tmp` f-string 修正、ASCII helperの `ord/chr` 依存撤去）と selfhost rewrite の String polyfill（`strip/lstrip/rstrip/startswith/endswith/find/lower/upper/map`）を追加。`js` は `stage1/native pass`・`multistage stage2 pass` を維持し、先頭失敗は `stage3 sample_transpile_fail (SyntaxError: Invalid or unexpected token)` へ前進。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] `emit` のインデント生成（文字列乗算）を loop 化し、`quote_string_literal` の `quote` 非文字列防御、`_emit_function` の `in_class` 判定を `None` 依存から空文字判定へ変更。`js` は `stage1/native pass`・`multistage stage2 pass` を維持し、先頭失敗は `stage3 sample_transpile_fail (SyntaxError: Unexpected token '{')` に更新（`py2js_stage2.js` の未解決 placeholder/関数ヘッダ崩れが残件）。
