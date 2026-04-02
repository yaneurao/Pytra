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

### P0-OPAQUE-STORAGE-HINT: @extern class に class_storage_hint:"opaque" と meta.opaque_v1 を付与する

compile/resolve が `@extern class`（メソッドシグネチャのみ、フィールドなし）を検出したとき、`class_storage_hint: "opaque"` と `meta.opaque_v1` を付与する。現状は `"value"` になっており `meta.opaque_v1` も付かない。emitter は `class_storage_hint` を見て rc の要否を判断する（`"opaque"` → 生ポインタ、rc なし）。

spec: [docs/ja/spec/spec-opaque-type.md](../spec/spec-opaque-type.md)
fixture: `test/fixture/source/py/oop/extern_opaque_basic.py`

1. [ ] [ID: P0-OPAQUE-HINT-S1] compile/resolve で `@extern class`（body が全て `FunctionDef` + `...`）を検出し `class_storage_hint: "opaque"` を設定する
2. [ ] [ID: P0-OPAQUE-HINT-S2] `ClassDef.meta.opaque_v1` を付与する（`schema_version: 1`）
3. [ ] [ID: P0-OPAQUE-HINT-S3] `extern_opaque_basic` fixture の EAST3 golden で `class_storage_hint: "opaque"` と `meta.opaque_v1` が付いていることを確認する
4. [ ] [ID: P0-OPAQUE-HINT-S4] フィールドを持つ `@extern class` は `"opaque"` にならないことを確認する（`"ref"` のまま）

### P0-ITER-OPS-REMOVAL: iter_ops.py を削除し typed lowering に完全移行する

`src/pytra/built_in/iter_ops.py` は `object` ベースの `py_reversed_object` / `py_enumerate_object` を定義しているが、EAST3 の typed lowering が整備された現在は不要。この object ベースのヘルパーが残っていることで、C++ の object 退化削除（P0-CPP-VARIANT Phase 4）がブロックされている。

手順:
1. compile/lower で `reversed(list[T])` / `enumerate(str)` の typed lowering を実装し、`py_reversed_object` / `py_enumerate_object` への fallback を止める
2. EAST3 golden を再生成して `py_reversed_object` / `py_enumerate_object` が消えたことを確認
3. `src/pytra/built_in/iter_ops.py` を削除
4. 全言語の mapping.json から `py_reversed_object` / `py_enumerate_object` を削除
5. `src/runtime/east/built_in/iter_ops.east` を削除

1. [ ] [ID: P0-ITER-OPS-S1] compile/lower で `reversed(list[T])` の typed lowering を実装する（object fallback を止める）
2. [ ] [ID: P0-ITER-OPS-S2] `enumerate(str)` が typed path に乗らないケースを修正する（`enumerate_basic` fixture）
3. [ ] [ID: P0-ITER-OPS-S3] EAST3 golden を再生成し、`py_reversed_object` / `py_enumerate_object` が EAST3 に出現しないことを確認する
4. [ ] [ID: P0-ITER-OPS-S4] `src/pytra/built_in/iter_ops.py` と `src/runtime/east/built_in/iter_ops.east` を削除する
5. [ ] [ID: P0-ITER-OPS-S5] 全言語の mapping.json から `py_reversed_object` / `py_enumerate_object` エントリを削除する
6. [ ] [ID: P0-ITER-OPS-S6] fixture + sample + stdlib parity に全言語で回帰がないことを確認する

### P0-RUNTIME-CALL-COVERAGE: EAST runtime_call と mapping.json の双方向カバレッジ lint

EAST3 が生成する `runtime_call` と mapping.json の `calls` テーブルの整合を自動検証する。

検証方向:
1. **EAST → mapping.json**: fixture/sample/stdlib の EAST3 golden に出現する全 `runtime_call` が、各言語の mapping.json `calls` に登録されているか。未登録なら emitter が黙って壊れる。
2. **mapping.json → fixture**: mapping.json `calls` に登録されている runtime_call が、いずれかの fixture/sample/stdlib EAST3 golden に出現しているか。未カバーなら死んだエントリか、テスト不足。

1. [x] [ID: P0-RTCALL-COV-S1] `tools/check/check_runtime_call_coverage.py` を作成する — EAST3 golden を走査して runtime_call を収集し、全言語の mapping.json `calls` と双方向で突き合わせる（2026-04-01）
2. [x] [ID: P0-RTCALL-COV-S2] 未カバーの runtime_call に対して fixture を追加する（`list.clear`, `list.reverse`, `list.sort`, `set.clear`, `dict.pop`, `dict.setdefault` 等）— `list_mutation_methods.py`, `dict_mutation_methods.py`, `set_mutation_methods.py`, `str_methods_extended.py` を追加（2026-04-01）
3. [x] [ID: P0-RTCALL-COV-S3] `run_local_ci.py` に組み込む（2026-04-01）
4. [x] [ID: P0-RTCALL-COV-S4] `check_emitter_hardcode_lint.py` に `rt: call_coverage` カテゴリを追加し、各言語の mapping.json runtime_call カバレッジを `emitter-hardcode-lint.md` のマトリクスに統合する（`rt: type_id` と同じ仕組み）（2026-04-02）

### P0-BUILTIN-NAME-REMOVAL: EAST3 の builtin_name を廃止し mapping.json キーを runtime_call に統一する

EAST3 ノードの `builtin_name` は旧 toolchain の残骸。`runtime_call` と別名で 44 個存在し、mapping.json のキーが `runtime_call` と一致しない原因になっている。`resolve_runtime_call` の `builtin_name` フォールバックを削除し、mapping.json キーを `runtime_call` 値に統一する。

影響範囲: EAST compile/resolve、全言語の mapping.json、`resolve_runtime_call`、各 emitter

1. [ ] [ID: P0-BN-REMOVE-S1] EAST3 の `builtin_name` フィールドを一覧化し、対応する `runtime_call` 値との対応表を作成する
2. [ ] [ID: P0-BN-REMOVE-S2] 全言語の mapping.json `calls` キーを `runtime_call` 値に統一する
3. [ ] [ID: P0-BN-REMOVE-S3] `resolve_runtime_call` から `builtin_name` フォールバックを削除する
4. [ ] [ID: P0-BN-REMOVE-S4] EAST compile/resolve から `builtin_name` フィールド生成を削除する
5. [ ] [ID: P0-BN-REMOVE-S5] `check_runtime_call_coverage.py` の `rt: call_cov` が全言語で正しく突き合わせできることを確認する
6. [ ] [ID: P0-BN-REMOVE-S6] fixture + sample + stdlib parity に全言語で回帰がないことを確認する

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
