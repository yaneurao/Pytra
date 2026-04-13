<a href="../../en/todo/infra.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# TODO — インフラ・ツール・仕様

> 領域別 TODO。全体索引は [index.md](./index.md) を参照。

最終更新: 2026-04-14

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
5. [ ] [ID: P1-PARITY-CONSOLIDATION-S5] 旧版削除とテスト整理
6. [x] [ID: P1-PARITY-CONSOLIDATION-S6] `pytra-cli.py` の `_build_pipeline` で `target="js"` → `target_language="ts"` 変換を追加する
   - 2026-04-14: `_build_pipeline()` に lowering 用 `js -> ts` マッピングを追加。

### 保留中タスク

- P20-INT32 は [plans/p4-int32-default.md](../plans/p4-int32-default.md) に保留中。再開時にここへ戻す。
