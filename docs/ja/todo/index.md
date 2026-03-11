# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-12

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

### P1: relative import の second wave (`js/ts`) に対する representative transpile smoke を固定し、remaining backend handoff を整える

文脈: [docs/ja/plans/p1-relative-import-secondwave-smoke.md](../plans/p1-relative-import-secondwave-smoke.md)

1. [ ] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01] `js/ts` の relative import representative transpile smoke を lock し、coverage inventory / docs handoff を次 baseline に更新する。
2. [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S1-01] live plan / TODO と `js/ts` second-wave smoke contract を固定した。
3. [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S2-01] `py2js` smoke に representative relative import transpile case を追加した。
4. [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S2-02] `py2ts` smoke に representative relative import transpile case を追加した。
5. [ ] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-SMOKE-01-S3-01] coverage inventory / backend parity docs / handoff metadata を `js/ts` baseline へ同期して close-ready にする。
- 進捗メモ: `js/ts` は contract 駆動の representative transpile smoke を lock 済みで、残りは `js/ts` coverage baseline と handoff metadata の同期だけになった。

### P1: relative import second-wave rollout planning

文脈: [p1-relative-import-secondwave-planning.md](../plans/p1-relative-import-secondwave-planning.md)

1. [ ] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01] second-wave relative import rollout の live contract / docs handoff / verification lane を固定する。
2. [x] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01-S1-01] live plan / TODO と second-wave rollout contract / checker / docs handoff を追加した。
3. [ ] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01-S2-01] second-wave backend ごとの representative smoke / fail-closed 導入順を backend group 単位の bundle に落とす。
4. [ ] [ID: P1-RELATIVE-IMPORT-SECONDWAVE-PLANNING-01-S3-01] coverage docs / support wording / archive handoff を second-wave current state に同期して task を閉じる。

- 進捗メモ: second-wave backend 集合は `go/java/js/kotlin/nim/scala/swift/ts`、representative scenario は `parent_module_alias` / `parent_symbol_alias`、handoff は live plan `p1-relative-import-secondwave-planning.md` に同期した。
