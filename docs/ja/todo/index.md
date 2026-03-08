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

1. [ ] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01] `JsonValue` を使って selfhost/host の JSON artifact 境界を decode-first 契約へ揃える。
   文脈: [p2-jsonvalue-selfhost-decode-alignment.md](../plans/p2-jsonvalue-selfhost-decode-alignment.md)
   - [x] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S1-01] selfhost/host の JSON loader で `dict[str, object]` / `list[object]` を直接前提にしている箇所を棚卸しする。
     進捗メモ: `py2x` / `ir2lang` / `east_io` / `toolchain/link/*` が raw JSON artifact 境界で、`py2x-selfhost.py` 本体は間接依存だけを持つと整理した。
   - [x] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S1-02] docs に「selfhost は `match` ではなく decode helper ベースで `JsonValue` を使う」契約を固定する。
     進捗メモ: `spec-dev` に selfhost/host JSON artifact loader も `loads_obj` / `JsonValue.as_*` / `JsonObj.get_*` を正本とする契約を追記した。
   - [x] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S2-01] `pytra.std.json` に selfhost-ready な `loads_obj` / `loads_arr` / `JsonObj.get_*` 最小APIを定義する。
     進捗メモ: `loads_arr`, `JsonValue.as_*`, `JsonObj.get/get_*`, `JsonArr.get/get_*` を追加し、checked-in C++ runtime と forward decl 回帰を同期した。
   - [x] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S2-02] `program_loader` / `program_validator` の JSON decode を `JsonValue` helper ベースへ移行する。
     進捗メモ: `link` 系 loader/validator は `loads_obj` / `JsonObj.get_*` を内部 decode の正本にしつつ、外向け return contract は raw dict のまま維持した。
   - [x] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S3-01] `py2x.py` / `py2x-selfhost.py` / `ir2lang.py` の JSON artifact 境界を `JsonValue` decode lane へ揃える。
     進捗メモ: `py2x` の link-input 判定、`ir2lang` の wrapped/root unwrap、`east_io` の `.json` 入口を `loads_obj` / `JsonObj.get_*` ベースへ揃え、`py2x-selfhost.py` 本体は indirect 依存だけを維持した。
   - [x] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S3-02] representative selfhost / linked-program / CLI tests を `JsonValue` 経路で green にする。
     進捗メモ: `test_py2x_cli` / `test_ir2lang_cli` / `test_pylib_json` / `test/unit/link/test_*.py` と `check_noncpp_east3_contract --skip-transpile` を `JsonValue` 経路で通した。
   - [ ] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S4-01] raw object tree 依存の再侵入を防ぐ guard / regression を追加する。
   - [ ] [ID: P2-JSONVALUE-SELFHOST-ALIGN-01-S4-02] docs / decision log / archive 同期まで完了し、本計画を閉じる。
