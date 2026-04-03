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

### P0-ISINSTANCE-DETID: EAST3 の IsInstance ノードから PYTRA_TID_* を廃止し型名を直接持たせる

EAST3 の `IsInstance` ノードが `expected_type_id: {"id": "PYTRA_TID_DICT"}` のように廃止予定の type_id 定数を参照している。emitter は型名（`dict`, `str`, `list` 等）を知りたいだけなのに、`PYTRA_TID_DICT` → `dict` の逆引きを強いられている。C++ emitter はこの逆引きを内部で持っているが、新規 backend（Kotlin, Scala 等）がこの旧方式を実装しようとする原因になっている。

spec-adt.md §6 で `PYTRA_TID_*` / `type_id_table` は廃止予定と明記済み。EAST3 の `IsInstance` ノードを型名ベースに移行する。

1. [ ] [ID: P0-ISINS-DETID-S1] `IsInstance` ノードの `expected_type_id` を `expected_type_name: str`（`"dict"`, `"str"`, `"list"` 等）に変更する spec を定義する
2. [ ] [ID: P0-ISINS-DETID-S2] compile/resolve で `IsInstance` の `expected_type_id` 生成を型名ベースに変更する
3. [ ] [ID: P0-ISINS-DETID-S3] EAST3 golden を再生成し、`PYTRA_TID_*` が `IsInstance` ノードに出現しないことを確認する
4. [ ] [ID: P0-ISINS-DETID-S4] C++ emitter の `PYTRA_TID_*` 逆引きを削除し、型名を直接参照するように更新する。C++ parity に回帰がないことを確認する（**C++ 担当へ委譲**）

注: 各言語の emitter 修正（Kotlin: `x is Type`、Java: `x instanceof Type` 等）と parity 確認は各言語の担当が行う。インフラ担当の責務は S1〜S3 の EAST3 変更と C++ への委譲まで。

### P0-OPAQUE-STORAGE-HINT: @extern class に class_storage_hint:"opaque" と meta.opaque_v1 を付与する

compile/resolve が `@extern class`（メソッドシグネチャのみ、フィールドなし）を検出したとき、`class_storage_hint: "opaque"` と `meta.opaque_v1` を付与する。現状は `"value"` になっており `meta.opaque_v1` も付かない。emitter は `class_storage_hint` を見て rc の要否を判断する（`"opaque"` → 生ポインタ、rc なし）。

spec: [docs/ja/spec/spec-opaque-type.md](../spec/spec-opaque-type.md)
fixture: `test/fixture/source/py/oop/extern_opaque_basic.py`

1. [ ] [ID: P0-OPAQUE-HINT-S1] compile/resolve で `@extern class`（body が全て `FunctionDef` + `...`）を検出し `class_storage_hint: "opaque"` を設定する
2. [ ] [ID: P0-OPAQUE-HINT-S2] `ClassDef.meta.opaque_v1` を付与する（`schema_version: 1`）
3. [ ] [ID: P0-OPAQUE-HINT-S3] `extern_opaque_basic` fixture の EAST3 golden で `class_storage_hint: "opaque"` と `meta.opaque_v1` が付いていることを確認する
4. [ ] [ID: P0-OPAQUE-HINT-S4] フィールドを持つ `@extern class` は `"opaque"` にならないことを確認する（`"ref"` のまま）

### P0-BUILTIN-NAME-REMOVAL: EAST3 の builtin_name を廃止し mapping.json キーを runtime_call に統一する

S1-S3 完了済み（[archive/20260403.md](archive/20260403.md) 参照）。

4. [ ] [ID: P0-BN-REMOVE-S4] EAST compile/resolve から `builtin_name` フィールド生成を削除する
5. [ ] [ID: P0-BN-REMOVE-S5] `check_runtime_call_coverage.py` の `rt: call_cov` が正しく突き合わせできることを確認する（C++ で代表確認。各言語の parity は各担当に委譲）

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
