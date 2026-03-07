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

### P0: pytra-cli C++ max最適化で linked-program build を使う

文脈: [docs/ja/plans/p0-pytra-cli-cpp-maxopt-linked-build.md](../plans/p0-pytra-cli-cpp-maxopt-linked-build.md)

1. [ ] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01] `pytra-cli --target cpp --build --codegen-opt 3` を linked-program optimizer 込みの max C++ route にし、sample parity で非退行を固定する。
2. [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S1-01] `pytra-cli` の `--codegen-opt` と `py2x/eastlink/ir2lang/py2cpp` の最適化段対応表を棚卸しし、`codegen-opt=3` の目標 semantics を固定する。
3. [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S1-02] `pytra-cli` max-opt C++ route の CLI 契約と sample parity gate を spec/plan に固定する。
4. [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S2-01] `pytra-cli --target cpp --build --codegen-opt 3` が linked-program optimizer を経由する build route を実装する。
5. [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S2-02] `pytra-cli --target cpp --codegen-opt 3` の transpile-only route も linked-program optimizer を使うよう揃える。
6. [x] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S3-01] representative CLI regression を追加し、`codegen-opt=3` の route 選択と manifest/build/run を固定する。
7. [ ] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S3-02] sample parity を回し、max-opt route でも C++ sample が green であることを確認する。
8. [ ] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S4-01] `pytra-cli` / how-to-use / 必要な docs に max-opt C++ route と sample parity 手順を反映する。
9. [ ] [ID: P0-PYTRACLI-CPP-MAXOPT-LINKED-01-S4-02] 完了結果を記録し、計画を archive へ移して閉じる。

### P1: 全target sample parity 完了

文脈: [docs/ja/plans/p1-all-target-sample-parity-rollout.md](../plans/p1-all-target-sample-parity-rollout.md)

1. [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01] parity target 全体について sample parity を `toolchain_missing` なしで完走できる状態にし、全target green の実行基準を固定する。
2. [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S1-01] parity target 全体の `runner_needs` と current `toolchain_missing` を棚卸しし、target ごとの不足 toolchain を matrix 化する。
3. [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S1-02] 「全target parity green」の done 条件、許容しない failure category、確認コマンドを spec/plan に固定する。
4. [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S2-01] compiled target 群（`rs/cs/go/java/kotlin/swift/scala`）の toolchain bootstrap 手順を整備し、`toolchain_missing` を解消する。
5. [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S2-02] scripting / mixed target 群（`ruby/lua/php/nim`）の toolchain bootstrap 手順を整備し、`toolchain_missing` を解消する。
6. [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S3-01] baseline target（`cpp/js/ts`）の sample parity を再確認し、他 target 修復中も `18/18` を維持する。
7. [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S3-02] compiled target 群（`rs/cs/go/java/kotlin/swift/scala`）の sample parity を green へ持ち上げる。
8. [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S3-03] scripting / mixed target 群（`ruby/lua/php/nim`）の sample parity を green へ持ち上げる。
9. [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S4-01] 全 target parity 一括実行の scripts / docs / how-to-use を整備し、再実行手順を固定する。
10. [ ] [ID: P1-ALLTARGET-SAMPLE-PARITY-01-S4-02] full parity 実行結果を記録し、計画を archive へ移して閉じる。

### P2: linked runtime helper 向け `@template` v1

文脈: [docs/ja/plans/p2-linked-runtime-helper-template-v1.md](../plans/p2-linked-runtime-helper-template-v1.md)

1. [ ] [ID: P2-LINKED-RUNTIME-TEMPLATE-01] linked runtime helper 向け generic surface の v1 として `@template("T")` を採用し、runtime helper 限定・explicit instantiation なしの前提を固定する。
2. [ ] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S1-01] `TypeVar` 案と `@template` 案の比較を閉じ、`@template("T")` を v1 canonical syntax として決定する。
3. [ ] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S1-02] runtime helper 限定・top-level function 限定・explicit instantiation なし、という v1 スコープを spec/plan に固定する。
4. [ ] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S2-01] parser / EAST / linked metadata の canonical shape（例: `meta.template_v1`）を設計する。
5. [ ] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S2-02] validation ルール（適用位置、パラメータ名、重複、runtime helper 限定）を設計する。
6. [ ] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S3-01] future `@instantiate(...)` と両立する surface 拡張方針を記録する。
7. [ ] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S3-02] specialization collector / monomorphization の後続計画との接続点を整理する。
8. [ ] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S4-01] docs / TODO / 関連 plan を同期して、generic v1 の前提を固定する。
9. [ ] [ID: P2-LINKED-RUNTIME-TEMPLATE-01-S4-02] 完了時に archive へ移せる状態まで決定ログと受け入れ基準を整える。
