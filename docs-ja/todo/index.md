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



## メモ

- このファイルは未完了タスクのみを保持します。
- 完了済みタスクは `docs-ja/todo/archive/index.md` 経由で履歴へ移動します。
- `docs-ja/todo/archive/index.md` は索引のみを保持し、履歴本文は `docs-ja/todo/archive/YYYYMMDD.md` に日付単位で保存します。

## P1: CppEmitter の pylib 互換名正規化除去（中優先）

文脈: `docs-ja/plans/p1-cpp-emitter-remove-pylib-compat.md`（`P1-CPP-EMIT-NORM-01`）

1. [ ] [ID: P1-CPP-EMIT-NORM-01] `src/hooks/cpp/emitter/cpp_emitter.py` の `_normalize_runtime_module_name` を削除し、`pylib.*` 互換名を前提としない runtime module 解決へ切り替える（`P1-CPP-EMIT-NORM-01-S1` 〜 `S3` の完了でクローズ）。
2. [x] [ID: P1-CPP-EMIT-NORM-01-S1] `src/hooks/cpp/emitter/cpp_emitter.py` と `src/hooks/cpp/emitter/call.py` の該当呼び出しを洗い出し、`module_name` 正規化なしでの解決パスへ置換する。
3. [ ] [ID: P1-CPP-EMIT-NORM-01-S2] `src/pytra/compiler/east_parts/code_emitter.py` の同名的な正規化利用有無を確認し、必要なら `pylib` 前提経路を削減する。
4. [ ] [ID: P1-CPP-EMIT-NORM-01-S3] 回帰テスト/ドキュメントを整備し、`pylib.*` 互換を求めるケースが存在しないことを明文化する（`docs-ja/spec/spec-dev.md` 追記含む）。

## P1: CppEmitter 多重継承廃止（中優先）

文脈: `docs-ja/plans/p1-cpp-emitter-no-multiple-inheritance.md`（`P1-CPP-EMIT-NOMI-01`）

1. [ ] [ID: P1-CPP-EMIT-NOMI-01] `src/hooks/cpp/emitter/cpp_emitter.py` の多重継承を廃止し、単一継承 + 明示的委譲へ切り替える。
2. [x] [ID: P1-CPP-EMIT-NOMI-01-S1] `cpp_emitter.py` の状態管理を維持しつつ、`CppCallEmitter`/`CppStatementEmitter`/`CppExpressionEmitter`/`CppBinaryOperatorEmitter`/`CppTriviaEmitter`/`CppTemporaryEmitter` のメソッドを `CppEmitter` へデリゲーション注入し、単一継承化を実現する。
3. [ ] [ID: P1-CPP-EMIT-NOMI-01-S2] `CppEmitter` 単一継承移行中の `isinstance()`/型チェック関連の条件分岐を簡素化し、分岐経路を明示フラグ化する。
