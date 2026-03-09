# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-09

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

### P0: C++ `py_runtime.h` の core 境界を再整理し、残存 helper を上流 / 専用lane へ戻す

文脈: [docs/ja/plans/p0-cpp-pyruntime-core-boundary-realign.md](../plans/p0-cpp-pyruntime-core-boundary-realign.md)

1. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01] `py_runtime.h` の core 境界を再整理し、残存 helper を上流 / 専用lane へ戻す。
2. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S1-01] `numeric_ops/zip_ops/contains`、typed helper、tuple helper、`type_id` wrapper の checked-in caller を棚卸しし、end state を分類する。
3. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S1-02] `spec-runtime` に反しない include ownership / upstream contract / non-goal を決定ログへ固定する。
4. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S2-01] C++ emitter / prelude / generated path の helper include 収集を拡張し、`zip` / `contains` / numeric helper を explicit include 化する。
5. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S2-02] `py_runtime.h` から `numeric_ops` / `zip_ops` / `contains` の transitive include を削除し、removed-include guard を更新する。
6. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-01] typed dict subscript を `.at()` 化し、`py_dict_get` の checked-in callsite を除去する。
7. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-02] tuple constant-index を generated/runtime path でも `std::get<N>` へ寄せ、tuple `py_at` helper を縮退または退役させる。
8. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-03] typed list/dict mutation helper を object bridge 専用 surface まで縮め、typed lane は emitter direct lowering を優先する。
9. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S4-01] `type_id` registry / subtype / isinstance の ownership を `py_tid_*` 主体へ寄せ、`py_runtime.h` の wrapper を薄くする。
10. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S4-02] `test_cpp_runtime_type_id.py` と generated runtime caller を更新し、cyclic ownership が再混入しないよう guard を追加する。
11. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S5-01] `py_isinstance_of` fast path、`PyFile` alias などの small cleanup を片付ける。
12. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S5-02] representative test / parity / docs / archive を更新して閉じる。
- 進捗メモ: [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S1-01] 監査結果を active plan に反映し、初手は `numeric_ops/zip_ops/contains` の explicit include 契約固定から着手する。ここを片付けてから `py_dict_get`、tuple helper、`type_id` ownership の順に進める。
