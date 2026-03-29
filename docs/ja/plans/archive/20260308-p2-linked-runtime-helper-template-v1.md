<a href="../../../en/plans/archive/20260308-p2-linked-runtime-helper-template-v1.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: linked runtime helper 向け `@template` v1

最終更新: 2026-03-08

関連 TODO:
- 完了済み。履歴は `docs/ja/todo/archive/20260308.md` の `ID: P2-LINKED-RUNTIME-TEMPLATE-01` を参照。

関連:
- [p2-runtime-sot-linked-program-integration.md](../p2-runtime-sot-linked-program-integration.md)
- [p2-runtime-helper-generics-under-linked-program.md](../p2-runtime-helper-generics-under-linked-program.md)
- [../spec/spec-template.md](../../spec/spec-template.md)

背景:
- linked runtime helper generics の長期案は既にあるが、syntax 候補が `TypeVar` と `@template("T")` の両論で止まっている。
- 現時点の判断では、runtime helper 限定で implicit monomorphization を始めるなら、Python 本来の generic syntax を無理に流用するより `@template("T")` の方が意図が明確で、parser / validator / linked-program collector の設計も素直である。
- また、将来 explicit instantiation を入れる場合も `@instantiate(...)` を同じ decorator family に足せるため、surface 拡張の方向性が読みやすい。
- 一方で、user program 全般へ generic を開放するには blast radius が大きすぎるため、最初のスコープは runtime helper 限定に絞る必要がある。

目的:
- generic surface の v1 として `@template("T", ...)` を正式に採用する。
- ただし対象は linked-program に載る runtime helper の top-level function に限定する。
- explicit instantiation はまだ入れず、使用箇所からの specialization collector / monomorphization は後段で扱う。
- 先に syntax / metadata / validation / docs を固め、generic 実装本体の前提を固定する。

対象:
- `@template("T", ...)` surface syntax
- parser / EAST metadata / linked metadata 契約
- runtime helper 限定の validation ルール
- `spec-template.md` と generic/runtime helper plan の整合
- TODO / docs 上の導入順序

非対象:
- `@instantiate(...)` の導入
- user code 全般での template 利用
- generic class / method / nested generic
- monomorphization collector の本実装
- backend emit / specialization naming の実装

受け入れ基準:
- `@template("T")` を generic surface の v1 canonical syntax として docs に固定する。
- 適用対象は runtime helper の top-level function 限定と明記される。
- parser / metadata 契約が `template_v1` 相当の canonical 表現を持つ設計で固定される。
- `@instantiate` は後段拡張として明確に分離される。
- `TypeVar` は引き続き generic surface の v1 には使わない、と方針が明記される。
- TODO 上で、runtime SoT linked-program integration の後段 P2 として着手順が固定される。

基本方針:
1. syntax の決定だけを generic 実装本体と切り離して先に固定する。
2. v1 は `@template("T", ...)` のみを導入し、`@instantiate(...)` は future extension に回す。
3. 対象は runtime helper 限定にし、implicit monomorphization 前提の blast radius を制御する。
4. linked-program 統合後に specialization collector を実装する前提で、metadata 契約を先に作る。

確認コマンド（予定）:
- `python3 tools/check/check_todo_priority.py`
- `python3 -m py_compile src/toolchain/ir/core.py src/toolchain/frontends/runtime_abi.py`
- 実装着手後は `tools/unittest/ir` / `tools/unittest/link` / `tools/unittest/common` の generic 関連回帰を追加する

## 分解

- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S1-01] `TypeVar` 案と `@template` 案の比較を閉じ、`@template("T")` を v1 canonical syntax として決定する。
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S1-02] runtime helper 限定・top-level function 限定・explicit instantiation なし、という v1 スコープを spec/plan に固定する。
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S2-01] parser / EAST / linked metadata の canonical shape（例: `meta.template_v1`）を設計する。
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S2-02] validation ルール（適用位置、パラメータ名、重複、runtime helper 限定）を設計する。
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S3-01] future `@instantiate(...)` と両立する surface 拡張方針を記録する。
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S3-02] specialization collector / monomorphization の後続計画との接続点を整理する。
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S4-01] docs / TODO / 関連 plan を同期して、generic v1 の前提を固定する。
- [x] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S4-02] 完了時に archive へ移せる状態まで決定ログと受け入れ基準を整える。

## フェーズ詳細

### Phase 1: syntax 決定

やること:
- `@template("T")` を正式採用する。
- `TypeVar` を v1 generic surface には使わないと決める。
- explicit instantiation なしの v1 スコープを明示する。

成果物:
- syntax 決定
- scope 決定

### Phase 2: metadata / validation 設計

やること:
- parser / EAST / linked metadata の canonical shape を決める。
- `runtime helper only` をどこでどう検証するかを決める。
- invalid case の diagnostics を設計する。

成果物:
- metadata schema
- validation rules

### Phase 3: 後続実装との接続

やること:
- future `@instantiate(...)` の入り口を定義する。
- specialization collector / monomorphization と metadata をどうつなぐか決める。

成果物:
- 拡張方針
- collector 接続点

### Phase 4: 運用固定

やること:
- docs と TODO を同期する。
- 後続 P2 計画との順序関係を固定する。

成果物:
- docs
- TODO 順序

## 決定ログ

- 2026-03-08: ユーザーとの議論により、runtime helper limited generics の v1 syntax は `TypeVar` ではなく `@template("T")` が自然だと判断した。
- 2026-03-08: 理由は、関数単位の type parameter 宣言が明示的であり、Pytra 専用 surface として曖昧さが少なく、将来 `@instantiate(...)` を足す拡張とも整合しやすいためである。
- 2026-03-08: ただし v1 では explicit instantiation はまだ入れず、runtime helper 限定の implicit monomorphization 前提で設計する。
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S1-01]: `TypeVar` は Python 注釈としては自然だが、関数単位の type parameter 宣言を surface 上で明示できず、runtime helper v1 の専用 generic syntax としては曖昧さが残るため採用しない。`@template("T")` は function-scoped declaration が明示的で、parser / validator / linked metadata の設計も直線的である。
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S1-02]: v1 スコープは linked runtime helper の top-level function に限定する。class generic / method generic / user code 一般 / explicit instantiation は後段計画へ分離し、implicit monomorphization の blast radius を runtime helper 内へ閉じ込める。
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S2-01]: canonical metadata は `FunctionDef.meta.template_v1` とし、`schema_version=1`, `params`, `scope=\"runtime_helper\"`, `instantiation_mode=\"linked_implicit\"` を持つ shape で固定する。raw `decorators` は保存用であり、backend / linker の正本には使わない。
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S2-02]: validation は二段に分ける。parser/EAST build は decorator form・パラメータ名・重複・適用位置（top-level function only）を検証し、linked-program validator は runtime helper provenance を検証して `runtime helper only` を fail-closed で enforce する。
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S3-01]: future explicit instantiation は `@template` と同じ decorator family に `@instantiate("name", type_args...)` を足す方向で拡張する。v1 の canonical syntax family を途中で `TypeVar` や bracket syntax へ分岐させない。
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S3-02]: specialization collector / monomorphization は raw decorator ではなく `FunctionDef.meta.template_v1` を入口にする。`instantiation_mode="linked_implicit"` は linked-program collector が callsite から deterministic に concrete type tuple を収集する契約として扱う。
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S4-01]: `spec-template`、generic 関連 P2 メモ、runtime SoT linked-program 統合メモ、active TODO を同期し、linked runtime helper generics の v1 前提を `@template("T", ...)` / `template_v1` / collector 接続の 3 点で固定した。
- 2026-03-08 [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S4-02]: 本計画は syntax / metadata / validation / future extension path の docs fixation を目的としており、実装本体の blocker は解消済みと判断する。archive 後の後続着手は `P2-RUNTIME-SOT-LINKED-PROGRAM-*` と `P2-RUNTIME-HELPER-GENERICS-*` 系で扱う。
