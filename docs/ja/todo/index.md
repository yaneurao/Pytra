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

1. [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01] EAST3 マーカーで安全性を確定し、C++ の空初期化を `= {};` に縮退する。
2. [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S1-01] 適用条件（左辺型=右辺空コンテナ型、非Any/object、非boxing）を仕様化する。
3. [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S1-02] EAST3 マーカースキーマ（例: `cpp_empty_init_shorthand_v1`）と fail-closed 条件を定義する。
4. [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S2-01] EAST3 optimizer pass で対象ノードへマーカーを付与する。
5. [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S2-02] C++ emitter をマーカー参照型に切替え、`T x = T{};` を `T x = {};` へ縮退する。
6. [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S2-03] マーカー不在/不整合時の fallback を実装し、既存出力へ戻す。
7. [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S3-01] unit テストを追加し、誤適用（Any/object 経路）と再発を検知可能にする。
8. [x] [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01-S3-02] `sample/cpp/18` 再生成と transpile チェックで非退行を確認する。
- 進捗メモ: [ID: P0-EAST3-CPP-EMPTY-INIT-SHORTHAND-01] `cpp_empty_init_shorthand_v1` を追加し、空 `List/Dict/Set` の安全ケースを `= {};` へ縮退（Any/object/union/不整合は既存 `T{}` fallback）。

### P0: Scala 出力の冗長括弧（`((...))` / 不要 `(...)`）削減

文脈: [docs/ja/plans/p0-scala-redundant-parentheses-normalization.md](../plans/p0-scala-redundant-parentheses-normalization.md)

1. [x] [ID: P0-SCALA-PAREN-NORM-01] Scala 出力の冗長括弧を削減し、`sample/scala/01` の可読性を改善する。
2. [x] [ID: P0-SCALA-PAREN-NORM-01-S1-01] 冗長括弧パターン（`BinOp` / `Compare` / `BoolOp` / 条件式）を棚卸しし、除去対象と保持対象を分類する。
3. [x] [ID: P0-SCALA-PAREN-NORM-01-S1-02] 優先順位を壊さない最小括弧ルール（必要括弧判定）を仕様化する。
4. [x] [ID: P0-SCALA-PAREN-NORM-01-S2-01] `Compare` / `BoolOp` の条件式レンダリングで二重括弧を削減する。
5. [x] [ID: P0-SCALA-PAREN-NORM-01-S2-02] `BinOp` の単純式 fastpath を追加し、不要な外側括弧を削減する。
6. [x] [ID: P0-SCALA-PAREN-NORM-01-S2-03] 優先順位が必要なケースでは括弧維持するガードを追加する（fail-closed）。
7. [x] [ID: P0-SCALA-PAREN-NORM-01-S3-01] unit テストを更新し、冗長括弧再発を回帰検知できるようにする。
8. [x] [ID: P0-SCALA-PAREN-NORM-01-S3-02] `sample/scala/01` 再生成と transpile チェックで非退行を確認する。
- 進捗メモ: [ID: P0-SCALA-PAREN-NORM-01] `If/While/ForCore` 条件の二重括弧を正規化し、`BinOp` 単純式 fastpath で不要括弧を削減。Scala smoke/transpile と `sample/scala/01` 再生成を通過。

### P0: C++ `ForCore` 単文ループの波括弧省略

文脈: [docs/ja/plans/p0-cpp-forcore-single-stmt-brace-omit.md](../plans/p0-cpp-forcore-single-stmt-brace-omit.md)

1. [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01] `ForCore` 単文ループで不要な波括弧 `{}` を省略し、C++ 出力可読性を改善する。
2. [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S1-01] `ForCore` の brace 省略条件（単文・安全条件・除外条件）を確定する。
3. [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S2-01] `CppEmitter` の既定 brace 判定へ `ForCore` を追加し、出力経路へ適用する。
4. [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S3-01] unit テストを追加/更新し、`ForCore` 省略回帰を固定する。
5. [x] [ID: P0-CPP-FORCORE-BRACE-OMIT-01-S3-02] `sample/cpp/18` 再生成と transpile チェックで非退行を確認する。
- 進捗メモ: [ID: P0-CPP-FORCORE-BRACE-OMIT-01] `StaticRangeForPlan + NameTarget` の単文 `ForCore` で brace 省略を有効化し、unit/transpile と `sample/cpp/18` 再生成で `for (...)` 単文出力を確認。

### P1: sample/ruby/03 出力品質改善（Julia hot path）

文脈: [docs/ja/plans/p1-ruby-s03-quality-uplift.md](../plans/p1-ruby-s03-quality-uplift.md)

1. [x] [ID: P1-RUBY-S03-QUALITY-01] `sample/ruby/03` の生成品質を改善し、可読性とホットパス効率を引き上げる。
2. [x] [ID: P1-RUBY-S03-QUALITY-01-S1-01] `sample/ruby/03` の冗長断片（`__pytra_div` / append / 初期化 / 括弧 / cast）を棚卸しし、優先順を固定する。
3. [x] [ID: P1-RUBY-S03-QUALITY-01-S1-02] fail-closed 適用境界（型既知条件、演算意味維持条件）を仕様化する。
4. [x] [ID: P1-RUBY-S03-QUALITY-01-S2-01] 型既知の割り算経路で `__pytra_div` 依存を削減する emitter fastpath を追加する。
5. [x] [ID: P1-RUBY-S03-QUALITY-01-S2-02] `pixels.append` 周辺の冗長呼び出しを削減する出力規則を追加する。
6. [x] [ID: P1-RUBY-S03-QUALITY-01-S2-03] `r/g/b` 初期化の冗長代入を削減する分岐出力へ更新する。
7. [x] [ID: P1-RUBY-S03-QUALITY-01-S2-04] Ruby 出力の過剰括弧を削減する正規化規則を追加する。
8. [x] [ID: P1-RUBY-S03-QUALITY-01-S2-05] 同型変換 helper（`__pytra_float/__pytra_int`）の不要呼び出しを抑制する。
9. [x] [ID: P1-RUBY-S03-QUALITY-01-S3-01] unit/golden 回帰を追加し、冗長パターンの再発を検知可能にする。
10. [x] [ID: P1-RUBY-S03-QUALITY-01-S3-02] `sample/ruby/03` 再生成と transpile/parity で非退行を確認する。
- 進捗メモ: [ID: P1-RUBY-S03-QUALITY-01-S1-01] `sample/ruby/03` の冗長断片を `__pytra_div`/append3連/`r,g,b` 初期化/括弧/cast に分類し、hot path 優先順と fail-closed 境界（型既知 numeric 限定）を確定。
- 進捗メモ: [ID: P1-RUBY-S03-QUALITY-01-S2-04] `_strip_outer_parens` + `BinOp` precedence guard を追加し、`sample/ruby/03` の `if/while` 二重括弧と `zx2 = (zx * zx)` 系を縮退（`03_julia_set` parity 通過）。
- 進捗メモ: [ID: P1-RUBY-S03-QUALITY-01-S2-02] 連続 `append` を `concat([...])` へ縮退する peephole を追加し、`sample/ruby/01,03` で `pixels.concat([r, g, b])` を確認（`03_julia_set` parity 通過）。
- 進捗メモ: [ID: P1-RUBY-S03-QUALITY-01-S3-01] `test_py2rb_smoke` に括弧縮退 + `pixels.concat` の回帰検知を追加し、再発検知を固定。
- 進捗メモ: [ID: P1-RUBY-S03-QUALITY-01-S3-02] `sample/ruby/01,03` を再生成し、`runtime_parity_check --case-root sample --targets ruby --ignore-unstable-stdout 03_julia_set` を再通過。
- 進捗メモ: [ID: P1-RUBY-S03-QUALITY-01-S2-01] `Div` の右辺が非ゼロ数値定数のときのみ direct `/` fastpath を追加し、`sample/ruby/06` の `254.0` 除算で `__pytra_div` を削減（`03/06` parity 通過）。
- 進捗メモ: [ID: P1-RUBY-S03-QUALITY-01-S2-05] float cast で数値定数を literal 化（`2 -> 2.0`）し、`__pytra_float(<const>)` 呼び出しを抑制。`03/06` parity を再通過。
- 進捗メモ: [ID: P1-RUBY-S03-QUALITY-01-S2-03] `r/g/b` の pre-init + `if` 冗長パターンを保守的 peephole で除去し、`sample/ruby/03` で pre-init 行を削減（parity 通過）。

### P1: sample/18 Rust 出力品質改善（可読性 + ホットパス縮退）

文脈: [docs/ja/plans/p1-rs-s18-quality-uplift.md](../plans/p1-rs-s18-quality-uplift.md)

1. [x] [ID: P1-RS-S18-QUALITY-01] `sample/rs/18` の生成品質を改善し、可読性とホットパス効率を引き上げる。
2. [x] [ID: P1-RS-S18-QUALITY-01-S1-01] sample/18 Rust 出力の冗長断片（clone/添字/走査/format）を棚卸しし、改善対象を固定する。
3. [x] [ID: P1-RS-S18-QUALITY-01-S1-02] 期待効果とリスクで実装順を確定し、fail-closed 適用境界を定義する。
4. [x] [ID: P1-RS-S18-QUALITY-01-S2-01] `current_token/previous_token/eval_expr` で borrow 優先経路を追加し、不要 `clone` を削減する。
5. [x] [ID: P1-RS-S18-QUALITY-01-S2-02] 非負添字が確定する経路で index 正規化式を省略する fastpath を追加する。
6. [x] [ID: P1-RS-S18-QUALITY-01-S2-03] tokenize の文字走査を `String` 汎用経路から軽量経路（bytes/chars）へ縮退する。
7. [x] [ID: P1-RS-S18-QUALITY-01-S2-04] 小規模固定 token 判定で map 依存を減らし、分岐/lookup を簡素化する。
8. [x] [ID: P1-RS-S18-QUALITY-01-S2-05] `to_string/format!` 連鎖を簡約し、同値な直接生成へ寄せる。
9. [x] [ID: P1-RS-S18-QUALITY-01-S2-06] `&Vec<T>` 受けを `&[T]` に縮退できる経路を実装する。
10. [x] [ID: P1-RS-S18-QUALITY-01-S2-07] `BTreeMap` 利用箇所の必要性を再評価し、順序不要経路を軽量mapへ切替える。
11. [x] [ID: P1-RS-S18-QUALITY-01-S3-01] unit/golden 回帰を追加し、冗長出力パターンの再発を検知可能にする。
12. [x] [ID: P1-RS-S18-QUALITY-01-S3-02] `sample/rs/18` 再生成と transpile/smoke/parity で非退行を確認する。
- 進捗メモ: [ID: P1-RS-S18-QUALITY-01-S1-01] sample/18 Rust の冗長断片を `clone`/添字正規化/走査/format連鎖/`&Vec<T>` で棚卸しし、改善対象を固定。
- 進捗メモ: [ID: P1-RS-S18-QUALITY-01-S1-02] 実装順を `borrow -> 添字 -> &[T] -> 文字列 -> 走査 -> token判定 -> map再評価` に固定し、fail-closed 境界を定義。
- 進捗メモ: [ID: P1-RS-S18-QUALITY-01-S2-06] 借用 list 引数の型を `&Vec<T>` から `&[T]` へ縮退し、`sample/rs/18` の `tokenize/eval_expr/execute` 署名で確認（transpile/parity 通過）。
- 進捗メモ: [ID: P1-RS-S18-QUALITY-01-S2-01] `AnnAssign` の list 添字初期化で borrow 優先経路を追加し、`eval_expr` の `ExprNode` 取得を clone から `&ExprNode` 参照へ縮退（unit/transpile/parity 通過）。
- 進捗メモ: [ID: P1-RS-S18-QUALITY-01-S2-02] `if` 条件の then 節限定で符号ヒントを導入し、`single_tag > 0` 配下の `single_char_token_kinds[single_tag - 1]` から負添字正規化式を除去（unit/transpile/parity 通過）。
- 進捗メモ: [ID: P1-RS-S18-QUALITY-01-S2-03] `str` 添字の非負確定経路で `py_str_at_nonneg` を導入し、`sample/rs/18` tokenize ホットパスを軽量化（unit/transpile/parity 通過）。
- 進捗メモ: [ID: P1-RS-S18-QUALITY-01-S2-04] 小規模固定 `dict[str, const]` の `get` を `match` へ縮退し、`sample/rs/18` の token 判定 lookup を簡素化（unit/transpile/parity 通過）。
- 進捗メモ: [ID: P1-RS-S18-QUALITY-01-S2-05] cast 無し `str` Add 連鎖を `format!` 1回へ平坦化し、`sample/rs/18` の nested `format!` を削減（unit/transpile/parity 通過）。
- 進捗メモ: [ID: P1-RS-S18-QUALITY-01-S2-07] 順序依存解析（`items/keys/values`・dict反復・外部不明呼び出し）を追加し、順序不要な `dict[str,int64]` の `env` 経路を `HashMap` へ縮退（unit/transpile/parity 通過）。
- 進捗メモ: [ID: P1-RS-S18-QUALITY-01-S3-01] `test_py2rs_smoke` に `single_tag` 添字 fastpath / `py_str_at_nonneg` / nested `format!` 非出力の回帰検知を追加。
- 進捗メモ: [ID: P1-RS-S18-QUALITY-01-S3-02] `sample/rs/18` 再生成と `test_py2rs_smoke` / `check_py2rs_transpile` / parity（case18）を再通過。

### P1: sample/rs/08 出力品質改善（可読性 + ホットパス縮退）

文脈: [docs/ja/plans/p1-rs-s08-quality-uplift.md](../plans/p1-rs-s08-quality-uplift.md)

1. [x] [ID: P1-RS-S08-QUALITY-01] `sample/rs/08` の生成品質を改善し、可読性とホットパス効率を引き上げる。
2. [x] [ID: P1-RS-S08-QUALITY-01-S1-01] `sample/rs/08` の冗長箇所（clone/添字正規化/loop/分岐/capture判定/capacity）をコード断片で固定する。
3. [x] [ID: P1-RS-S08-QUALITY-01-S2-01] `capture` 返却の不要 `clone` を削減する出力規則を導入する。
4. [x] [ID: P1-RS-S08-QUALITY-01-S2-02] 非負添字が保証される経路で index 正規化式を省略する fastpath を追加する。
5. [x] [ID: P1-RS-S08-QUALITY-01-S2-03] 単純 `range` 由来ループを Rust `for` へ縮退する fastpath を追加する。
6. [x] [ID: P1-RS-S08-QUALITY-01-S2-04] `if/elif` 連鎖を `else if` / `match` 相当へ簡素化する出力規則を追加する。
7. [x] [ID: P1-RS-S08-QUALITY-01-S2-05] capture 判定 `%` を next-capture カウンタ方式へ置換する fastpath を追加する。
8. [x] [ID: P1-RS-S08-QUALITY-01-S2-06] 推定可能な `frames` サイズに対する `reserve` 出力規則を追加する。
9. [x] [ID: P1-RS-S08-QUALITY-01-S3-01] 回帰テストを追加し、`sample/rs/08` 再生成差分を固定する。
10. [x] [ID: P1-RS-S08-QUALITY-01-S3-02] transpile/smoke/parity を実行し、非退行を確認する。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S1-01] `sample/rs/08` の冗長断片（clone/添字正規化/loop/分岐/%判定/reserve不足）を固定し、実装優先順を確定。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S2-01] return式上の `bytes(bytearray)` は move 優先で clone を省略し、`sample/rs/08` の `return (frame).clone();` を除去。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S2-02] 簡易 non-negative 解析を追加し、`sample/rs/08` の `grid[y][x]` 経路で負添字正規化式を省略。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S2-03] ascending `step=1` の `ForRange` を `for` fastpath へ切替え、`sample/rs/08` 主ループを `while` から縮退。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S2-04] nested `if` を `else if` 連鎖へ平坦化し、`sample/rs/08` の `d` 分岐を簡素化。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S2-05] `for` fastpath 内で `if i % capture_every == 0` を `next_capture` 比較 + 加算へ置換し、`sample/rs/08` から `%` 判定を除去（unit/transpile/parity 通過）。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S2-06] 同変換ループで `frames.push(...)` を検出した場合、`ceil(steps_total/capture_every)` 見積りで `frames.reserve(...)` を導入。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S3-01] `test_py2rs_smoke` に `next_capture` 変換と `frames.reserve` 出力の回帰検知を追加。
- 進捗メモ: [ID: P1-RS-S08-QUALITY-01-S3-02] `sample/rs/08` 再生成と `test_py2rs_smoke` / `check_py2rs_transpile` / parity（case08）を再通過。

### P2: `from ... import *` 正式対応（wildcard import）

文脈: [docs/ja/plans/p2-wildcard-import-support.md](../plans/p2-wildcard-import-support.md)

1. [x] [ID: P2-WILDCARD-IMPORT-01] `from M import *` を正式サポートし、解決不能ケースは fail-closed で `input_invalid` に統一する。
2. [x] [ID: P2-WILDCARD-IMPORT-01-S1-01] wildcard import の公開シンボル決定規則（`__all__` 優先、未定義時 public 名）を仕様化する。
3. [x] [ID: P2-WILDCARD-IMPORT-01-S1-02] 既存 import 診断契約（unsupported/duplicate/missing）との整合を整理し、エラー分類を固定する。
4. [x] [ID: P2-WILDCARD-IMPORT-01-S2-01] import graph / export table で wildcard 展開情報を構築し、解決テーブルへ反映する。
5. [x] [ID: P2-WILDCARD-IMPORT-01-S2-02] 同名衝突・非公開名・未解決 wildcard を fail-closed で検出する。
6. [x] [ID: P2-WILDCARD-IMPORT-01-S2-03] CLI の wildcard 例外分岐とテスト期待値を正式対応契約へ更新する。
7. [x] [ID: P2-WILDCARD-IMPORT-01-S3-01] unit/統合テスト（正常系 + 衝突/失敗系）を追加して再発検知を固定する。
8. [x] [ID: P2-WILDCARD-IMPORT-01-S3-02] `spec-user.md` / `spec-import.md` / TODO の記述を実装契約に同期する。
- 進捗メモ: [ID: P2-WILDCARD-IMPORT-01] wildcard を `__all__` 優先/public fallback で解決し、`unresolved_wildcard` fail-closed・重複検出・CLI/回帰テスト・spec 同期まで完了。

### P2: sample/18 C++ AST コンテナ値型化

文脈: [docs/ja/plans/p2-cpp-s18-value-container.md](../plans/p2-cpp-s18-value-container.md)

1. [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01] sample/18 の AST コンテナ値型化（`list<rc<T>> -> list<T>`）を段階導入する。
2. [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S1-01] AST コンテナ利用点を棚卸しし、値型化可能な non-escape 条件を定義する。
3. [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S1-02] EAST3 メタと C++ emitter 連携仕様（ownership hint / fail-closed）を設計する。
4. [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S2-01] sample/18 先行で `expr_nodes` / `stmts` の値型出力を実装する。
5. [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S2-02] 逸脱ケースで `rc` へフォールバックする条件を実装する。
6. [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S3-01] 回帰テスト（型出力断片 + 実行整合）を追加して再発検知を固定する。
- 進捗メモ: [ID: P2-CPP-S18-VALUE-CONTAINER-01-S1-02] sample/18 の `expr_nodes`/`stmts` について non-escape 条件を棚卸しし、`container_ownership_hint_v1` を使う EAST3→CppEmitter 連携仕様（safe 時のみ `list<T>`、不成立時 `list<rc<T>>` fallback）を確定。
- 進捗メモ: [ID: P2-CPP-S18-VALUE-CONTAINER-01] dataclass の保守的 value 判定 + `cpp_list_model=pyobj` の `list[ValueClass]` typed 維持を実装し、sample/18 を `list<Token/ExprNode/StmtNode>` へ縮退。unit/transpile/parity を再通過。

### P2: Scala 負例fixtureの skip 撤廃（失敗期待テスト化）

文脈: [docs/ja/plans/p2-scala-negative-fixture-fail-assertion.md](../plans/p2-scala-negative-fixture-fail-assertion.md)

1. [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01] Scala 負例 fixture を skip 運用から「失敗期待の明示テスト」へ移行する。
2. [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S1-01] 負例 fixture の現行失敗理由を棚卸しし、期待する失敗分類を固定する。
3. [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S1-02] `DEFAULT_EXPECTED_FAILS` の stale エントリを除去し、負例集合を最新化する。
4. [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S2-01] `check_py2scala_transpile.py` を正例成功 + 負例失敗期待の両検証モードへ再構成する。
5. [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S2-02] `unexpected pass` / `unexpected error category` を fail-closed で検知する。
6. [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S3-01] unit テストを追加し、skip 再流入を回帰検知する。
7. [x] [ID: P2-SCALA-NEGATIVE-ASSERT-01-S3-02] `how-to-use` 文書へ Scala の正例/負例検証手順を追記する。
- 進捗メモ: [ID: P2-SCALA-NEGATIVE-ASSERT-01] `check_py2scala_transpile.py` を skip 廃止の fail-closed 検証へ更新し、負例5件のカテゴリ一致 (`user_syntax_error` / `unsupported_by_design`) を固定。`ng_untyped_param` stale 除去・unit追加・ja/en how-to 反映まで完了。

### P3: 非C++ backend へのコンテナ参照管理モデル展開

文脈: [docs/ja/plans/p3-multilang-container-ref-model-rollout.md](../plans/p3-multilang-container-ref-model-rollout.md)

1. [x] [ID: P3-MULTILANG-CONTAINER-REF-01] non-C++ backend に「動的境界は参照管理、型既知 non-escape は値型」の共通方針を展開する。
2. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-01] backend 別の現行コンテナ所有モデル（値/参照/GC/ARC）を棚卸しし、差分マトリクスを作成する。
3. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-02] 「参照管理境界」「typed/non-escape 縮退」「escape 条件」の共通用語と判定規則を仕様化する。
4. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-01] EAST3 ノードメタに container ownership hint を保持・伝播する最小拡張を設計する。
5. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-02] CodeEmitter 基底で利用する ownership 判定 API（backend 中立）を定義する。
6. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-01] Rust backend に pilot 実装し、`object` 境界と typed 値型経路の出し分けを追加する。
7. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-02] GC 系 backend（Java or Kotlin）に pilot 実装し、同一判定規則で縮退を確認する。
8. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-03] pilot 2 backend の回帰テスト（unit + sample 断片）を追加し、再発検知を固定する。
9. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01] `cs/js/ts/go/swift/ruby/lua` へ順次展開し、backend ごとの差分を吸収する。
10. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S1-01] C# backend へ展開し、ref境界引数コンテナの copy ctor 材料化を導入する。
11. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S2-01] JS/TS backend へ展開し、動的 helper 境界で同一判定規則を適用する。
12. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S3-01] Go backend へ展開し、`any` 境界と typed 値型経路を分離する。
13. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S4-01] Swift backend へ展開し、`Any` 境界と typed 値型経路を分離する。
14. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S5-01] Ruby backend へ展開し、動的 helper 境界と局所値経路の材料化規則を追加する。
15. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S6-01] Lua backend へ展開し、table helper 境界と局所値経路の材料化規則を追加する。
16. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-02] parity/smoke を実行して non-regression を確認し、未達は blocker として分離記録する。
17. [x] [ID: P3-MULTILANG-CONTAINER-REF-01-S5-01] `docs/ja/how-to-use.md` と backend 仕様へ運用ルール（参照管理境界・rollback）を追記する。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S1-02] backend 差分マトリクス（`rs/cs/go/java/kotlin/swift` の typed+Any fallback と `js/ts/ruby/lua` の動的helper中心）を整理し、`container_ref_boundary` / `typed_non_escape_value_path` / `escape_condition` の共通語彙と fail-closed 判定を v1 化。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S2-02] EAST3 `container_ownership_hints_v1` と `meta.container_ownership_hint_ref` の最小契約、ならびに CodeEmitter 基底 API（hint解決/境界分類/value_path 判定）を設計して責務境界を固定。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S3-02] Kotlin emitter に `ref_vars` と `AnnAssign/Assign` の `toMutableList()/toMutableMap()` 材料化を実装し、GC backend pilot を同一境界規則で導入。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S3-03] `test_py2kotlin_smoke` 回帰を追加し、`check_py2kotlin_transpile` と sample parity(case18) を再通過して再発検知を固定。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S3-01] Rust pilot として、参照引数（`&[T]` など）を値型ローカルへ初期化する際の `to_vec()/clone()` 材料化を追加し、`test_py2rs_smoke` 新規回帰 + `check_py2rs_transpile` + sample/18 parity(rs) を再通過。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S1-01] C# emitter に `current_ref_vars` と copy ctor 材料化（`new List/Dictionary/HashSet(... )`）を導入し、`test_py2cs_smoke` と sample parity(case18) を通過。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S2-01] JS emitter に ref-container 材料化（`slice/Array.from`・object spread・`new Set`）を導入し、JS/TS smoke と sample parity(case18) を通過（`check_py2js/ts` は共通 east3-contract blocker を分離記録）。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S3-01] Go emitter に ref-container 材料化（slice copy + map copy IIFE）を導入し、`test_py2go_smoke`/`check_py2go_transpile` は通過（sample/18 parity(go) は既存 compile blocker を S4-02 に分離）。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S4-01] Swift emitter に `ref_vars` 追跡 + container 材料化（`Array(__pytra_as_list(...))` / `Dictionary(uniqueKeysWithValues: __pytra_as_dict(...).map { ... })`）を導入し、`test_py2swift_smoke`/`check_py2swift_transpile` を通過（sample parity は toolchain_missing skip）。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S5-01] Ruby emitter に `ref_vars` + `decl_type` 材料化（`__pytra_as_list/__pytra_as_dict` + `.dup`）と `dict.get -> fetch` lower を導入し、`test_py2rb_smoke` は通過（sample/18 parity は既存 run_failed を S4-02 blocker へ分離）。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01-S6-01] Lua emitter に関数スコープ `ref_vars/type_map` と shallow-copy 材料化（list/dict）を追加し、追加回帰 + `check_py2lua_transpile` + sample/18 parity(lua) を通過（`test_py2lua_smoke` 全体の既存期待差分は S4-02 へ分離）。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S4-02] 横断確認で `go` parity compile error（TokenLike field）、`ruby` parity run_failed（tokenize）、`swift` toolchain_missing skip、`cs/rb/js/ts` transpile 既知失敗を blocker として分離記録。
- 進捗メモ: [ID: P3-MULTILANG-CONTAINER-REF-01-S5-01] `how-to-use` と backend spec（GSK/Ruby/Lua）に `container_ref_boundary` / `typed_non_escape_value_path` / rollback 手順（Any注釈寄せ・明示コピー）を追記。

### P3: CodeEmitter から C# selfhost 起因修正を隔離

文脈: [docs/ja/plans/p3-codeemitter-cs-isolation.md](../plans/p3-codeemitter-cs-isolation.md)

1. [x] [ID: P3-CODEEMITTER-CS-ISOLATION-01] C# selfhost 起因の修正を `CodeEmitter` から隔離し、共通層の責務を backend 中立へ戻す。
2. [x] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-01] `v0.4.0` 以降の `CodeEmitter` 差分を棚卸しし、「共通必須 / C# 固有 / 判定保留」の3分類を作成する。
3. [x] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-02] 「共通必須」の判定基準（backend 中立性・他言語利用実績・fail-closed 必要性）を明文化する。
4. [x] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-01] 「C# 固有」変更を `CSharpEmitter` / C# runtime / selfhost 準備層へ移管する。
5. [x] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-02] `CodeEmitter` から C# 固有回避コードを除去し、共通実装へ戻す。
6. [x] [ID: P3-CODEEMITTER-CS-ISOLATION-01-S3-01] unit/selfhost 回帰を実施し、C# pass 維持と他 backend 非退行を確認する。
- 進捗メモ: [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-01] `v0.4.0` 以降の `CodeEmitter` 変更を commit 単位で棚卸しし、`共通必須 / C#固有 / 判定保留` の3分類を文脈ファイルへ記録。
- 進捗メモ: [ID: P3-CODEEMITTER-CS-ISOLATION-01-S1-02] 共通必須判定を `backend中立性 / 他言語利用実績 / fail-closed必要性` の3軸に固定し、移管判定ルールを明文化。
- 進捗メモ: [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-01] scope 名正規化（`_normalize_scope_names`）を `CodeEmitter` から `CSharpEmitter` へ移管し、共通層 API を `set[str]` 前提へ戻した。`test_code_emitter`/`test_py2cs_smoke` 通過、`check_py2cs_transpile` fail 2件は既知継続。
- 進捗メモ: [ID: P3-CODEEMITTER-CS-ISOLATION-01-S2-02] `is_declared` の逆順走査を C# 回避 `while` から `range(...,-1,-1)` に戻し、`_const_int_literal` の返り型注釈を `int|None` へ復帰。`test_code_emitter`/`test_py2cs_smoke` 通過、`check_py2cs_transpile` fail 2件は既知継続。
- 進捗メモ: [ID: P3-CODEEMITTER-CS-ISOLATION-01-S3-01] `check_multilang_selfhost_stage1 --strict-stage1` / `check_multilang_selfhost_multistage` を含む回帰を再実施し、C# 行を stage1/native・multistage(stage1/2/3) すべて `pass` へ回復。`test_code_emitter`/`test_py2cs_smoke` も通過。

### P4: 全言語 selfhost 完全化（低低優先）

文脈: [docs/ja/plans/p4-multilang-selfhost-full-rollout.md](../plans/p4-multilang-selfhost-full-rollout.md)

1. [ ] [ID: P4-MULTILANG-SH-01] `cpp/rs/cs/js/ts/go/java/swift/kotlin` の selfhost を段階的に成立させ、全言語の multistage 監視を通過可能にする。
2. [ ] [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost の stage2 依存 transpile 失敗を解消し、multistage を通す。
3. [ ] [ID: P4-MULTILANG-SH-01-S3-01] TypeScript の preview-only 状態を解消し、selfhost 実行可能な生成モードへ移行する。
4. [ ] [ID: P4-MULTILANG-SH-01-S3-02] Go/Java/Swift/Kotlin の native backend 化タスクと接続し、selfhost 実行チェーンを有効化する。
5. [ ] [ID: P4-MULTILANG-SH-01-S4-01] 全言語 multistage 回帰を CI 導線へ統合し、失敗カテゴリの再発を常時検知できるようにする。
6. [ ] [ID: P4-MULTILANG-SH-01-S4-02] 完了判定テンプレート（各言語の stage 通過条件と除外条件）を文書化し、運用ルールを固定する。
- 完了済み子タスク（`S1-01` 〜 `S2-02-S3`）および過去進捗メモは `docs/ja/todo/archive/20260301.md` へ移管済み。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] JS emitter の selfhost parser 制約違反（`Any` 受け `node.get()/node.items()`）と関数内 `FunctionDef` 未対応を解消し、先頭失敗を `stage1_dependency_transpile_fail` から `self_retranspile_fail (ERR_MODULE_NOT_FOUND: ./pytra/std.js)` まで前進。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost 準備に shim 生成・import 正規化・export 注入・構文置換を追加し、`ERR_MODULE_NOT_FOUND` を解消。先頭失敗は `SyntaxError: Unexpected token ':'`（`raw[qpos:]` 由来）へ遷移。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost 向けに slice/集合判定の source 側縮退、ESM shim 化、import 正規化再設計、`argparse`/`Path` 互換 shim、`.py -> EAST3(JSON)` 入力経路、`JsEmitter` profile loader の selfhost 互換化を段階適用。先頭失敗は `ReferenceError/SyntaxError` 群を解消して `TypeError: CodeEmitter._dict_copy_str_object is not a function` へ遷移。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] `CodeEmitter.load_type_map` と `js_emitter` 初期化の dict access を object-safe 化し、selfhost rewrite に `set/list/dict` polyfill と `CodeEmitter` static alias 補完を追加。先頭失敗は `dict is not defined` を解消して `TypeError: module.get is not a function` へ前進。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] selfhost rewrite を `.get -> __pytra_dict_get` 化し、`Path` shim に `parent/name/stem` property 互換と `mkdir(parents/exist_ok)` 既定冪等化を追加。`js` は `stage1 pass / stage2 pass` に到達し、先頭失敗は `stage3 sample output missing` へ遷移。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] `CodeEmitter/JsEmitter` の object-safe 変換（`startswith/strip/find` 依存除去、`next_tmp` f-string 修正、ASCII helperの `ord/chr` 依存撤去）と selfhost rewrite の String polyfill（`strip/lstrip/rstrip/startswith/endswith/find/lower/upper/map`）を追加。`js` は `stage1/native pass`・`multistage stage2 pass` を維持し、先頭失敗は `stage3 sample_transpile_fail (SyntaxError: Invalid or unexpected token)` へ前進。
- 進捗メモ: [ID: P4-MULTILANG-SH-01-S2-03] `emit` のインデント生成（文字列乗算）を loop 化し、`quote_string_literal` の `quote` 非文字列防御、`_emit_function` の `in_class` 判定を `None` 依存から空文字判定へ変更。`js` は `stage1/native pass`・`multistage stage2 pass` を維持し、先頭失敗は `stage3 sample_transpile_fail (SyntaxError: Unexpected token '{')` に更新（`py2js_stage2.js` の未解決 placeholder/関数ヘッダ崩れが残件）。
