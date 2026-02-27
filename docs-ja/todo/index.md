# TODO（未完了）

> `docs-ja/` が正（source of truth）です。`docs/` はその翻訳です。

<a href="../../docs/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-27

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs-ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs-ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs-ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs-ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs-ja/todo/index.md` / `docs-ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。

## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs-ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs-ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。


## 未完了タスク

### P0: Go/Java/Swift/Kotlin sidecar 完全撤去（最優先）

文脈: [docs-ja/plans/p0-sidecar-full-removal.md](../plans/p0-sidecar-full-removal.md)

1. [ ] [ID: P0-SIDECAR-REMOVE-01] Go/Java/Swift/Kotlin backend の sidecar 互換経路を完全撤去し、native 単一路線へ統一する。
2. [x] [ID: P0-SIDECAR-REMOVE-01-S1-01] `py2go.py` / `py2java.py` / `py2swift.py` / `py2kotlin.py` から `--*-backend sidecar` と sidecar 分岐を削除する。
3. [x] [ID: P0-SIDECAR-REMOVE-01-S1-02] sidecar 専用 emitter import / `transpile_to_js` / `write_js_runtime_shims` 依存を撤去し、未使用コードを整理する。
4. [x] [ID: P0-SIDECAR-REMOVE-01-S2-01] transpile/smoke/check 導線（`test_py2*` / `check_py2*_transpile.py` / `runtime_parity_check.py`）から sidecar 指定経路を除去する。
5. [x] [ID: P0-SIDECAR-REMOVE-01-S2-02] `sample/go` / `sample/java` / `sample/swift` / `sample/kotlin` を再生成し、`.js` sidecar 非生成を回帰条件として固定する。
6. [x] [ID: P0-SIDECAR-REMOVE-01-S3-01] `docs-ja/how-to-use.md` / `docs-ja/spec/spec-import.md` / 関連 spec から sidecar 記述を撤去し、native 単一路線へ更新する。
7. [x] [ID: P0-SIDECAR-REMOVE-01-S3-02] `docs/` 翻訳同期を反映し、日英で sidecar 記述の不整合を解消する。
8. [x] [ID: P0-SIDECAR-REMOVE-01-S4-01] 最終回帰（4言語 transpile + parity + sample 検証）を完了し、完了条件を文脈へ記録する。
9. [ ] [ID: P0-SIDECAR-REMOVE-01-S5-01] Go native parity 失敗 6 ケース（`10/13/14/15/16/18`）を順に修正し、`run_failed` を解消する。
10. [ ] [ID: P0-SIDECAR-REMOVE-01-S5-02] Kotlin native parity 失敗 7 ケース（`10/12/13/14/15/16/18`）を順に修正し、`run_failed` を解消する。
11. [ ] [ID: P0-SIDECAR-REMOVE-01-S5-03] `runtime_parity_check.py --targets go,java,swift,kotlin --all-samples` を再実行し、`case_fail=0` で親 `P0-SIDECAR-REMOVE-01` を完了化する。
- `P0-SIDECAR-REMOVE-01-S1-01` `py2{go,java,swift,kotlin}.py` から `--*-backend` CLI と sidecar 分岐（`.js` 生成・runtime shim 出力）を削除し、native 直生成へ統一した。
- `P0-SIDECAR-REMOVE-01-S1-02` sidecar emitter 4ファイル（`go/java/swift/kotlin *_emitter.py`）を削除し、`hooks/*/emitter/__init__.py` は native 実装へ委譲する互換 API のみに整理した。
- `P0-SIDECAR-REMOVE-01-S2-01` `test_py2{go,java,swift,kotlin}_smoke.py` と `runtime_parity_check.py` / `check_gsk_native_regression.py` から sidecar 引数・前提を除去し、native-only 回帰を unit test（`51/51`）で確認した。
- `P0-SIDECAR-REMOVE-01-S2-02` `tools/regenerate_samples.py --langs go,java,swift,kotlin --force`（`regen=72 fail=0`）を実行し、`sample/{go,java,swift,kotlin}` の `.js` sidecar が `0` 件であることを確認した。
- `P0-SIDECAR-REMOVE-01-S3-01` `docs-ja/how-to-use.md` / `docs-ja/spec/spec-import.md` / `docs-ja/spec/spec-gsk-native-backend.md` / `docs-ja/spec/spec-java-native-backend.md` の sidecar 互換前提記述を「撤去済み・native-only」へ更新した。
- `P0-SIDECAR-REMOVE-01-S3-02` 英語版 `docs/how-to-use.md` / `docs/spec/spec-import.md` / `docs/spec/spec-gsk-native-backend.md` / `docs/spec/spec-java-native-backend.md` を同期し、日英で sidecar 記述の整合性を確保した。
- `P0-SIDECAR-REMOVE-01-S4-01` 最終回帰を実行し、`check_py2{go,java,swift,kotlin}_transpile.py` は `ok=132 fail=0 skipped=6` で通過、`find sample/{go,java,swift,kotlin} -name '*.js' | wc -l` は `0` を確認した。`runtime_parity_check.py --targets go,java,swift,kotlin --all-samples` は `case_pass=11 case_fail=7 (run_failed=13, toolchain_missing=18)` で失敗し、失敗は Go/Kotlin native 既存課題（型/宣言衝突）に起因することを記録した。
- `P0-SIDECAR-REMOVE-01-S5-*` ユーザー指示により、Go/Kotlin parity 失敗 7 ケース（Go 6 + Kotlin 7、重複あり）を順に潰すタスクを最優先として追加した。

### P2: Ruby backend 追加（中優先）

文脈: [docs-ja/plans/p2-ruby-backend-rollout.md](../plans/p2-ruby-backend-rollout.md)
- 言語展開順方針: `Ruby -> Lua -> PHP`（Lua/PHP は Ruby 完了後に `P2` タスクとして起票）

1. [ ] [ID: P2-RUBY-BACKEND-01] Ruby backend（`py2rb.py` + Ruby emitter/runtime）を追加し、`sample/py` 主要ケースで parity を確認できる状態まで引き上げる。
2. [ ] [ID: P2-RUBY-BACKEND-01-S1-01] Ruby backend の契約（入力 EAST3、fail-closed、runtime 境界、非対象）を文書化する。
3. [ ] [ID: P2-RUBY-BACKEND-01-S1-02] `src/py2rb.py` と `src/hooks/ruby/emitter/` の骨格を追加し、最小 fixture（`add` / `if_else` / `for_range`）が変換・実行できる状態を作る。
4. [ ] [ID: P2-RUBY-BACKEND-01-S2-01] 式/文の基本 lower（代入、分岐、ループ、関数呼び出し、組み込み最小セット）を実装し、`sample/py` 前半ケースを通す。
5. [ ] [ID: P2-RUBY-BACKEND-01-S2-02] class/instance/isinstance/import（`math`・画像runtime含む）対応を段階実装し、残ケースの parity 失敗を縮退する。
6. [ ] [ID: P2-RUBY-BACKEND-01-S3-01] `tools/check_py2rb_transpile.py` と smoke/parity 導線を追加し、回帰監視を固定する。
7. [ ] [ID: P2-RUBY-BACKEND-01-S3-02] `sample/ruby` 再生成、README バッジ/対応表、`docs-ja/how-to-use.md` と `docs/how-to-use.md` の手順を同期する。

### P2: ForCore tuple unpack 型伝播改善（中優先）

文脈: [docs-ja/plans/p2-forcore-tuple-type-propagation.md](../plans/p2-forcore-tuple-type-propagation.md)

1. [ ] [ID: P2-FORCORE-TYPE-01] `for a, b in ...` の tuple target で要素型が `unknown/object` へ落ちる経路を縮退し、EAST3 lowering から C++ emitter まで型情報を維持する。
2. [ ] [ID: P2-FORCORE-TYPE-01-S1-01] `east2_to_east3_lowering._build_target_plan` で `target_type=tuple[...]` の要素型を `TupleTarget.elements[].target_type` へ伝播する。
3. [ ] [ID: P2-FORCORE-TYPE-01-S1-02] C++ `ForCore` tuple unpack の emit で `int64/str/...` を直接束縛し、未確定要素のみ fail-closed で `object` フォールバックする。
4. [ ] [ID: P2-FORCORE-TYPE-01-S2-01] `enumerate(list[str])` を含む fixture/sample を回帰に追加し、`py_at(...)` 由来の `object` 束縛が不要な箇所で発生しないことを固定する。
5. [ ] [ID: P2-FORCORE-TYPE-01-S2-02] `check_py2cpp_transpile.py` と `sample/18` コンパイル検証を実行し、型伝播導入後の回帰結果を文脈ファイルへ記録する。

### P3: microgpt 原本保全タスク再開（低優先）

文脈: [docs-ja/plans/p3-microgpt-revival.md](../plans/p3-microgpt-revival.md)

1. [ ] [ID: P3-MSP-REVIVE-01] archive 移管済みの `microgpt` 保全タスクを新規 ID で再開し、回帰監視を TODO 運用へ復帰する。
2. [ ] [ID: P3-MSP-REVIVE-01-S1-01] archive 側の `P3-MSP-*` 履歴と再開スコープの対応表を作成し、再開対象を明確化する。
3. [ ] [ID: P3-MSP-REVIVE-01-S1-02] 原本 `microgpt` 入力の transpile / syntax-check / 実行確認の現行手順を再確認し、期待値を固定する。
4. [ ] [ID: P3-MSP-REVIVE-01-S2-01] `check_microgpt_original_py2cpp_regression.py` を運用基準へ合わせて見直し、再発検知条件を更新する。
5. [ ] [ID: P3-MSP-REVIVE-01-S2-02] 失敗時に parser / lower / runtime の責務へ再分類できるログ運用テンプレートを整備する。
6. [ ] [ID: P3-MSP-REVIVE-01-S3-01] 必要に応じて `microgpt` 用の追加 fixture / smoke を補強し、CI での監視を安定化する。
7. [ ] [ID: P3-MSP-REVIVE-01-S3-02] 再開タスク完了時に archive へ戻すための移管条件（完了定義）を文書化する。

### P4: 全言語 selfhost 完全化（低低優先）

文脈: [docs-ja/plans/p4-multilang-selfhost-full-rollout.md](../plans/p4-multilang-selfhost-full-rollout.md)

1. [ ] [ID: P4-MULTILANG-SH-01] `cpp/rs/cs/js/ts/go/java/swift/kotlin` の selfhost を段階的に成立させ、全言語の multistage 監視を通過可能にする。
2. [ ] [ID: P4-MULTILANG-SH-01-S1-01] 現状の stage1/stage2/stage3 未達要因を言語別に固定化し、優先順（blocking chain）を明文化する。
3. [ ] [ID: P4-MULTILANG-SH-01-S1-02] multistage runner 未定義言語（go/java/swift/kotlin）の runner 契約を定義し、`runner_not_defined` を解消する実装方針を確定する。
4. [ ] [ID: P4-MULTILANG-SH-01-S2-01] Rust selfhost の stage1 失敗（from-import 受理）を解消し、stage2 へ進める。
5. [ ] [ID: P4-MULTILANG-SH-01-S2-02] C# selfhost の stage2 compile 失敗を解消し、stage3 変換を通す。
6. [ ] [ID: P4-MULTILANG-SH-01-S2-03] JS selfhost の stage2 依存 transpile 失敗を解消し、multistage を通す。
7. [ ] [ID: P4-MULTILANG-SH-01-S3-01] TypeScript の preview-only 状態を解消し、selfhost 実行可能な生成モードへ移行する。
8. [ ] [ID: P4-MULTILANG-SH-01-S3-02] Go/Java/Swift/Kotlin の native backend 化タスクと接続し、selfhost 実行チェーンを有効化する。
9. [ ] [ID: P4-MULTILANG-SH-01-S4-01] 全言語 multistage 回帰を CI 導線へ統合し、失敗カテゴリの再発を常時検知できるようにする。
10. [ ] [ID: P4-MULTILANG-SH-01-S4-02] 完了判定テンプレート（各言語の stage 通過条件と除外条件）を文書化し、運用ルールを固定する。
