# TODO（未完了）

> `docs-ja/` が正（source of truth）です。`docs/` はその翻訳です。

<a href="../../docs/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-25

## 文脈運用ルール

- 各タスクは `ID` と文脈ファイル（`docs-ja/plans/*.md`）を必須にする。
- 優先度上書きは `docs-ja/plans/instruction-template.md` 形式でチャット指示し、`todo2.md` は使わない。
- 着手対象は「未完了の最上位優先度ID（最小 `P<number>`、同一優先度では上から先頭）」に固定し、明示上書き指示がない限り低優先度へ進まない。
- `P0` が 1 件でも未完了なら `P1` 以下には着手しない。
- 着手前に文脈ファイルの `背景` / `非対象` / `受け入れ基準` を確認する。
- 進捗メモとコミットメッセージは同一 `ID` を必ず含める（例: ``[ID: P0-XXX-01] ...``）。
- `docs-ja/todo/index.md` の進捗メモは 1 行要約に留め、詳細（判断・検証ログ）は文脈ファイル（`docs-ja/plans/*.md`）の `決定ログ` に記録する。
- 1 つの `ID` が大きい場合は、文脈ファイル側で `-S1` / `-S2` 形式の子タスクへ分割して進めてよい（親 `ID` 完了までは親チェックを維持）。
- 割り込み等で未コミット変更が残っている場合は、同一 `ID` を完了させるか差分を戻すまで別 `ID` に着手しない。
- `docs-ja/todo/index.md` / `docs-ja/plans/*.md` 更新時は `python3 tools/check_todo_priority.py` を実行し、差分に追加した進捗 `ID` が最上位未完了 `ID`（またはその子 `ID`）と一致することを確認する。
- 作業中の判断は文脈ファイルの `決定ログ` へ追記する。



## P3: test/misc 追加サンプルの変換復旧（超低優先）

### 文脈
- `docs-ja/plans/p3-misc-extended-transpile.md`

### タスク（S001〜S008）

1. [ ] [ID: P3-MISC-02-S001] `test/misc/101_*` 〜 `test/misc/150_*` を `py2cpp.py` で C++ 変換可能にする。
2. [ ] [ID: P3-MISC-02-S002] `test/misc/151_*` 〜 `test/misc/200_*` を `py2cpp.py` で C++ 変換可能にする。
3. [ ] [ID: P3-MISC-02-S003] `test/misc/201_*` 〜 `test/misc/250_*` を `py2cpp.py` で C++ 変換可能にする。
4. [ ] [ID: P3-MISC-02-S004] `test/misc/251_*` 〜 `test/misc/300_*` を `py2cpp.py` で C++ 変換可能にする。
5. [ ] [ID: P3-MISC-02-S005] `test/misc/301_*` 〜 `test/misc/350_*` を `py2cpp.py` で C++ 変換可能にする。
6. [ ] [ID: P3-MISC-02-S006] `test/misc/351_*` 〜 `test/misc/400_*` を `py2cpp.py` で C++ 変換可能にする。
7. [ ] [ID: P3-MISC-02-S007] `test/misc/401_*` 〜 `test/misc/450_*` を `py2cpp.py` で C++ 変換可能にする。
8. [ ] [ID: P3-MISC-02-S008] `test/misc/451_*` 〜 `test/misc/500_*` を `py2cpp.py` で C++ 変換可能にする。

- 上記 8 タスクは超低優先（P3）として、難度順で着手する。`test/misc` 側を編集しないことを前提とする。


## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs-ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs-ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。
