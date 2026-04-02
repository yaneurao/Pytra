<a href="../../en/todo/infra.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — インフラ・ツール・仕様

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-02

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。

完了済みタスクは [アーカイブ](archive/20260331.md) を参照。

## 未完了タスク

### P0-RUNTIME-CALL-COVERAGE: EAST runtime_call と mapping.json の双方向カバレッジ lint

EAST3 が生成する `runtime_call` と mapping.json の `calls` テーブルの整合を自動検証する。

検証方向:
1. **EAST → mapping.json**: fixture/sample/stdlib の EAST3 golden に出現する全 `runtime_call` が、各言語の mapping.json `calls` に登録されているか。未登録なら emitter が黙って壊れる。
2. **mapping.json → fixture**: mapping.json `calls` に登録されている runtime_call が、いずれかの fixture/sample/stdlib EAST3 golden に出現しているか。未カバーなら死んだエントリか、テスト不足。

1. [x] [ID: P0-RTCALL-COV-S1] `tools/check/check_runtime_call_coverage.py` を作成する — EAST3 golden を走査して runtime_call を収集し、全言語の mapping.json `calls` と双方向で突き合わせる（2026-04-01）
2. [x] [ID: P0-RTCALL-COV-S2] 未カバーの runtime_call に対して fixture を追加する（`list.clear`, `list.reverse`, `list.sort`, `set.clear`, `dict.pop`, `dict.setdefault` 等）— `list_mutation_methods.py`, `dict_mutation_methods.py`, `set_mutation_methods.py`, `str_methods_extended.py` を追加（2026-04-01）
3. [x] [ID: P0-RTCALL-COV-S3] `run_local_ci.py` に組み込む（2026-04-01）
4. [x] [ID: P0-RTCALL-COV-S4] `check_emitter_hardcode_lint.py` に `rt: call_coverage` カテゴリを追加し、各言語の mapping.json runtime_call カバレッジを `emitter-hardcode-lint.md` のマトリクスに統合する（`rt: type_id` と同じ仕組み）（2026-04-02）

### P5-PARITY-STREAMING: runtime_parity_check_fast.py のストリーミング出力

C++ fixture parity（137件、20分超）で完了まで stdout が返らず、進捗が見えない問題。

1. [x] [ID: P5-PARITY-STREAM-S1] `tools/check/runtime_parity_check_fast.py` の各ケース完了時に即座に stdout へ結果行を flush する（バッファリングをやめる）— `[PASS]`/`[FAIL]` print に `flush=True` を追加し、メインループで `sys.stdout.flush()` を呼ぶ（2026-04-02）
2. [x] [ID: P5-PARITY-STREAM-S2] 既存の summary 出力フォーマットとの互換を維持する — SUMMARY行/SUMMARY_CATEGORIES行は変更なし（2026-04-02）

### P20-DATA-DRIVEN-TESTS: パイプライン系テストのデータ駆動化

文脈: [docs/ja/plans/plan-emit-expect-data-driven-tests.md](../plans/plan-emit-expect-data-driven-tests.md)

ステータス: **保留中** — 既存テストが他 agent により変更中のため、安定してから Phase 1 に着手する。

`tools/unittest/` の 267 スクリプトのうち ~80件はパイプライン系（入力→parse/resolve/lower/emit→期待出力）で、JSON データで定義できる。残り ~190件（tooling/selfhost/link 等）は Python テストとして残す。

**Phase 1: emit 層で方式を確立**

1. [ ] [ID: P20-DDT-S1] `test/cases/emit/cpp/` に JSON テストケース 5〜10 件を作成する
2. [ ] [ID: P20-DDT-S2] `tools/unittest/test_emit_cases.py` を実装する（pytest parametrize で JSON 走査）
3. [ ] [ID: P20-DDT-S3] `test_common_renderer.py` の対応テストを JSON に移行し、元メソッドを削除する

**Phase 2: パイプライン層に横展開**

4. [ ] [ID: P20-DDT-S4] `test/cases/{east1,east2,east3}/` に JSON テストケースを作成する
5. [ ] [ID: P20-DDT-S5] `tools/unittest/test_pipeline_cases.py` を実装する
6. [ ] [ID: P20-DDT-S6] `tools/unittest/ir/` と `tools/unittest/toolchain2/` の対応テストを段階的に JSON に移行する

**Phase 3: smoke テストの統合**

7. [ ] [ID: P20-DDT-S7] `tools/unittest/emit/<lang>/test_py2*_smoke.py` (~20件) を JSON に移行する
8. [ ] [ID: P20-DDT-S8] `tools/unittest/common/test_pylib_*.py` (~10件) を JSON に移行する
9. [ ] [ID: P20-DDT-S9] 空になったスクリプトを削除する

### 保留中タスク

- P20-INT32 は [plans/p4-int32-default.md](../plans/p4-int32-default.md) に保留中。再開時にここへ戻す。
