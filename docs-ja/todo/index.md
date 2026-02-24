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



## P1: C++ Emitter Reduction

### 文脈
- `docs-ja/plans/p1-cpp-emitter-reduce.md`

### タスク（S1〜S8, 小粒度）

1. [ ] [ID: P1-CPP-EMIT-01] `CppEmitter` の責務分類を確定し、`expression/render/statement/runtime_call/cast/control_flow/misc` の移管対象を固定する。
2. [ ] [ID: P1-CPP-EMIT-01-S1] `CppEmitter` の expression rendering のヘルパ群を `src/hooks/cpp/emitter/expr.py` 相当へ移譲し、呼び出し元を最小差分で切り替える。
3. [ ] [ID: P1-CPP-EMIT-01-S2] statement rendering のうち `For`/`While`/`If`/`Try` 系を `src/hooks/cpp/emitter/stmt.py` 側に移譲する。
4. [ ] [ID: P1-CPP-EMIT-01-S3] cast / runtime-call / import の分岐を専用ヘルパへ整理し、重複分岐を削減する。
5. [ ] [ID: P1-CPP-EMIT-01-S4] `temp` 名生成（`__tmp`）と一時変数生存域管理を 1 モジュールへ集約し、同名ロジックの重複を除去する。
6. [ ] [ID: P1-CPP-EMIT-01-S5] `fallback_tuple_target_names_from_repr` 系の変換ロジックを共通処理に集約し、`code_emitter` 側互換を壊さずに移管する。
7. [ ] [ID: P1-CPP-EMIT-01-S6] `cast`/`object receiver` 周辺の分岐を 1 ハンドラに寄せ、`emit_binary_op` 系の条件分岐重複を 1/3 以下に抑える。
8. [ ] [ID: P1-CPP-EMIT-01-S7] `render_trivia` とコメント/ディレクティブ処理を切り出し、`docs-ja/plans/p1-codeemitter-dispatch-redesign.md` との責務整合を確認する。
9. [ ] [ID: P1-CPP-EMIT-01-S8] `py2cpp.py` から CppEmitter 本体ロジック参照をなくし、CLI/配線だけに絞る。
10. [ ] [ID: P1-CPP-EMIT-01-S9] 上位 API 互換を保ったまま `check_py2cpp_transpile` / `test_py2cpp_smoke` を回して回帰検証を固定する。

### 対応方針
- 1 つの `S*` は原則 1〜3 関数単位で着手し、1 タスクあたり 1 コミット以内で完了可能な粒度にする。
- 各 `S*` の終端で `git diff` を確認し、受け入れ基準を `docs-ja/plans/p1-cpp-emitter-reduce.md` の決定ログに追記する。


## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs-ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs-ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。
