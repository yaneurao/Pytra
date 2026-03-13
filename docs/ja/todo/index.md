# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-13

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
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01] 非 C++ / 非 C# backend の checked-in `src/runtime/<lang>/pytra/**` を全廃し、repo 常設 runtime layout を `generated/native` のみに揃える。文脈: [p0-noncpp-runtime-pytra-deshim.md](../plans/p0-noncpp-runtime-pytra-deshim.md)
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S1-01] 12 backend の current `pytra/**` directory/file inventory、delete blocker references、current->target mapping を plan / contract / checker / test で固定した。
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S1-02] active contract / checker / spec wording を `generated/native only` へ切り替え、checked-in `pytra/**` 再出現を fail-fast にした。
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S2-01] Rust (`rs`) の checked-in `src/runtime/rs/pytra/**` を削除し、`py2rs` / selfhost / runtime guard / smoke から repo-tree `pytra/**` 前提を外した。
- [x] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S2-02] static family (`go/java/kotlin/scala/swift/nim`) の registry / packaging / smoke / tooling を `generated/native` 直参照へ揃え、checked-in `pytra/**` は deletion inventory としてのみ残る状態にした。
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S2-03] static family の checked-in `src/runtime/<lang>/pytra/**` を物理削除し、allowlist / inventory / representative smoke を deletion end state に同期する。
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S3-01] JS/TS の import path / shim writer / selfhost / smoke を見直し、repo-tree `src/runtime/{js,ts}/pytra/**` direct-load と compat shim 契約を撤去する。
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S3-02] Lua/Ruby/PHP の packaging / runtime copy / loader contract を `generated/native` または output-side staging へ移し、repo-tree `pytra/**` 常設前提を撤去する。
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S3-03] script family (`js/ts/lua/ruby/php`) の checked-in `src/runtime/<lang>/pytra/**` を物理削除し、representative smoke と contract baseline を deletion end state へ更新する。
- [ ] [ID: P0-NONCPP-RUNTIME-PYTRA-DESHIM-01-S4-01] docs / TODO / archive 参照 / inventory を最終同期し、「非 C++ / 非 C# backend に checked-in `pytra/` は存在しない」状態で close する。
