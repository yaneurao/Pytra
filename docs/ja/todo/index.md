# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-02

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

### P0: EAST3 変数 lifetime 解析基盤の導入（backend 共通）

文脈: [docs/ja/plans/p0-east3-lifetime-analysis-foundation.md](../plans/p0-east3-lifetime-analysis-foundation.md)

1. [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01] EAST3 に backend 非依存の lifetime 注釈（def/use・live-range・last-use）を導入し、non-escape 解析と統合する。
2. [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S1-01] lifetime 注釈スキーマと fail-closed 規則を仕様化する。
3. [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S1-02] block-local CFG と def-use index 生成基盤を追加する。
4. [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S2-01] backward data-flow で liveness 固定点計算を実装する。
5. [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S2-02] last-use / live-range 注釈をノード `meta` へ付与する。
6. [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S2-03] non-escape summary と lifetime 判定を統合し、escape 値を候補から除外する。
7. [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S3-01] 分岐・ループ・tuple unpack・call を含む unit テストで回帰を固定する。
8. [x] [ID: P0-EAST3-LIFETIME-ANALYSIS-01-S3-02] optimizer 回帰 + transpile smoke（`cpp/rs`）で非退行を確認する。

### P0: sample 多言語出力の正しさ修正（Scala/C#）

文脈: [docs/ja/plans/p0-sample-multilang-output-correctness-fixes.md](../plans/p0-sample-multilang-output-correctness-fixes.md)

1. [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01] sample 出力の正しさ不備（Scala 演算子優先順位 / C# typed 除算）を修正する。
2. [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S1-01] Scala emitter で算術式の優先順位保持を修正し、`sample/scala/01` の崩れ式を解消する。
3. [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S1-02] C# emitter の typed 除算出力を修正し、整数除算経路を除去する。
4. [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S2-01] Scala/C# の回帰テストを追加し、同種退行を固定する。
5. [x] [ID: P0-SAMPLE-OUTPUT-CORRECTNESS-01-S2-02] `sample/01` 再生成 + parity で非退行を確認する。

### P1: sample 多言語出力の型既知 fastpath 強化（品質改善）

文脈: [docs/ja/plans/p1-sample-multilang-output-quality-uplift.md](../plans/p1-sample-multilang-output-quality-uplift.md)

1. [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01] 多言語 sample 出力の型既知 fastpath を強化し、`Any/Object` 退化と helper/cast 過多を削減する。
2. [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-01] `go/java` の `Any/Object` 退化 hotspot（`sample/18`）を棚卸しし、typed fastpath の適用境界を固定する。
3. [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-02] `kotlin/swift/scala` の helper/cast 連鎖（`__pytra_int/float`, `asInstanceOf`）を棚卸しし、削減優先順を確定する。
4. [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S1-03] `rs/js/ts` のループ冗長パターン（`__for_i` 再代入、`__start_N`）の縮退規則を仕様化する。
5. [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-01] `go/java` emitter に typed container/typed access fastpath を実装する。
6. [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-02] `kotlin/swift/scala` emitter に cast/helper 抑制 fastpath を実装する。
7. [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S2-03] `rs/js/ts` emitter に canonical loop 出力を実装し、冗長一時変数を削減する。
8. [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S3-01] 言語別回帰テストを追加し、退化再発を検知可能にする。
9. [x] [ID: P1-SAMPLE-OUTPUT-QUALITY-01-S3-02] 対象 sample を再生成し、smoke/transpile/parity で非退行を確認する。

### P2: sample 多言語出力の可読性縮退（冗長構文整理）

文脈: [docs/ja/plans/p2-sample-multilang-output-readability-uplift.md](../plans/p2-sample-multilang-output-readability-uplift.md)

1. [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01] sample 出力の冗長構文（不要括弧/補助変数/append連鎖）を整理し、可読性を改善する。
2. [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S1-01] 各言語の冗長構文パターンを棚卸しし、適用境界を定義する。
3. [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-01] `js/ts` の loop 補助変数（`__start_N`）を簡約する出力規則を実装する。
4. [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-02] `ruby/lua` の append 連鎖を簡約する出力規則を実装する。
5. [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S2-03] `java` の冗長括弧/step 変数の簡約規則を実装する。
6. [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S3-01] 回帰テストを追加して可読性退行を検知可能にする。
7. [x] [ID: P2-SAMPLE-OUTPUT-READABILITY-01-S3-02] 対象 sample を再生成し、transpile/parity で非退行を確認する。

### P3: PHP backend 追加（EAST3 -> PHP native）

文脈: [docs/ja/plans/p3-php-backend-rollout.md](../plans/p3-php-backend-rollout.md)

1. [ ] [ID: P3-PHP-BACKEND-01] 変換対象言語として PHP を追加し、`EAST3 -> PHP native` 生成経路を成立させる。
2. [x] [ID: P3-PHP-BACKEND-01-S1-01] 対応構文・非対応構文・runtime 分離契約を仕様化する。
3. [x] [ID: P3-PHP-BACKEND-01-S1-02] `src/py2php.py` と profile loader を追加し、CLI 導線を確立する。
4. [ ] [ID: P3-PHP-BACKEND-01-S2-01] PHP native emitter 骨格（関数・分岐・ループ・基本式）を実装する。
5. [ ] [ID: P3-PHP-BACKEND-01-S2-02] class/inheritance と container 操作の最低限 lower を実装する。
6. [ ] [ID: P3-PHP-BACKEND-01-S2-03] runtime helper を `src/runtime/php/pytra/` へ分離し、生成コードから参照する方式へ統一する。
7. [ ] [ID: P3-PHP-BACKEND-01-S3-01] `test_py2php_smoke.py` と `check_py2php_transpile.py` を追加し、回帰導線を整備する。
8. [ ] [ID: P3-PHP-BACKEND-01-S3-02] `runtime_parity_check` / `regenerate_samples` に PHP を統合し、`sample/php` を再生成する。
9. [ ] [ID: P3-PHP-BACKEND-01-S3-03] docs（how-to-use/spec/README 系）の PHP backend 記載を更新する。

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
