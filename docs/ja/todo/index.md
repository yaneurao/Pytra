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

1. [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01] `py_runtime.h` の object read bridge（`py_at(object)` / `py_slice(object)`）を退役し、typed / `JsonArr` accessor を正本に寄せる。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S1-01] `py_at(object)` / `py_slice(object)` の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S1-02] `JsonArr` 依存と削除順序を決定ログへ固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S2-01] JSON / runtime callsite を typed / nominal accessor へ置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S2-02] representative regression を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S3-01] `py_at(object)` / `py_slice(object)` を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-READ-01-S3-02] parity / docs / archive を更新して閉じる。

2. [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01] `py_dict_get(dict<str, object>, ...)` 直取得 lane を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S1-01] direct getter の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S1-02] `JsonObj` / typed dict への置換方針を決定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S2-01] callsite を `JsonObj` accessor へ寄せる。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S2-02] `py_runtime.h` から direct getter を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-DICTGET-01-S3-01] regression / parity / docs を更新する。

3. [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01] `py_dict_get_maybe` convenience を縮退する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S1-01] `py_dict_get_maybe` callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S1-02] `JsonObj` / explicit default への移行方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S2-02] `py_dict_get_maybe` overload を削減する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-MAYBE-01-S3-01] guard / docs / parity を更新する。

4. [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01] generic `py_dict_get_default` overload を縮退する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S1-01] generic overload の checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S1-02] 残す primitive wrapper を決定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S2-01] redundant overload を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S2-02] codegen / runtime tests を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-GENERIC-01-S3-01] parity / docs / archive を同期する。

5. [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01] `dict<str, object>` 専用 `py_dict_get_default` を縮退する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S1-01] object-dict default access の callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S1-02] `JsonObj.get_*` へ寄せる順序を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S2-01] representative callsite を `JsonObj` helper へ移す。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S2-02] object-dict default overload を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTDEFAULT-OBJECT-01-S3-01] regression / parity / docs を更新する。

6. [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01] `dict_get_*` convenience を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S1-01] `dict_get_*` callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S1-02] `JsonObj` API への置換表を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S2-01] representative callsite / tests を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S2-02] `dict_get_*` convenience を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICTGET-CONVENIENCE-01-S3-01] guard / parity / docs を更新する。

7. [ ] [ID: P0-CPP-PYRUNTIME-DYNITER-01] dynamic iteration primitive を縮退する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S1-01] `py_iter_or_raise/object` callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S1-02] typed / nominal 置換方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S2-02] primitive bridge を削除または最小化する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNITER-01-S3-01] parity / docs / archive を更新する。

8. [ ] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01] `py_dyn_range_*` compat wrapper を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S1-01] `py_dyn_range` callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S1-02] typed iterable への置換順序を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S2-02] `py_dyn_range_*` を削除または最小化する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S3-01] guard / parity / docs を更新する。

9. [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01] `begin/end(object)` と ADL 補助を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S1-01] range-for compat callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S1-02] typed iterable 置換方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S2-02] `begin/end(object)` と ADL 補助を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S3-01] parity / docs / archive を更新する。

10. [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01] object-string comparison convenience を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S1-01] object-string 比較 callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S1-02] explicit decode 置換方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S2-02] comparison overload を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S3-01] guard / parity / docs を更新する。

11. [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01] `py_to_str_list_from_object` を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S1-01] callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S1-02] typed argv / decode 置換方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S2-02] helper を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S3-01] parity / docs / archive を更新する。

12. [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01] `dict<str, str>` 用 `dict_get_node` overload を縮退する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S1-01] checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S1-02] 残す最小 wrapper を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S2-01] redundant overload を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S2-02] representative tests を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S3-01] docs / archive を同期する。
