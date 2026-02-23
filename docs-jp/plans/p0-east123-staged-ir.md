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
- `type_id` 関連 lower を EAST3 命令化し、backend 側は命令写像に限定する
- `type_id` 以外の言語非依存意味論（boxing/unboxing, iterable, truthy/len/str, 主要 built-in lower）も EAST3 命令化へ段階移行する
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
7. `type_id` 判定 lower は EAST3 経由へ統一され、backend での C++ 直書き判定生成が原則なくなる。
8. `type_id` 以外の言語非依存意味論でも、backend/hook 側の直接実装が段階的に縮退し、EAST3 命令写像へ集約される。

確認コマンド（最低）:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_py2js_transpile.py`
- `python3 tools/check_py2ts_transpile.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`

サブタスク実行順（todo 同期）:
1. `P0-EAST123-01-S1`: ルートスキーマ（`east_stage`, `schema_version`, `meta.dispatch_mode`）の仕様統一。
2. `P0-EAST123-01-S2`: `dispatch mode` 適用点と後段再判断禁止の仕様固定。
3. `P0-EAST123-01-S3`: `spec-east` / `spec-type_id` / `spec-boxing` / `spec-iterable` / `spec-dev` の整合調整。
4. `P0-EAST123-01-S4`: `spec-east123` を上位仕様、`spec-linker` を下位仕様として確定し、参照順を明文化。
5. `P0-EAST123-02-S1`: `For` / `ForRange` の `ForCore + iter_plan` lower 実装。
6. `P0-EAST123-02-S2`: `Any/object` 境界命令の EAST3 lower 実装。
7. `P0-EAST123-02-S3`: `--object-dispatch-mode` の単一点適用実装。
8. `P0-EAST123-06-S1`: parser 直後 `EAST1` 出力 API 追加。
9. `P0-EAST123-06-S2`: `EAST1 -> EAST2` normalize pass 分離 + `load_east(...)` 互換維持。
10. `P0-EAST123-07-S1`: `type_id` 判定（`isinstance` / `issubclass` / subtype）の EAST3 命令化。
11. `P0-EAST123-07-S2`: backend 側 `type_id` 直書き判定生成の撤去（runtime API 写像へ統一）。
12. `P0-EAST123-08-S1`: IR-first 移行対象（boxing/unboxing, iterable, truthy/len/str, built-in lower）の優先度確定。
13. `P0-EAST123-08-S2`: 第1陣（boxing/unboxing, iterable, truthy/len/str）の EAST3 移行。
14. `P0-EAST123-08-S3`: 第2陣（主要 built-in lower）の EAST3 移行。
15. `P0-EAST123-03-S1`: C++ hooks / `py2cpp.py` の意味論実装経路棚卸し。
16. `P0-EAST123-03-S2`: EAST3 命令写像へ置換し、重複ロジックを撤去。
17. `P0-EAST123-05-S1`: hooks 分類と縮退メトリクス基線を確定。
18. `P0-EAST123-05-S2`: 意味論 hook 新規流入を防ぐ CI ルール追加。
19. `P0-EAST123-04-S1`: schema テスト整備（必須項目、`iter_plan` 形状、`dispatch_mode`）。
20. `P0-EAST123-04-S2`: lowering 契約テスト（`EAST2 -> EAST3`）整備。
21. `P0-EAST123-04-S3`: selfhost + クロスターゲット回帰導線へ統合。

決定ログ:
- 2026-02-23: 初版作成。`docs-jp/spec/spec-east123.md` を最優先事項として `todo` の `P0` へ昇格し、実装導入の作業枠を定義した。
- 2026-02-23: `EAST3` 導入効果を明示するため、`ID: P0-EAST123-05`（hooks 縮退の定量管理）を TODO/plan に追加した。
- 2026-02-23: 現行 `EAST2` が `EAST1 + EAST2` 相当である課題を反映し、`ID: P0-EAST123-06`（EAST1/EAST2 分離）を TODO/plan に追加した。
- 2026-02-23: `type_id` 関連 lower を backend 直書きではなく EAST3 命令化へ統一する方針を反映し、`ID: P0-EAST123-07` を TODO/plan に追加した。
- 2026-02-23: `type_id` に限らず IR-first を徹底するため、`ID: P0-EAST123-08`（言語非依存意味論の EAST3 命令化と C++ hooks 縮退）を TODO/plan に追加した。
- 2026-02-23: 実行単位を小さく保つため、`P0-EAST123-01-S1` を起点に `-S1/-S2/...` 形式で約20サブタスクへ再分割した。
- 2026-02-23: `spec-east123` を上位仕様、`spec-linker` を下位仕様として扱う順序を `P0-EAST123-01-S4` として TODO/plan へ追加した。
