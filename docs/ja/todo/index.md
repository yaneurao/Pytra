# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-08

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

- [ ] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01] C++ `py_runtime.h` を `@template` ベースで縮退させる。文脈: [p1-cpp-pyruntime-template-slimming.md](../plans/p1-cpp-pyruntime-template-slimming.md)
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S1-01] `py_runtime.h` に残る generic helper 候補を棚卸しし、第一波 / 第二波 / 保留へ分類する。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S1-02] `spec-template` / `spec-runtime` / `spec-east` / `spec-linker` に helper-limited `@template` の責務境界と specialization 契約を追記する。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S2-01] parser / EAST metadata / validator で `@template("T", ...)` を runtime helper 限定で受理する。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S2-02] linked-program 側に specialization collector と monomorphization の最小実装を入れる。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-01] `sum` / `min` / `max` を pure Python generic helper として SoT 側へ移し、C++ generated helper へ切り替える。
- [x] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S3-02] `zip` / `sorted` のうち少なくとも 1 系統以上を同様に移し、`py_runtime.h` から hand-written helper を撤去する。
- [ ] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S4-01] runtime symbol index / build graph / representative backend/runtime tests を新 contract へ追従させる。
- [ ] [ID: P1-CPP-PYRUNTIME-TEMPLATE-SLIM-01-S4-02] fixture/sample parity・docs 同期・必要な guard 追加まで完了し、本計画を閉じる。
