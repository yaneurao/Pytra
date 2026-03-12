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

- [ ] [ID: P1-NONCPP-RUNTIME-LAYOUT-ROLLOUT-REMAINING-01] `go/java/kotlin/scala/swift/nim/js/ts/lua/ruby/php` runtime を P0 と同じ `generated/native` ownership model へ段階 rollout する（文脈: [p1-noncpp-runtime-layout-rollout-remaining.md](../plans/p1-noncpp-runtime-layout-rollout-remaining.md)）。進捗: `S1-01` で mapping table と hook/path baseline checker、`S1-02` で current/target file inventory・module bucket・canonical compare baseline coverage rule（`generated ∪ blocked = built_in/std/utils baseline`、compat/native overlap は許容）を固定し、`S2-01` で Wave A (`go/java/kotlin/scala/swift/nim`) の実 tree / runtime hook / guard / smoke path baseline を `generated/native` へ切替、`S2-02` で Java `std/json` stale lane を解消し、Nim `utils/*_helper` representative `Try/finally` lowering を入れて Wave A regeneration check を全通しし、`S2-03` で Wave A native residual を contract 化した上で Java `native/std/{math_impl,time_impl}` を generated 側へ吸収して削除し、`S3-01` を `js/ts` と `lua/ruby/php` の 2 bundle で完了して Wave B の runtime tree / shim / package export baseline を `generated/native` へ揃え、PHP public output bucket も `pytra/utils/*` へ正規化し、`S3-02` を `utils/png,gif` live regeneration、Lua decorator import ignore、Wave B regeneration green test、blocked compare lane classification、`js/ts/php std/time` compare lane、`js/ts std/math` compare lane、`php std/math` compare lane、そして Wave B generated compare end state（`js/ts/php = std/{math,time}+utils/{gif,png}`, `lua/ruby = helper-shaped generated artifacts only`）の contract 固定まで完了し、`S3-03` の first bundle で Wave B native residual の module/file baseline（`js/ts = built_in/py_runtime + std/{math,pathlib,time} substrate`, `php = built_in/py_runtime + std/time substrate`, `lua/ruby = built_in/py_runtime substrate only`）を contract 化し、next bundle で `js/ts std/pathlib` compare lane を live-generated 化して `pytra/std/pathlib` と JS runtime shim を generated 側へ切り替え、current bundle で `php std/pathlib` compare lane を live-generated 化して `pytra/std/pathlib.php` と PHP runtime packaging を generated 側へ切り替え、Wave B の `js/ts/php` blocked compare baseline を `built_in/* + std/json` まで縮退させた
- [ ] [ID: P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01] backend parity の secondary tier (`go/java/kt/scala/swift/nim`) に残る未対応 cell を live rollout task として実装で埋める（文脈: [p5-backend-parity-secondary-rollout.md](../plans/p5-backend-parity-secondary-rollout.md)）
- [ ] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01] backend parity の long-tail tier (`js/ts/lua/rb/php`) に残る未対応 cell を live rollout task として実装で埋める（文脈: [p6-backend-parity-longtail-rollout.md](../plans/p6-backend-parity-longtail-rollout.md)）
