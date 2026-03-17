# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-18（P5-CPP-PY-IS-TYPE-DEAD-CODE-REMOVE-01 追加）

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

### P5: py_runtime.h 縮小

#### P5-1: py_is_type デッドコード除去

文脈: [docs/ja/plans/p5-cpp-py-is-type-dead-code-remove.md](../plans/p5-cpp-py-is-type-dead-code-remove.md)

1. [ ] [ID: P5-CPP-PY-IS-TYPE-DEAD-CODE-REMOVE-01] `py_is_dict` / `py_is_list` / `py_is_set` / `py_is_str` / `py_is_bool` / `py_is_int` / `py_is_float` を `py_runtime.h` から削除する。emitter は `PYTRA_TID_*` + `py_runtime_value_isinstance` 体系に移行済みでありデッドコード化している。

#### P5-2: FloorDiv / Mod の EAST3 IR ノード化

文脈: [docs/ja/plans/p5-east3-floordiv-mod-node.md](../plans/p5-east3-floordiv-mod-node.md)

2. [ ] [ID: P5-EAST3-FLOORDIV-MOD-NODE-01] `py_floordiv` / `py_mod` を EAST3 IR ノード経由の C++ インライン emit に変更し、`py_runtime.h` から除去する。各言語バックエンドが floor 除算・modulo を言語ネイティブに生成できる基盤を整える。

### P6: py_runtime.h 縮小・多言語対応

#### P6-1: C++ emitter リストミューテーション IR バイパス修正

文脈: [docs/ja/plans/p6-cpp-list-mut-ir-bypass-fix.md](../plans/p6-cpp-list-mut-ir-bypass-fix.md)

1. [ ] [ID: P6-CPP-LIST-MUT-IR-BYPASS-FIX-01] `cpp_emitter.py` が `py_list_*_mut()` を直接 emit しているパスを IR ノード（ListAppend 等）経由に統一し、`py_runtime.h` から 6 関数を除去する。

#### P6-2: py_len / py_slice の EAST3 IR ノード化

文脈: [docs/ja/plans/p6-east3-len-slice-node.md](../plans/p6-east3-len-slice-node.md)

2. [ ] [ID: P6-EAST3-LEN-SLICE-NODE-01] `py_len` / `py_slice` を EAST3 IR ノード化し、C++ emitter がインライン式を生成するよう変更。`py_runtime.h` から除去する。
