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

### P0: sample/13 `candidates` 選択式 CSE/hoist 再実施（改善項目 #6）

文脈: [docs/ja/plans/p0-cpp-s13-candidate-index-cse-revisit.md](../plans/p0-cpp-s13-candidate-index-cse-revisit.md)

1. [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02] sample/13 の `candidates` 選択で CSE/hoist を再実施し、重複式を縮退する。
2. [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S1-01] sample/13 の `candidates` 選択で重複している index/要素取得断片を棚卸しする。
3. [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S1-02] 適用境界（型既知・副作用なし・fail-closed）を仕様化する。
4. [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S2-01] CppEmitter で index 計算と要素取得の hoist 出力を実装する。
5. [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S2-02] 適用不可ケースの fallback を固定し、意味保持を担保する。
6. [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S3-01] unit テストを追加し、重複式再発を検知可能にする。
7. [x] [ID: P0-CPP-S13-CANDIDATE-CSE-02-S3-02] `sample/cpp/13` 再生成と transpile チェックで非退行を確認する。
- 進捗メモ: [ID: P0-CPP-S13-CANDIDATE-CSE-02] `Assign(Name=Subscript)` の複雑 index を `auto __idx_*` へ hoist する経路を追加し、sample/13 と unit/transpile 回帰を通過。

### P0: sample/13 C++ tuple 構築の冗長ラップ削減

文脈: [docs/ja/plans/p0-cpp-s13-tuple-construction-slimming.md](../plans/p0-cpp-s13-tuple-construction-slimming.md)

1. [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01] sample/13 の tuple 構築で二重ラップを削減し、最短等価表現へ統一する。
2. [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S1-01] sample/13 の tuple 二重ラップ発生箇所を棚卸しし、適用境界を固定する。
3. [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S1-02] `make_tuple` 直接化と `append/emplace` の適用優先ルールを定義する。
4. [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S2-01] CppEmitter の tuple 構築出力を更新し、二重ラップを除去する。
5. [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S2-02] `append` 系で `emplace_back` 可能な経路を追加し、余分な一時構築を削減する。
6. [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S2-03] 適用不可ケースの fallback を固定し、現行意味を維持する。
7. [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S3-01] unit テストを追加し、二重ラップ再発を検知可能にする。
8. [x] [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01-S3-02] `sample/cpp/13` 再生成と transpile チェックで非退行を確認する。
- 進捗メモ: [ID: P0-CPP-S13-TUPLE-CTOR-SLIM-01] `append(::std::make_tuple(...))` 経路で tuple 冗長 cast を抑止し、sample/13 の `::std::tuple<...>(::std::make_tuple(...))` を撤去。

### P0: sample/13 C++ grid 初期化 IIFE 縮退

文脈: [docs/ja/plans/p0-cpp-s13-grid-init-iife-reduction.md](../plans/p0-cpp-s13-grid-init-iife-reduction.md)

1. [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01] sample/13 の `grid` 初期化で不要 IIFE を縮退し、通常文列へ統一する。
2. [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S1-01] sample/13 の IIFE 初期化断片を棚卸しし、縮退可能条件を固定する。
3. [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S1-02] 「縮退可能 / IIFE維持」の境界条件を仕様化する（fail-closed）。
4. [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S2-01] CppEmitter の初期化出力を更新し、縮退可能パターンで通常文列へ変換する。
5. [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S2-02] fallback 経路を維持し、縮退不可ケースは現行 IIFE 出力に戻す。
6. [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S3-01] unit テストを追加し、IIFE 再発と誤縮退を回帰検知可能にする。
7. [x] [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01-S3-02] `sample/cpp/13` 再生成と transpile チェックで非退行を確認する。
- 進捗メモ: [ID: P0-CPP-S13-GRID-IIFE-REDUCE-01] sample/13 は既に `list<list<int64>>(...)` 初期化へ縮退済みで、IIFE 非出力と回帰コマンド通過を確認。


### P0: EAST3 マーカー経由で C++ tuple unpack を構造化束縛へ縮退

文脈: [docs/ja/plans/p0-east3-cpp-structured-binding-tuple-unpack.md](../plans/p0-east3-cpp-structured-binding-tuple-unpack.md)

1. [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01] EAST3 マーカーで安全条件を固定し、C++ tuple unpack を構造化束縛へ縮退する。
2. [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S1-01] 適用条件（宣言時 unpack / tuple 要素確定 / 非Any-object）を仕様化する。
3. [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S1-02] EAST3 マーカースキーマ（例: `cpp_struct_bind_unpack_v1`）と fail-closed 条件を定義する。
4. [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S2-01] EAST3 optimizer pass で対象 `Assign(Tuple)` へマーカーを付与する。
5. [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S2-02] CppEmitter tuple assign 分岐をマーカー参照型に切替え、構造化束縛出力を実装する。
6. [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S2-03] マーカー不在/不整合時の fallback を固定し、現行 `std::get` 経路を維持する。
7. [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S3-01] unit テストを追加して構造化束縛適用/非適用境界を回帰固定する。
8. [x] [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01-S3-02] `sample/cpp/16` 再生成と transpile チェックで非退行を確認する。
- 進捗メモ: [ID: P0-EAST3-CPP-STRUCT-BIND-UNPACK-01] `cpp_struct_bind_unpack_v1` を `Assign(Tuple)` に付与し、宣言時 unpack を `auto [..]` へ縮退（再代入/union/Any は `std::get` fallback 維持）。

### P0: EAST3 マーカー経由で C++ 空初期化を `= {};` へ縮退

文脈: [docs/ja/plans/p0-east3-cpp-empty-init-shorthand.md](../plans/p0-east3-cpp-empty-init-shorthand.md)

1. [ ] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01] EAST3 マーカーで安全性を確定し、C++ の空初期化を `= {};` に縮退する。
2. [ ] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S1-01] 適用条件（左辺型=右辺空コンテナ型、非Any/object、非boxing）を仕様化する。
3. [ ] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S1-02] EAST3 マーカースキーマ（例: `cpp_empty_init_shorthand_v1`）と fail-closed 条件を定義する。
4. [ ] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S2-01] EAST3 optimizer pass で対象ノードへマーカーを付与する。
5. [ ] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S2-02] C++ emitter をマーカー参照型に切替え、`T x = T{};` を `T x = {};` へ縮退する。
6. [ ] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S2-03] マーカー不在/不整合時の fallback を実装し、既存出力へ戻す。
7. [ ] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S3-01] unit テストを追加し、誤適用（Any/object 経路）と再発を検知可能にする。
8. [ ] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S3-02] `sample/cpp/18` 再生成と transpile チェックで非退行を確認する。

### P0: Scala 出力の冗長括弧（`((...))` / 不要 `(...)`）削減

文脈: [docs/ja/plans/p0-scala-redundant-parentheses-normalization.md](../plans/p0-scala-redundant-parentheses-normalization.md)

1. [ ] [ID: P0-SCALA-PAREN-NORM-01] Scala 出力の冗長括弧を削減し、`sample/scala/01` の可読性を改善する。
2. [ ] [ID: P0-SCALA-PAREN-NORM-01-S1-01] 冗長括弧パターン（`BinOp` / `Compare` / `BoolOp` / 条件式）を棚卸しし、除去対象と保持対象を分類する。
3. [ ] [ID: P0-SCALA-PAREN-NORM-01-S1-02] 優先順位を壊さない最小括弧ルール（必要括弧判定）を仕様化する。
4. [ ] [ID: P0-SCALA-PAREN-NORM-01-S2-01] `Compare` / `BoolOp` の条件式レンダリングで二重括弧を削減する。
5. [ ] [ID: P0-SCALA-PAREN-NORM-01-S2-02] `BinOp` の単純式 fastpath を追加し、不要な外側括弧を削減する。
6. [ ] [ID: P0-SCALA-PAREN-NORM-01-S2-03] 優先順位が必要なケースでは括弧維持するガードを追加する（fail-closed）。
7. [ ] [ID: P0-SCALA-PAREN-NORM-01-S3-01] unit テストを更新し、冗長括弧再発を回帰検知できるようにする。
8. [ ] [ID: P0-SCALA-PAREN-NORM-01-S3-02] `sample/scala/01` 再生成と transpile チェックで非退行を確認する。

### P0: C++ `ForCore` 単文ループの波括弧省略

文脈: [docs/ja/plans/p0-cpp-forcore-single-stmt-brace-omit.md](../plans/p0-cpp-forcore-single-stmt-brace-omit.md)

1. [ ] [ID: P0-CPP-FORCORE-BRACE-OMIT-01] `ForCore` 単文ループで不要な波括弧 `{}` を省略し、C++ 出力可読性を改善する。
2. [ ] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S1-01] `ForCore` の brace 省略条件（単文・安全条件・除外条件）を確定する。
3. [ ] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S2-01] `CppEmitter` の既定 brace 判定へ `ForCore` を追加し、出力経路へ適用する。
4. [ ] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S3-01] unit テストを追加/更新し、`ForCore` 省略回帰を固定する。
5. [ ] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S3-02] `sample/cpp/18` 再生成と transpile チェックで非退行を確認する。

### P1: sample/ruby/03 出力品質改善（Julia hot path）

文脈: [docs/ja/plans/p1-ruby-s03-quality-uplift.md](../plans/p1-ruby-s03-quality-uplift.md)

1. [ ] [ID: P1-RUBY-S03-QUALITY-01] `sample/ruby/03` の生成品質を改善し、可読性とホットパス効率を引き上げる。
2. [ ] [ID: P1-RUBY-S03-QUALITY-01-S1-01] `sample/ruby/03` の冗長断片（`__pytra_div` / append / 初期化 / 括弧 / cast）を棚卸しし、優先順を固定する。
3. [ ] [ID: P1-RUBY-S03-QUALITY-01-S1-02] fail-closed 適用境界（型既知条件、演算意味維持条件）を仕様化する。
4. [ ] [ID: P1-RUBY-S03-QUALITY-01-S2-01] 型既知の割り算経路で `__pytra_div` 依存を削減する emitter fastpath を追加する。
5. [ ] [ID: P1-RUBY-S03-QUALITY-01-S2-02] `pixels.append` 周辺の冗長呼び出しを削減する出力規則を追加する。
6. [ ] [ID: P1-RUBY-S03-QUALITY-01-S2-03] `r/g/b` 初期化の冗長代入を削減する分岐出力へ更新する。
7. [ ] [ID: P1-RUBY-S03-QUALITY-01-S2-04] Ruby 出力の過剰括弧を削減する正規化規則を追加する。
8. [ ] [ID: P1-RUBY-S03-QUALITY-01-S2-05] 同型変換 helper（`__pytra_float/__pytra_int`）の不要呼び出しを抑制する。
9. [ ] [ID: P1-RUBY-S03-QUALITY-01-S3-01] unit/golden 回帰を追加し、冗長パターンの再発を検知可能にする。
10. [ ] [ID: P1-RUBY-S03-QUALITY-01-S3-02] `sample/ruby/03` 再生成と transpile/parity で非退行を確認する。

### P1: sample/18 Rust 出力品質改善（可読性 + ホットパス縮退）

文脈: [docs/ja/plans/p1-rs-s18-quality-uplift.md](../plans/p1-rs-s18-quality-uplift.md)

1. [ ] [ID: P1-RS-S18-QUALITY-01] `sample/rs/18` の生成品質を改善し、可読性とホットパス効率を引き上げる。
2. [ ] [ID: P1-RS-S18-QUALITY-01-S1-01] sample/18 Rust 出力の冗長断片（clone/添字/走査/format）を棚卸しし、改善対象を固定する。
3. [ ] [ID: P1-RS-S18-QUALITY-01-S1-02] 期待効果とリスクで実装順を確定し、fail-closed 適用境界を定義する。
4. [ ] [ID: P1-RS-S18-QUALITY-01-S2-01] `current_token/previous_token/eval_expr` で borrow 優先経路を追加し、不要 `clone` を削減する。
5. [ ] [ID: P1-RS-S18-QUALITY-01-S2-02] 非負添字が確定する経路で index 正規化式を省略する fastpath を追加する。
6. [ ] [ID: P1-RS-S18-QUALITY-01-S2-03] tokenize の文字走査を `String` 汎用経路から軽量経路（bytes/chars）へ縮退する。
7. [ ] [ID: P1-RS-S18-QUALITY-01-S2-04] 小規模固定 token 判定で map 依存を減らし、分岐/lookup を簡素化する。
8. [ ] [ID: P1-RS-S18-QUALITY-01-S2-05] `to_string/format!` 連鎖を簡約し、同値な直接生成へ寄せる。
9. [ ] [ID: P1-RS-S18-QUALITY-01-S2-06] `&Vec<T>` 受けを `&[T]` に縮退できる経路を実装する。
10. [ ] [ID: P1-RS-S18-QUALITY-01-S2-07] `BTreeMap` 利用箇所の必要性を再評価し、順序不要経路を軽量mapへ切替える。
11. [ ] [ID: P1-RS-S18-QUALITY-01-S3-01] unit/golden 回帰を追加し、冗長出力パターンの再発を検知可能にする。
12. [ ] [ID: P1-RS-S18-QUALITY-01-S3-02] `sample/rs/18` 再生成と transpile/smoke/parity で非退行を確認する。

### P1: sample/rs/08 出力品質改善（可読性 + ホットパス縮退）

文脈: [docs/ja/plans/p1-rs-s08-quality-uplift.md](../plans/p1-rs-s08-quality-uplift.md)

1. [ ] [ID: P1-RS-S08-QUALITY-01] `sample/rs/08` の生成品質を改善し、可読性とホットパス効率を引き上げる。
2. [x] [ID: P1-RS-S08-QUALITY-01-S1-01] `sample/rs/08` の冗長箇所（clone/添字正規化/loop/分岐/capture判定/capacity）をコード断片で固定する。
3. [x] [ID: P1-RS-S08-QUALITY-01-S2-01] `capture` 返却の不要 `clone` を削減する出力規則を導入する。
4. [x] [ID: P1-RS-S08-QUALITY-01-S2-02] 非負添字が保証される経路で index 正規化式を省略する fastpath を追加する。
5. [x] [ID: P1-RS-S08-QUALITY-01-S2-03] 単純 `range` 由来ループを Rust `for` へ縮退する fastpath を追加する。
6. [x] [ID: P1-RS-S08-QUALITY-01-S2-04] `if/elif` 連鎖を `else if` / `match` 相当へ簡素化する出力規則を追加する。
7. [ ] [ID: P1-RS-S08-QUALITY-01-S2-05] capture 判定 `%` を next-capture カウンタ方式へ置換する fastpath を追加する。
8. [ ] [ID: P1-RS-S08-QUALITY-01-S2-06] 推定可能な `frames` サイズに対する `reserve` 出力規則を追加する。
9. [ ] [ID: P1-RS-S08-QUALITY-01-S3-01] 回帰テストを追加し、`sample/rs/08` 再生成差分を固定する。
10. [ ] [ID: P1-RS-S08-QUALITY-01-S3-02] transpile/smoke/parity を実行し、非退行を確認する。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S1-01] `sample/rs/08` の冗長断片（clone/添字正規化/loop/分岐/%判定/reserve不足）を固定し、実装優先順を確定。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S2-01] return式上の `bytes(bytearray)` は move 優先で clone を省略し、`sample/rs/08` の `return (frame).clone();` を除去。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S2-02] 簡易 non-negative 解析を追加し、`sample/rs/08` の `grid[y][x]` 経路で負添字正規化式を省略。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S2-03] ascending `step=1` の `ForRange` を `for` fastpath へ切替え、`sample/rs/08` 主ループを `while` から縮退。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S2-04] nested `if` を `else if` 連鎖へ平坦化し、`sample/rs/08` の `d` 分岐を簡素化。

### P2: `from ... import *` 正式対応（wildcard import）

文脈: [docs/ja/plans/p2-wildcard-import-support.md](../plans/p2-wildcard-import-support.md)

1. [ ] [ID: P2-WILDCARD-IMPORT-01] `from M import *` を正式サポートし、解決不能ケースは fail-closed で `input_invalid` に統一する。
2. [ ] [ID: P2-WILDCARD-IMPORT-01-S1-01] wildcard import の公開シンボル決定規則（`__all__` 優先、未定義時 public 名）を仕様化する。
3. [ ] [ID: P2-WILDCARD-IMPORT-01-S1-02] 既存 import 診断契約（unsupported/duplicate/missing）との整合を整理し、エラー分類を固定する。
4. [ ] [ID: P2-WILDCARD-IMPORT-01-S2-01] import graph / export table で wildcard 展開情報を構築し、解決テーブルへ反映する。
5. [ ] [ID: P2-WILDCARD-IMPORT-01-S2-02] 同名衝突・非公開名・未解決 wildcard を fail-closed で検出する。
6. [ ] [ID: P2-WILDCARD-IMPORT-01-S2-03] CLI の wildcard 例外分岐とテスト期待値を正式対応契約へ更新する。
7. [ ] [ID: P2-WILDCARD-IMPORT-01-S3-01] unit/統合テスト（正常系 + 衝突/失敗系）を追加して再発検知を固定する。
8. [ ] [ID: P2-WILDCARD-IMPORT-01-S3-02] `spec-user.md` / `spec-import.md` / TODO の記述を実装契約に同期する。

### P2: sample/18 C++ AST コンテナ値型化

文脈: [docs/ja/plans/p2-cpp-s18-value-container.md](../plans/p2-cpp-s18-value-container.md)

1. [ ] [ID: P2-CPP-S18-VALUE-CONTAINER-01] sample/18 の AST コンテナ値型化（`list<rc<T>> -> list<T>`）を段階導入する。
2. [ ] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S1-01] AST コンテナ利用点を棚卸しし、値型化可能な non-escape 条件を定義する。
3. [ ] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S1-02] EAST3 メタと C++ emitter 連携仕様（ownership hint / fail-closed）を設計する。
4. [ ] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S2-01] sample/18 先行で `expr_nodes` / `stmts` の値型出力を実装する。
5. [ ] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S2-02] 逸脱ケースで `rc` へフォールバックする条件を実装する。
6. [ ] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S3-01] 回帰テスト（型出力断片 + 実行整合）を追加して再発検知を固定する。

### P2: Scala 負例fixtureの skip 撤廃（失敗期待テスト化）

文脈: [docs/ja/plans/p2-scala-negative-fixture-fail-assertion.md](../plans/p2-scala-negative-fixture-fail-assertion.md)

1. [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01] Scala 負例 fixture を skip 運用から「失敗期待の明示テスト」へ移行する。
2. [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S1-01] 負例 fixture の現行失敗理由を棚卸しし、期待する失敗分類を固定する。
3. [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S1-02] `DEFAULT_EXPECTED_FAILS` の stale エントリを除去し、負例集合を最新化する。
4. [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S2-01] `check_py2scala_transpile.py` を正例成功 + 負例失敗期待の両検証モードへ再構成する。
5. [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S2-02] `unexpected pass` / `unexpected error category` を fail-closed で検知する。
6. [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S3-01] unit テストを追加し、skip 再流入を回帰検知する。
7. [ ] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S3-02] `how-to-use` 文書へ Scala の正例/負例検証手順を追記する。

### P3: 非C++ backend へのコンテナ参照管理モデル展開

文脈: [docs/ja/plans/p3-multilang-container-ref-model-rollout.md](../plans/p3-multilang-container-ref-model-rollout.md)

1. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01] non-C++ backend に「動的境界は参照管理、型既知 non-escape は値型」の共通方針を展開する。
2. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-01] backend 別の現行コンテナ所有モデル（値/参照/GC/ARC）を棚卸しし、差分マトリクスを作成する。
3. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-02] 「参照管理境界」「typed/non-escape 縮退」「escape 条件」の共通用語と判定規則を仕様化する。
4. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-01] EAST3 ノードメタに container ownership hint を保持・伝播する最小拡張を設計する。
5. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-02] CodeEmitter 基底で利用する ownership 判定 API（backend 中立）を定義する。
6. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-01] Rust backend に pilot 実装し、`object` 境界と typed 値型経路の出し分けを追加する。
7. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-02] GC 系 backend（Java or Kotlin）に pilot 実装し、同一判定規則で縮退を確認する。
8. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-03] pilot 2 backend の回帰テスト（unit + sample 断片）を追加し、再発検知を固定する。
9. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01] `cs/js/ts/go/swift/ruby/lua` へ順次展開し、backend ごとの差分を吸収する。
10. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-02] parity/smoke を実行して non-regression を確認し、未達は blocker として分離記録する。
11. [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S5-01] `docs/ja/how-to-use.md` と backend 仕様へ運用ルール（参照管理境界・rollback）を追記する。

### P3: CodeEmitter から C# selfhost 起因修正を隔離

文脈: [docs/ja/plans/p3-codeemitter-cs-isolation.md](../plans/p3-codeemitter-cs-isolation.md)

1. [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01] C# selfhost 起因の修正を `CodeEmitter` から隔離し、共通層の責務を backend 中立へ戻す。
2. [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-01] `v0.4.0` 以降の `CodeEmitter` 差分を棚卸しし、「共通必須 / C# 固有 / 判定保留」の3分類を作成する。
3. [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-02] 「共通必須」の判定基準（backend 中立性・他言語利用実績・fail-closed 必要性）を明文化する。
4. [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-01] 「C# 固有」変更を `CSharpEmitter` / C# runtime / selfhost 準備層へ移管する。
5. [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-02] `CodeEmitter` から C# 固有回避コードを除去し、共通実装へ戻す。
6. [ ] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S3-01] unit/selfhost 回帰を実施し、C# pass 維持と他 backend 非退行を確認する。

### P4: 全言語 selfhost 完全化（低低優先）

文脈: [docs/ja/plans/p4-multilang-selfhost-full-rollout.md](../plans/p4-multilang-selfhost-full-rollout.md)

1. [ ] [ID: P4-MULTILANG-SH-01] `cpp/rs/cs/js/ts/go/java/swift/kotlin` の selfhost を段階的に成立させ、全言語の multistage 監視を通過可能にする。
2. [ ] [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost の stage2 依存 transpile 失敗を解消し、multistage を通す。
3. [ ] [ID: P4-MULTILANG-SH-01-S3-01] TypeScript の preview-only 状態を解消し、selfhost 実行可能な生成モードへ移行する。
4. [ ] [ID: P4-MULTILANG-SH-01-S3-02] Go/Java/Swift/Kotlin の native backend 化タスクと接続し、selfhost 実行チェーンを有効化する。
5. [ ] [ID: P4-MULTILANG-SH-01-S4-01] 全言語 multistage 回帰を CI 導線へ統合し、失敗カテゴリの再発を常時検知できるようにする。
6. [ ] [ID: P4-MULTILANG-SH-01-S4-02] 完了判定テンプレート（各言語の stage 通過条件と除外条件）を文書化し、運用ルールを固定する。
- 完了済み子タスク（`S1-01` 〜 `S2-02-S3`）および過去進捗メモは `docs/ja/todo/archive/20260301.md` へ移管済み。
