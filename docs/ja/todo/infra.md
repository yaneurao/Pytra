<a href="../../en/todo/infra.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — インフラ・ツール・仕様

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-25

## 運用ルール

- 各タスクは `ID` と文脈ファイル（`docs/ja/plans/*.md`）を必須にする。
- 優先度順（小さい P 番号から）に着手する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める。
- **タスク完了時は `[ ]` を `[x]` に変更し、完了メモを追記してコミットすること。**
- 完了済みタスクは定期的に `docs/ja/todo/archive/` へ移動する。

完了済みタスクは [アーカイブ](archive/20260403.md) を参照。

## 未完了タスク

### P0-SELFHOST-MODULE-CLOSURE: selfhost build の transitive import 解決漏れを調査・固定する

2026-04-11 の再調査で、当初疑った build driver の `ImportFrom` closure 欠落は再現しなかった。`_collect_build_sources()`、link manifest、C++ emit のいずれにも `expand_defaults.py -> type_norm.py` は入っていた。最初の missing include は、C++ backend の別 abort 後に見ていた partial emit 生成物を blocker と誤診していたもの。

このタスクで実際に直したのは、
- `_collect_build_sources()` に対する closure regression test の追加
- `run_selfhost_parity.py` が欠損していた `collect_runtime_cpp_sources` helper 依存を fallback で復旧

までであり、build driver 本体の closure ロジック変更は不要だった。

1. [x] [ID: P0-SELFHOST-CLOSURE-S1] selfhost build driver の module collection ロジックを調査し、transitive import 解決漏れの原因を特定する
   - 2026-04-11: `_collect_build_sources()` は `toolchain.link.expand_defaults` と `toolchain.resolve.py.type_norm` を正しく収集していた。誤診だったことを確認。
2. [x] [ID: P0-SELFHOST-CLOSURE-S2] entry point からの reachability closure が `ImportFrom` を確実に追うように修正する
   - 2026-04-11: build driver 本体の修正は不要。代わりに `tools/unittest/tooling/test_pytra_cli2.py` に selfhost closure 回帰テストを追加。
3. [x] [ID: P0-SELFHOST-CLOSURE-S3] C++ selfhost で `expand_defaults.py → type_norm.py` が emit 対象に入ることを確認する
   - 2026-04-11: linked manifest と C++ emit 単体で `toolchain/resolve/py/type_norm.h` / `toolchain_resolve_py_type_norm.cpp` が出ることを確認。
4. [x] [ID: P0-SELFHOST-CLOSURE-S4] Go selfhost の既存テストに回帰がないことを確認する（module set が広がるため）
   - 2026-04-11: `run_selfhost_parity.py` の fallback は C++ branch 限定で、共通 regression test も通過。Go selfhost 側の driver 挙動に変更なし。

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

### P1-PARITY-CONSOLIDATION: runtime_parity_check.py を fast 版に統合する

文脈: [docs/ja/plans/p1-parity-check-consolidation.md](../plans/p1-parity-check-consolidation.md)

旧版 `runtime_parity_check.py` は `pytra-cli.py` subprocess 方式で、JS の `"js"` → `"ts"` マッピング漏れ等メンテが追いついていない。fast 版（in-memory API）に一本化する。

1. [x] [ID: P1-PARITY-CONSOLIDATION-S1] `check_noncpp_backend_health.py` の旧版呼び出しを fast 版に切り替える
   - 2026-04-14: parity 実行を `tools/check/runtime_parity_check_fast.py` へ切替。
2. [x] [ID: P1-PARITY-CONSOLIDATION-S2] `regenerate_samples.py` の旧版参照を fast 版に変更する
   - 2026-04-14: `--verify-cpp-on-diff` の検証経路を fast 版へ切替。
3. [x] [ID: P1-PARITY-CONSOLIDATION-S3] ドキュメント一括更新（tutorial / README / spec-tools.md のコマンド例を fast 版に書き換え）
   - 2026-04-14: `spec-tools.md` / tutorial / `tools/README.md` / `sample/README*.md` を更新し、`runtime_parity_check.py` を fast-backed 正規エントリとして明記。
4. [x] [ID: P1-PARITY-CONSOLIDATION-S4] fast 版を `runtime_parity_check.py` にリネームするか検討・実施する
   - 2026-04-14: 物理リネームは見送り。`runtime_parity_check.py` を fast 実装へ委譲する正規エントリにし、`runtime_parity_check_fast.py` は互換エイリアスとして維持する方針に決定。
5. [x] [ID: P1-PARITY-CONSOLIDATION-S5] 旧版削除とテスト整理
   - 2026-04-25: `runtime_parity_check.py` を fast 実装へ委譲する薄い正規エントリに置換し、共有 helper を `runtime_parity_shared.py` へ分離。旧 subprocess 版の `build_targets` / `check_case` を削除し、CLI テストを fast 経路へ整理。
6. [x] [ID: P1-PARITY-CONSOLIDATION-S6] `pytra-cli.py` の `_build_pipeline` で `target="js"` → `target_language="ts"` 変換を追加する
   - 2026-04-14: `_build_pipeline()` に lowering 用 `js -> ts` マッピングを追加。

### P1-DATACLASS-OVER-JSONVAL-DICT: 一時構造体の dict[str, JsonVal] を @dataclass に置き換える

文脈: [docs/ja/plans/p1-dataclass-over-jsonval-dict.md](../plans/p1-dataclass-over-jsonval-dict.md)

toolchain 内部で一時的なデータ受け渡しに `dict[str, JsonVal]` を多用している箇所を `@dataclass` に置き換え、selfhost の型解決を安定させる。emitter の手前の段（parse/resolve/compile/link）を優先。

1. [x] [ID: P1-DATACLASS-DICT-S1] 棚卸し: selfhost blocker に直結する/しそうな一時構造体の洗い出しと優先順位付け
   - 2026-04-25: `dict[str, JsonVal]` 出現箇所を parse/resolve/compile/link で棚卸し。優先順を `type_summary.py` summary dataclass 化、`parser.py` import metadata、`resolver.py` import resolution metadata、`linker.py` manifest row の順に確定。
2. [x] [ID: P1-DATACLASS-DICT-S2] parse 層（`src/toolchain/parse/py/`）の @dataclass 化
   - 2026-04-25: `parser.py` の `import_bindings` / `qualified_refs` を `ImportBindingDraft` / `QualifiedSymbolRefDraft` に置換。`nodes.py` の `to_jv()` と EAST JSON metadata 生成は外部 JSON 契約のため非対象として維持。
3. [x] [ID: P1-DATACLASS-DICT-S3] resolve 層（`src/toolchain/resolve/py/`）の @dataclass 化
   - 2026-04-25: `resolver.py` の import resolution binding 拡張を `ImportResolutionBinding` 経由に変更。EAST 入力 accessor と最終 metadata JSON は従来どおり dict/list のまま維持。
4. [x] [ID: P1-DATACLASS-DICT-S4] compile 層（`src/toolchain/compile/`）の @dataclass 化
   - 2026-04-25: `type_summary.py` の type summary payload builder を `TypeSummary` dataclass 経由に変更。追加で `lower.py` の target/iter plan draft を `TargetPlanDraft` / `RuntimeIterPlanDraft` / `StaticRangePlanDraft` に置換。EAST node builder と JSON accessor は非対象として維持。
5. [x] [ID: P1-DATACLASS-DICT-S5] link 層（`src/toolchain/link/`）の @dataclass 化
   - 2026-04-25: `linker.py` の `linked_program_v1` / manifest module entry / manifest global / diagnostics を draft dataclass 経由で生成。`type_stubgen.py` などの synthetic EAST node builder は非対象として維持。
6. [x] [ID: P1-DATACLASS-DICT-S6] emit/common/ の @dataclass 化（`common_renderer.py` 82箇所、`cli_runner.py` 9箇所、`profile_loader.py` 6箇所）
   - 2026-04-25: `profile_loader.py` の default profile doc を `LoweringProfileDocDraft` 経由に変更し、`cli_runner.py` の manifest module entry 取り込みを `ManifestModuleEntryDraft` に集約。`common_renderer.py` の EAST node 入力 dict は非対象として維持。
7. [x] [ID: P1-DATACLASS-DICT-S7] emit/cpp/ の @dataclass 化（`emitter.py` 116箇所、`header_gen.py` 18箇所、`runtime_bundle.py` 11箇所）
   - 2026-04-25: `runtime_bundle.py` の runtime artifact result、`header_gen.py` の include 行 draft、`emitter.py` の class variable spec を dataclass 経由に変更。EAST node 入力 dict と C++ AST 走査 helper は非対象として維持。

### P0-FIXTURE-PARITY-161: 全 backend を fixture 161/161 に揃える

文脈: [docs/ja/plans/p0-fixture-parity-161.md](../plans/p0-fixture-parity-161.md)

fixture が 146 → 161 に増えたが、C++ 以外の 17 backend が追いついていない。各 backend で fail しているケースを修正し 161/161 に揃える。

現状（2026-04-27 gen_backend_progress.py 出力）:

| backend | pass/total | fail |
|---|---|---|
| rs | 151/161 | 10 |
| cs | 135/161 | 26 |
| ps1 | 153/161 | 8 |
| js | 151/161 | 10 |
| ts | 150/161 | 11 |
| dart | 148/161 | 13 |
| go | 154/161 | 7 |
| java | 152/161 | 9 |
| scala | 139/161 | 22 |
| kotlin | 141/161 | 20 |
| swift | 153/161 | 8 |
| ruby | 155/161 | 6 |
| lua | 157/161 | 4 |
| php | 154/161 | 7 |
| nim | 142/161 | 19 |
| julia | 156/161 | 5 |
| zig | 150/161 | 11 |

1. [x] [ID: P0-FIX161-S1] 各 backend の fail ケースを `runtime_parity_check_fast.py --targets <lang> --case-root fixture` で特定し、fail リストを作成する
   - 2026-04-27: `backend-progress-fixture.md` の 161 件マトリクスと `.parity-results/*_fixture.json` から言語別 fail / 未実行リストを `docs/ja/plans/p0-fixture-parity-161.md` に整理。全言語 fresh sweep は重いため spot check まで実施。
2. [x] [ID: P0-FIX161-S2] fail 原因を分類する（emitter 未対応 / runtime 未実装 / golden 未生成 / EAST3 前段問題）
   - 2026-04-27: 未実行 / runtime 未実装・互換不足 / emitter 未対応 / import wiring / 型・narrowing・union runtime / 数値型 / 実行環境・profile 不整合へ分類。golden 未生成単独の blocker は現時点では確認なし。
3. [x] [ID: P0-FIX161-S3] 各 backend 担当が自分の言語を 161/161 に修正する（各言語 TODO にサブタスク展開）
   - 2026-04-27: `rust.md` / `cs.md` / `powershell.md` / `ts.md` / `dart.md` / `go.md` / `java.md` / `swift.md` / `ruby.md` / `lua.md` / `php.md` / `nim.md` / `julia.md` / `zig.md` に P0 fixture parity 161 タスクを追加。Java/Scala/Kotlin と JS/TS は共有 TODO 内で個別 ID に展開。

### 保留中タスク

- P20-INT32 は [plans/p4-int32-default.md](../plans/p4-int32-default.md) に保留中。再開時にここへ戻す。
