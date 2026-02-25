# TODO（未完了）

> `docs-ja/` が正（source of truth）です。`docs/` はその翻訳です。

<a href="../../docs/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-02-26

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

## P2: C++ selfhost の virtual ディスパッチ簡略化（低優先）

文脈: `docs-ja/plans/p2-cpp-virtual-selfhost-dispatch.md`（`P2-CPP-SELFHOST-VIRTUAL-01`）

1. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01] `virtual/override` ベースの selfhost クラス呼び出し経路へ縮退できる箇所を洗い出し、`type_id` 分岐を低優先で簡素化する。
2. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S2-01] `py2cpp.py` 側 emit を切り出しして、`virtual` へ寄せる対象経路と fallback 経路を分離する。
3. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S2-02] `CppEmitter` の class method 呼び出し描画で、`virtual`/`override` 有無に応じた分岐を明示化する。
4. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S2-03] 置換できない `type_id` 分岐は理由付きで残し、非対象リストへ接続する。
5. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S3-01] `sample` の 2〜3 件から `type_id` 分岐を `virtual` 呼び出しに移行する。
6. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S3-02] 移行対象を段階的に拡大し、selfhost 再変換（`sample`/`test`）の成功率を評価する。
7. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S3-03] 移行不能ケースは判定ロジックで固定し、次回に回す明細を更新する。
8. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S4-01] `test/unit` と `sample` 再生成の回帰ケースを追加・更新して diff を固定する。
9. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S4-02] `tools/check_selfhost_cpp_diff.py` と `tools/verify_selfhost_end_to_end.py` を再実行し、回帰条件が満たされることを確認する。
10. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S4-03] `docs-ja/spec/spec-dev.md`（必要なら `spec-type_id`）へ簡潔に反映する。
11. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S5-01] `test/unit` へ `Base`/`Child` の `virtual/override` 呼び出しケース（`Base.f` 明示呼び出し、`super().f`、`virtual` 期待差分）を追加し、`type_id` 分岐除去を固定する。
12. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S5-02] `sample` 再変換で `type_id` 分岐が残る境界 (`staticmethod`/`class` method/`object` receiver) を明文化した回帰ケースを追加する。
13. [ ] [ID: P2-CPP-SELFHOST-VIRTUAL-01-S5-03] `tools/verify_selfhost_end_to_end.py` を使う selfhost 回帰（最低2ケース）に virtual 化前後の差分検証を追加し、再変換可能性を固定する。

## P3: 非C++ emitter の EAST3 直結化と EAST2 互換撤去（低優先）

文脈: `docs-ja/plans/p3-east3-only-emitters.md`（`P3-EAST3-ONLY-01`）

1. [ ] [ID: P3-EAST3-ONLY-01] 非C++ 8ターゲット（`rs/cs/js/ts/go/java/swift/kotlin`）を `EAST3` 直結に統一し、`EAST2` 互換経路（`--east-stage 2` / `load_east_document_compat` / `east3_legacy_compat`）を撤去する。
2. [ ] [ID: P3-EAST3-ONLY-01-S1] 仕様/CLI 契約を `EAST3` のみに更新し、`--east-stage 2` の互換警告テストを廃止して非対応エラー基準へ移行する。
3. [ ] [ID: P3-EAST3-ONLY-01-S2] `js_emitter` を `EAST3` ノード直処理へ移行し、`js/ts/go/java/swift/kotlin` で `east3_legacy_compat` 非依存の生成経路を成立させる。
4. [ ] [ID: P3-EAST3-ONLY-01-S3] `rs_emitter` の `EAST3` 直処理を実装し、legacy 形状依存（`For/ForRange` 前提など）を撤去する。
5. [ ] [ID: P3-EAST3-ONLY-01-S4] `cs_emitter` の `EAST3` 直処理を実装し、legacy 形状依存を撤去する。
6. [ ] [ID: P3-EAST3-ONLY-01-S5] 8本 CLI から `load_east_document_compat` / `normalize_east3_to_legacy` 依存を削除し、`east3_legacy_compat.py` を削除する。
7. [ ] [ID: P3-EAST3-ONLY-01-S6] ドキュメント/仕様（`docs-ja/plans/plan-east123-migration.md` ほか）から `stage=2 互換` 前提を撤去して `EAST3 only` を明記する。
8. [ ] [ID: P3-EAST3-ONLY-01-S7] 回帰検証（`test_py2*_smoke`, `check_py2*_transpile`, `runtime_parity_check --case-root sample --all-samples`）を通し、8ターゲットのゴールデン整合を維持する。
