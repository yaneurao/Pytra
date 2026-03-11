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

1. [ ] [ID: P0-CPP-PYRUNTIME-FINAL-SHRINK-01] `py_runtime.h` の final residual surface を active handoff に戻し、object bridge/type_id seam を caller 側へ寄せて header をさらに縮める。文脈: [p0-cpp-pyruntime-final-shrink.md](../plans/p0-cpp-pyruntime-final-shrink.md)
- `P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S1-01` active plan / target end state / bundle order を `check_cpp_pyruntime_header_surface.py` とその unit test に固定し、archived residual-caller handoff を live task へ差し替えた。
- `P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S2-01` C++ tracked source で未使用の object mutation wrapper 8 本を `py_runtime.h` から削除し、残 bucket を `py_append(object&)` のみへ縮めた。
- `P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S2-01` tracked C++ caller の `py_enumerate_object` も `py_list_append_mut(...)` へ upstream 化し、`py_append(object&)` は header residual seam のみになった。
- `P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S2-02` thin `type_id` residual inventory を current helper 名 (`py_runtime_value_type_id` / `py_runtime_value_isinstance` / `py_runtime_object_isinstance` / `py_runtime_type_id_is_*`) に同期し、native/generated/C#/Rust caller を 1 つの shared bucket で固定した。
- `P0-CPP-PYRUNTIME-FINAL-SHRINK-01-S2-02` `check_cpp_pyruntime_header_surface.py` に legacy generic alias signature guard を追加し、`py_runtime_type_id/py_isinstance/py_is_subtype/py_issubclass` が header に戻る drift を fail-closed にした。
