# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-06

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

### P0: `cpp_list_model=pyobj` alias 維持の `rc<list<T>>` 化

1. [ ] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01] `cpp_list_model=pyobj` の alias 維持を `object` ではなく `rc<list<T>>` に置き換え、typed 要素型を保持したまま Python 互換の共有セマンティクスを成立させる。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
2. [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S1-01] `object` / `list<T>` / `rc<list<T>>` の責務境界を plan/spec で固定し、`@extern` ABI 非対象を明記する。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
3. [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S1-02] 現状の alias fallback で `object` boxing が入る生成ケースを fixture ベースで固定する。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
4. [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S2-01] C++ runtime に `rc<list<T>>` typed handle helper（生成/参照/値変換）を追加する。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
5. [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S2-02] `py_len/py_append/py_extend/py_pop/py_slice/py_at` の `rc<list<T>>` overload を追加する。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
6. [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S2-03] `rc<list<T>> <-> object`、`rc<list<T>> <-> list<T>` の最小 adapter を runtime に追加する。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
7. [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S3-01] emitter の alias 共有名判定を `object` fallback ではなく `rc<list<T>>` 宣言へ切り替える。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
8. [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S3-02] `Assign/AnnAssign` の `b = a` / 空 list 初期化 / literal 初期化で `make_object(...)` を出さず handle copy / handle new を使う。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
9. [x] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S3-03] method call / subscript / len / slice / truthy 判定の描画を `rc<list<T>>` aware に更新する。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
10. [ ] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S4-01] 関数引数・返り値・callsite coercion で `rc<list<T>>` と `list<T>` の adapter 挿入条件を整理し、ABI 境界で `list<T>` を維持する。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
11. [ ] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S4-02] `Any/object` へ流れる箇所だけ `object` boxing を残し、alias 用に入れた `object` fallback を縮小・撤去する。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
12. [ ] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S5-01] alias fixture / runtime unit / C++ backend unit を追加更新して回帰を固定する。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
13. [ ] [ID: P0-CPP-PYOBJ-RCLIST-ALIAS-01-S5-02] sample representative case（少なくとも `sample/18`）で compile/run を確認し、決定ログへ結果を残す。
文脈: `docs/ja/plans/p0-cpp-pyobj-rc-list-alias.md`
