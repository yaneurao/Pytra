# TASK GROUP: TG-P0-EAST123

最終更新: 2026-02-23

関連 TODO:
- `docs-jp/todo.md` の `ID: P0-EAST123-*`

背景:
- 単一 EAST + backend hooks 運用では、意味論 lowering が backend 側へ漏れやすく、hooks が肥大化する。
- `Any/object` 境界、`dispatch mode`、iterable 契約の責務境界を backend 非依存で固定する必要がある。
- `docs-jp/spec/spec-east123.md` に三段構成（EAST1/EAST2/EAST3）の設計ドラフトを追加済みであり、これを実装計画へ落とし込む段階に入った。

目的:
- `spec-east123` を最優先仕様として実装へ接続し、EAST3 を意味論の単一正本にする。
- `EAST2 -> EAST3` で `--object-dispatch-mode` を一括適用し、後段再判断を禁止する。
- hooks を「構文差分の最終調整」に限定し、意味論実装を core lowering 側へ回収する。

対象:
- EAST ルートスキーマ（`east_stage`, `schema_version`, `meta.dispatch_mode`）の導入
- 現行 `EAST2`（`EAST1 + EAST2` 混在）の段階分離（`EAST1`: parser 直後、`EAST2`: normalize 専任）
- `ForCore` / `RuntimeIterForPlan` / `Any/object` 境界命令の段階導入
- backend の意味論再解釈禁止（hooks 責務境界の明確化）
- hooks 縮退の定量管理（意味論 hook の撤去数、構文差分 hook の残存数）
- schema/例外契約/回帰テストの整備

非対象:
- 全ノード一括置換
- 新規最適化器の全面導入
- 既存 backend の全面 rewrite

受け入れ基準:
1. `docs-jp/spec/spec-east123.md` の契約（stage/scheme/dispatch 固定点）と実装仕様の差分が解消されている。
2. `EAST3.meta.dispatch_mode` と `RuntimeIterForPlan.dispatch_mode` が導入され、後段で mode 再判定しない。
3. hooks での意味論変更（dispatch 再判断、boxing/iterable 再実装）が段階的に撤去される。
4. `EAST3` 契約を unit/codegen/selfhost 回帰で検証できる。
5. hooks の責務が「構文差分のみ」に収束し、意味論 hook の残存箇所が一覧化・縮退管理されている。
6. `EAST1` と `EAST2` の責務が分離され、`EAST1` から normalize なしの parser 出力を取得できる。

確認コマンド（最低）:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`

サブタスク実行順（todo 同期）:
1. `P0-EAST123-01`: `spec-east123` の契約を実装仕様（`spec-dev` / `spec-east`）へ確定反映する。
2. `P0-EAST123-02`: `EAST2 -> EAST3` 最小 lowering（`ForCore`, `RuntimeIterForPlan`, `Any/object` 境界命令）を導入する。
3. `P0-EAST123-03`: backend/hook 側の意味論再解釈経路を撤去し、構文差分専任に縮退する。
4. `P0-EAST123-04`: schema/例外契約/回帰導線を固定し、CI レベルの再発防止へ接続する。
5. `P0-EAST123-05`: hooks 実装を定量的に縮退し、意味論 hook を撤去して構文差分 hook のみへ収束させる。
6. `P0-EAST123-06`: 現行 `EAST2` を `EAST1`/`EAST2` に段階分離し、parser と normalize の責務境界を固定する。

決定ログ:
- 2026-02-23: 初版作成。`docs-jp/spec/spec-east123.md` を最優先事項として `todo` の `P0` へ昇格し、実装導入の作業枠を定義した。
- 2026-02-23: `EAST3` 導入効果を明示するため、`ID: P0-EAST123-05`（hooks 縮退の定量管理）を TODO/plan に追加した。
- 2026-02-23: 現行 `EAST2` が `EAST1 + EAST2` 相当である課題を反映し、`ID: P0-EAST123-06`（EAST1/EAST2 分離）を TODO/plan に追加した。
