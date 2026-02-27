# P3: microgpt 原本保全タスク再開

最終更新: 2026-02-26

関連 TODO:
- `docs-ja/todo/index.md` の `ID: P3-MSP-REVIVE-01`

背景:
- `P3-MSP-01`〜`P3-MSP-09` は一度 archive 側へ移管され、現行 TODO から見えなくなっている。
- ユーザー要望により、microgpt 関連タスクを未完了 TODO として再掲し、継続運用できる状態へ戻す。
- 既存履歴との衝突を避けるため、再開分は新規 ID で管理する。

目的:
- `materials/refs/microgpt/microgpt-20260222.py` を基準とした保全・回帰監視タスクを TODO 運用へ復帰する。

対象:
- microgpt 原本入力の transpile / compile / run 検証導線
- 回帰ステージ分類と再発検知手順
- `docs-ja` 側 TODO と文脈の同期

非対象:
- microgpt モデル品質や学習収束の改善
- microgpt 以外の大型ケース展開

受け入れ基準:
- microgpt 再開タスクが `docs-ja/todo/index.md` で追跡可能になっている。
- 原本入力に対する検証コマンドと期待結果が再確認されている。
- archive 履歴（旧ID）と再開タスク（新ID）の対応が文書で追える。

確認コマンド:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_microgpt_original_py2cpp_regression.py --expect-stage any-known`
- `python3 src/py2cpp.py materials/refs/microgpt/microgpt-20260222.py -o work/out/microgpt_revival.cpp`

決定ログ:
- 2026-02-26: ユーザー要望により、archive 移管済みの microgpt タスクを新規 ID で TODO に復活する方針を確定した。
- 2026-02-27: [ID: `P3-MSP-REVIVE-01-S1-01`] archive 側の旧 `P3-MSP-*` と再開タスクの対応表を作成し、再開スコープを「監視導線の再固定（実装再開ではない）」へ明確化した。
- 2026-02-27: [ID: `P3-MSP-REVIVE-01-S1-02`] 原本 `materials/refs/microgpt/microgpt-20260222.py` で `check_microgpt_original_py2cpp_regression.py --expect-stage F` を再実行し、現行期待値を `stage=F`（syntax-check 失敗、先頭シグネチャ: `Value::log()`）に固定した。`py2cpp.py ... -o work/out/microgpt_revival.cpp` も再生成確認した。

## 旧ID対応表（S1-01）

| 旧ID | 旧タスク要約（archive） | 再開側の扱い |
| --- | --- | --- |
| `P3-MSP-01` | 原本改変項目の責務再分類（parser/lower/runtime） | `P3-MSP-REVIVE-01-S1-01` で履歴参照対象として継承 |
| `P3-MSP-02` | 原本入力失敗要因 A〜F の再現・列挙 | `P3-MSP-REVIVE-01-S1-01` で分類軸を継承、`S2-02` のログ分類テンプレへ接続 |
| `P3-MSP-03` | 原本で transpile -> syntax-check 成功（`stage=SUCCESS`）まで前進 | `P3-MSP-REVIVE-01-S1-02` で現行期待値を再確認する対象 |
| `P3-MSP-04` | parser: 無注釈引数/inline method 受理拡張 | 旧実装完了履歴として参照のみ（再開で再実装しない） |
| `P3-MSP-05` | parser: top-level `for`/tuple代入/複数内包の受理拡張 | 旧実装完了履歴として参照のみ（再開で再実装しない） |
| `P3-MSP-06` | EAST/emitter: `range(...)` lower 整合 | 旧実装完了履歴として参照のみ（再開で再実装しない） |
| `P3-MSP-07` | EAST/emitter: `zip` 経由の型崩れ安定化 | 旧実装完了履歴として参照のみ（再開で再実装しない） |
| `P3-MSP-08` | runtime/std 互換差分（`open`/`index`/`shuffle`）整理 | 旧実装完了履歴として参照のみ（再開で再実装しない） |
| `P3-MSP-09` | 原本固定の回帰導線（`check_microgpt_original_py2cpp_regression.py`）整備 | `P3-MSP-REVIVE-01-S2-01` で現行運用基準へ見直す対象 |

再開スコープ（S1-01 決定）:
- 再開 ID は「原本入力の検証導線・期待値・障害分類テンプレート」を維持/更新する運用タスクに限定する。
- parser/lower/runtime の追加機能実装は、現時点では再開対象外（必要時は別IDで新規起票）とする。

## 分解

- [x] [ID: P3-MSP-REVIVE-01-S1-01] archive 側の `P3-MSP-*` 履歴と再開スコープの対応表を作成し、再開対象を明確化する。
- [x] [ID: P3-MSP-REVIVE-01-S1-02] 原本 `microgpt` 入力の transpile / syntax-check / 実行確認の現行手順を再確認し、期待値を固定する。
- [ ] [ID: P3-MSP-REVIVE-01-S2-01] `check_microgpt_original_py2cpp_regression.py` を運用基準へ合わせて見直し、再発検知条件を更新する。
- [ ] [ID: P3-MSP-REVIVE-01-S2-02] 失敗時に parser / lower / runtime の責務へ再分類できるログ運用テンプレートを整備する。
- [ ] [ID: P3-MSP-REVIVE-01-S3-01] 必要に応じて `microgpt` 用の追加 fixture / smoke を補強し、CI での監視を安定化する。
- [ ] [ID: P3-MSP-REVIVE-01-S3-02] 再開タスク完了時に archive へ戻すための移管条件（完了定義）を文書化する。
