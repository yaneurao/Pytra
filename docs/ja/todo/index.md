# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-01

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


### P0: Scala3 parity 全通過化（sample + fixture）

文脈: [docs/ja/plans/p0-scala3-full-parity-rollout.md](../plans/p0-scala3-full-parity-rollout.md)

1. [ ] [ID: P0-SCALA3-PARITY-ALL-01] Scala3 backend で parity（stdout + artifact）を sample/fixture ともに全通過させる。
2. [x] [ID: P0-SCALA3-PARITY-ALL-01-S1-01] sample 全件 + fixture 正例群の baseline を取得し、失敗カテゴリを固定する。
3. [x] [ID: P0-SCALA3-PARITY-ALL-01-S1-02] Scala fixture parity の対象マニフェストを定義し、負例（P2）との境界を固定する。
4. [ ] [ID: P0-SCALA3-PARITY-ALL-01-S2-01] `save_gif` / `write_rgb_png` の `__pytra_noop` 経路を撤去して runtime 実装へ接続する。
5. [ ] [ID: P0-SCALA3-PARITY-ALL-01-S2-02] `// TODO: unsupported ...` 出力経路を縮小し、必要ノードの lowering を実装する（未対応は fail-closed）。
6. [ ] [ID: P0-SCALA3-PARITY-ALL-01-S2-03] sample/18 を含む高難度ケースの builtin/container 不足を補完し、`run_failed` を解消する。
7. [ ] [ID: P0-SCALA3-PARITY-ALL-01-S2-04] 継承先で上書きされるメソッドに `override def` を出力し、Scala3 の継承契約へ一致させる。
8. [ ] [ID: P0-SCALA3-PARITY-ALL-01-S3-01] `runtime_parity_check` の Scala artifact optional を撤去し、関連 unit テストを更新する。
9. [ ] [ID: P0-SCALA3-PARITY-ALL-01-S3-02] Scala parity の再実行導線（専用チェック）を追加し、CI/ローカル手順を固定する。
10. [ ] [ID: P0-SCALA3-PARITY-ALL-01-S3-03] parity 実行結果を確認し、`how-to-use` と `spec-tools` の Scala 手順を同期する。

### P1: sample/go/01 品質改善（C++品質との差分縮小）

文脈: [docs/ja/plans/p1-go-sample01-quality-uplift.md](../plans/p1-go-sample01-quality-uplift.md)

1. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01] Go backend の `sample/01` 出力品質を改善し、C++ 出力との差を縮小する。
2. [x] [ID: P1-GO-SAMPLE01-QUALITY-01-S1-01] `sample/go/01` の品質差分（冗長 cast / loop / no-op / any退化）を棚卸しし、改善優先順を固定する。
3. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-01] Go emitter の数値演算出力で同型変換連鎖を削減し、typed 経路を優先する。
4. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-02] `range(stop)` / `range(start, stop, 1)` 系を canonical `for` へ lower する fastpath を追加する。
5. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-03] `write_rgb_png` 経路を no-op から native runtime 呼び出しへ接続し、未解決時は fail-closed にする。
6. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S2-04] `sample/01` の `pixels` ホットパスで `[]any` 退化を抑制する typed container fastpath を追加する。
7. [ ] [ID: P1-GO-SAMPLE01-QUALITY-01-S3-01] 回帰テスト（コード断片 + parity）を追加し、`sample/go/01` 再生成差分を固定する。

### P1: sample/kotlin/01 品質改善（C++品質との差分縮小）

文脈: [docs/ja/plans/p1-kotlin-sample01-quality-uplift.md](../plans/p1-kotlin-sample01-quality-uplift.md)

1. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01] Kotlin backend の `sample/01` 出力品質を改善し、C++ 出力との差を縮小する。
2. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S1-01] `sample/kotlin/01` の品質差分（冗長 cast / loop / no-op / any退化）を棚卸しし、改善優先順を固定する。
3. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-01] Kotlin emitter の数値演算出力で同型変換連鎖を削減し、typed 経路を優先する。
4. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-02] 単純 `range` ループを canonical loop へ lower する fastpath を追加する。
5. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-03] `write_rgb_png` 経路を no-op から native runtime 呼び出しへ接続し、未解決時は fail-closed にする。
6. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S2-04] `sample/01` の `pixels` 経路で typed container fastpath を追加し、`MutableList<Any?>` 退化を抑制する。
7. [ ] [ID: P1-KOTLIN-SAMPLE01-QUALITY-01-S3-01] 回帰テスト（コード断片 + parity）を追加し、`sample/kotlin/01` 再生成差分を固定する。

### P1: sample/swift/01 品質改善（C++品質との差分縮小）

文脈: [docs/ja/plans/p1-swift-sample01-quality-uplift.md](../plans/p1-swift-sample01-quality-uplift.md)

1. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01] Swift backend の `sample/01` 出力品質を改善し、C++ 出力との差を縮小する。
2. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S1-01] `sample/swift/01` の品質差分（冗長 cast / loop / no-op / any退化）を棚卸しし、改善優先順を固定する。
3. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-01] Swift emitter の数値演算出力で同型変換連鎖を削減し、typed 経路を優先する。
4. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-02] 単純 `range` ループを canonical loop へ lower する fastpath を追加する。
5. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-03] `write_rgb_png` 経路を no-op から native runtime 呼び出しへ接続し、未解決時は fail-closed にする。
6. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S2-04] `sample/01` の `pixels` 経路で typed container fastpath を追加し、`[Any]` 退化を抑制する。
7. [ ] [ID: P1-SWIFT-SAMPLE01-QUALITY-01-S3-01] 回帰テスト（コード断片 + parity）を追加し、`sample/swift/01` 再生成差分を固定する。

### P1: sample/ruby/01 品質改善（C++品質との差分縮小）

文脈: [docs/ja/plans/p1-ruby-sample01-quality-uplift.md](../plans/p1-ruby-sample01-quality-uplift.md)

1. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01] Ruby backend の `sample/01` 出力品質を改善し、C++ 出力との差を縮小する。
2. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S1-01] `sample/ruby/01` の品質差分（冗長 cast / loop / truthy / 一時初期化）を棚卸しし、改善優先順を固定する。
3. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-01] Ruby emitter の数値演算出力で同型変換連鎖を削減し、typed 経路を優先する。
4. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-02] 単純 `range` ループを canonical loop へ lower する fastpath を追加する。
5. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-03] 比較式/論理式の `__pytra_truthy` 挿入条件を最適化し、Ruby ネイティブ条件式を優先する。
6. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S2-04] `sample/01` の `r/g/b` 等で不要な `nil` 初期化を削減する typed 代入 fastpath を追加する。
7. [ ] [ID: P1-RUBY-SAMPLE01-QUALITY-01-S3-01] 回帰テスト（コード断片 + parity）を追加し、`sample/ruby/01` 再生成差分を固定する。

### P1: sample/lua/01 品質改善（可読性・冗長性の縮小）

文脈: [docs/ja/plans/p1-lua-sample01-quality-uplift.md](../plans/p1-lua-sample01-quality-uplift.md)

1. [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01] `sample/lua/01` の可読性/冗長性を改善し、C++ 出力との差を縮小する。
2. [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S1-01] `sample/lua/01` の冗長箇所（暗黙runtime依存 / nil初期化 / ループ表現）をコード断片で固定する。
3. [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-01] `int/float/bytearray` など runtime 依存の出力を明示化し、自己完結性を改善する。
4. [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-02] typed 経路で `r/g/b` の不要な `nil` 初期化を削減する。
5. [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S2-03] 単純 `range` ループの step/括弧出力を簡素化する fastpath を追加する。
6. [ ] [ID: P1-LUA-SAMPLE01-QUALITY-01-S3-01] 回帰テストを追加し、`sample/lua/01` 再生成差分を固定する。

### P1: sample/rs/08 出力品質改善（可読性 + ホットパス縮退）

文脈: [docs/ja/plans/p1-rs-s08-quality-uplift.md](../plans/p1-rs-s08-quality-uplift.md)

1. [ ] [ID: P1-RS-S08-QUALITY-01] `sample/rs/08` の生成品質を改善し、可読性とホットパス効率を引き上げる。
2. [ ] [ID: P1-RS-S08-QUALITY-01-S1-01] `sample/rs/08` の冗長箇所（clone/添字正規化/loop/分岐/capture判定/capacity）をコード断片で固定する。
3. [ ] [ID: P1-RS-S08-QUALITY-01-S2-01] `capture` 返却の不要 `clone` を削減する出力規則を導入する。
4. [ ] [ID: P1-RS-S08-QUALITY-01-S2-02] 非負添字が保証される経路で index 正規化式を省略する fastpath を追加する。
5. [ ] [ID: P1-RS-S08-QUALITY-01-S2-03] 単純 `range` 由来ループを Rust `for` へ縮退する fastpath を追加する。
6. [ ] [ID: P1-RS-S08-QUALITY-01-S2-04] `if/elif` 連鎖を `else if` / `match` 相当へ簡素化する出力規則を追加する。
7. [ ] [ID: P1-RS-S08-QUALITY-01-S2-05] capture 判定 `%` を next-capture カウンタ方式へ置換する fastpath を追加する。
8. [ ] [ID: P1-RS-S08-QUALITY-01-S2-06] 推定可能な `frames` サイズに対する `reserve` 出力規則を追加する。
9. [ ] [ID: P1-RS-S08-QUALITY-01-S3-01] 回帰テストを追加し、`sample/rs/08` 再生成差分を固定する。
10. [ ] [ID: P1-RS-S08-QUALITY-01-S3-02] transpile/smoke/parity を実行し、非退行を確認する。

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
