# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-14

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

### P2

1. [ ] [ID: P2-MULTILANG-EXTERN-RUNTIME-REALIGN-01] 全言語の `@extern` runtime/emitter 契約を見直し、generated rewrite ではなく native owner + generic extern metadata に揃える。
文脈: [docs/ja/plans/p2-multilang-extern-runtime-realign.md](../plans/p2-multilang-extern-runtime-realign.md)
- 進捗メモ: `std/math,time,os,os_path,sys,glob` と `built_in/io_ops,scalar_ops` の manifest postprocess・native owner・emitter hardcode・generated drift inventory/checker を固定し、`S2-03` までで emitter hardcode inventory は全 row green。`S3-01` first bundle として representative smoke inventory/checker を追加し、`std/math/time` と `std/os/os_path/sys/glob` / `io_ops/scalar_ops` の current evidence path を contract へ固定した。追加で JS/TS `std/math,time` は generated wrapper から host binding 直書きを除き、`native/std/*_native` seam と rollout/baseline contract へ同期した。さらに C#/JS/TS `std/math` manifest postprocess を generic owner-wrapper helper へ寄せ、Java `std/time` も generated wrapper から `native/std/time_native.java` seam へ切り替えた。

2. [ ] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01] bundle-based coverage matrix を導入し、`feature x lane x backend` の contract coverage 100% を support matrix と分離して固定する。
文脈: [docs/ja/plans/p2-backend-contract-coverage-100.md](../plans/p2-backend-contract-coverage-100.md)
- 進捗メモ: 未着手。

3. [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01] `py_runtime.h` の typed fallback を EAST3 / C++ emitter / runtime SoT 側へ押し戻し、header を物理分割なしで縮める。
文脈: [docs/ja/plans/p2-cpp-pyruntime-upstream-fallback-shrink.md](../plans/p2-cpp-pyruntime-upstream-fallback-shrink.md)
- 進捗メモ: 未着手。
