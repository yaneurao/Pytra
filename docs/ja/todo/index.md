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

1. [ ] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01] `py_dyn_range_*` compat wrapper を退役する。
- [x] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S1-01] `py_dyn_range` callsite を棚卸しする。
- [x] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S1-02] typed iterable への置換順序を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S2-02] `py_dyn_range_*` を削除または最小化する。
- [ ] [ID: P0-CPP-PYRUNTIME-DYNRANGE-01-S3-01] guard / parity / docs を更新する。

2. [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01] `begin/end(object)` と ADL 補助を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S1-01] range-for compat callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S1-02] typed iterable 置換方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S2-02] `begin/end(object)` と ADL 補助を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-BEGINEND-01-S3-01] parity / docs / archive を更新する。

3. [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01] object-string comparison convenience を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S1-01] object-string 比較 callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S1-02] explicit decode 置換方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S2-02] comparison overload を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRCMP-01-S3-01] guard / parity / docs を更新する。

4. [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01] `py_to_str_list_from_object` を退役する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S1-01] callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S1-02] typed argv / decode 置換方針を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S2-01] representative callsite を置換する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S2-02] helper を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-OBJECT-STRLIST-01-S3-01] parity / docs / archive を更新する。

5. [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01] `dict<str, str>` 用 `dict_get_node` overload を縮退する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S1-01] checked-in callsite を棚卸しする。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S1-02] 残す最小 wrapper を固定する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S2-01] redundant overload を削除する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S2-02] representative tests を更新する。
- [ ] [ID: P0-CPP-PYRUNTIME-DICT-STR-NODE-01-S3-01] docs / archive を同期する。

6. [ ] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01] JS/TS 向け ambient global extern 変数を導入する。
- [ ] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S1-01] `extern()` / `extern("symbol")` の variable ambient-global 契約を docs に固定する。
- [ ] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S1-02] 既存 `extern(expr)` host fallback との切り分けを決定ログへ固定する。
- [ ] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S2-01] parser / EAST metadata に ambient global variable marker を追加する。
- [ ] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S2-02] representative IR/unit test で same-name / alias case を固定する。
- [ ] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S3-01] JS/TS emitter で ambient global extern variable を import-free symbol へ lower する。
- [ ] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S3-02] ambient global `Any` receiver の property/method/call raw lowering を追加する。
- [ ] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S4-01] unsupported backend guard / representative smoke を更新する。
- [ ] [ID: P2-JS-AMBIENT-GLOBAL-EXTERN-01-S4-02] docs / archive を同期して本計画を閉じる。

7. [ ] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01] compiler/backend 内部の JSON raw-dict loader を `JsonValue` decode-first 契約へ揃える。
- [ ] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S1-01] compiler/backend 内部で `json.loads(...)` を直接使う箇所を棚卸しする。
- [ ] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S1-02] selfhost blocker と host-only 後回し対象を決定ログへ固定する。
- [ ] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S2-01] `transpile_cli.py` の JSON root loader を `loads_obj()` ベースへ移行する。
- [ ] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S2-02] `runtime_symbol_index.py` と `code_emitter.py` の JSON loader を `JsonValue` lane へ移行する。
- [ ] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S3-01] backend internal loader（`js_emitter.py` など）を `JsonValue` lane へそろえる。
- [ ] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S3-02] representative tests / selfhost-related regressions を更新する。
- [ ] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S4-01] raw `json.loads(...)` 再侵入 guard を追加する。
- [ ] [ID: P3-COMPILER-JSONVALUE-INTERNAL-01-S4-02] docs / archive を同期して本計画を閉じる。

8. [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01] C++ selfhost の stage1 build / direct route / diff / stage2 を current runtime/layout 契約に合わせて復旧する。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S1-01] `tools/build_selfhost.py` 失敗点と missing artifact を棚卸しする。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S1-02] selfhost 復旧の受け入れ順序と current source of truth を決定ログへ固定する。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S2-01] stage1 build に必要な generated/static frontend artifact 供給を current layout に合わせて復旧する。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S2-02] `tools/build_selfhost.py` を green に戻し、`selfhost/py2cpp.out` を再生成する。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S3-01] direct `.py` route を復旧し、`tools/check_selfhost_direct_compile.py` を通す。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S3-02] host/selfhost diff と representative e2e を green に戻す。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S4-01] `tools/build_selfhost_stage2.py` を current contract に合わせて復旧する。
- [ ] [ID: P4-CPP-SELFHOST-ROLLOUT-01-S4-02] docs / archive / local CI gate 方針を更新して本計画を閉じる。
