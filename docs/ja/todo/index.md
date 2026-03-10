# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-11

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


### P3: compiler contract を harden し、stage / pass / backend handoff を fail-closed にする

文脈: [docs/ja/plans/p3-compiler-contract-hardening.md](../plans/p3-compiler-contract-hardening.md)

1. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01] compiler contract を harden し、stage / pass / backend handoff を fail-closed にする。
2. [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-01] `check_east_stage_boundary` / `validate_raw_east3_doc` / backend entry guard の現状を棚卸しし、未検証の blind spot（node shape、`type_expr` / `resolved_type`、`source_span`、helper metadata）を分類する。
3. [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-02] `P1-EAST-TYPEEXPR-01` / `P2-COMPILER-TYPED-BOUNDARY-01` と責務が衝突しないように、schema validator / invariant validator / backend input validator の責務境界を decision log に固定する。
4. [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-01] `spec-dev` `1.2.2` / `1.2.4` に raw EAST3 / linked output / backend input の required field、許容欠落、diagnostic category を固定した。
5. [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-02] `spec-dev` `1.2.3` に `type_expr` / `resolved_type` mirror、`dispatch_mode`、`source_span`、helper metadata の fail-closed policy を固定した。
6. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-01] `toolchain/link/program_validator.py` と周辺に central validator primitive を追加し、raw EAST3 / linked output の coarse check を node/meta invariant まで拡張する。
7. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-02] representative pass / lowering / linker entry に pre/post validation hook を導入し、invalid node の透過搬送を止める。
8. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S4-01] representative backend（まず C++）の入口で compiler contract validator を通し、backend-local crash や silent fallback を structured diagnostic へ置き換える。
9. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S4-02] `tools/check_east_stage_boundary.py` または後継 guard を拡張し、stage semantic contract の drift も検出できるようにする。
10. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S5-01] representative unit/selfhost 回帰を追加し、契約違反が expected failure として再現できるようにする。
11. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S5-02] docs / TODO / archive / migration note を更新し、今後 node/meta 追加時に validator 更新が必須であることを固定する。

### P4: backend_registry の正本化と selfhost parity gate の強化

文脈: [docs/ja/plans/p4-backend-registry-selfhost-parity-hardening.md](../plans/p4-backend-registry-selfhost-parity-hardening.md)

1. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01] backend_registry の正本化と selfhost parity gate の強化を行う。
2. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-01] `backend_registry.py` と `backend_registry_static.py` の重複 surface（backend spec、runtime copy、writer rule、option schema、direct-route behavior）を棚卸しし、intentional difference と drift 候補を分類する。
3. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-02] `build_selfhost` / `stage2` / `verify_selfhost_end_to_end` / `multilang selfhost` の現状 gate と blind spot を整理し、known block / regression の分類方針を decision log に固定する。
4. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-01] backend capability / runtime copy / option schema / writer metadata の canonical SoT を定義し、host/static の両方がそこから構成される形へ寄せる。
5. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-02] intentional difference を許す境界（例: host-only lazy import、selfhost-only direct route）と、その diagnostics 契約を固定する。
6. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-01] host registry / static registry を shared metadata または generator 経由へ寄せ、手書き重複を縮退する。
7. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-02] registry drift guard または diff test を追加し、片側だけ更新された backend surface を fail-fast で検知する。
8. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-01] stage1 / stage2 / direct e2e / multilang selfhost の representative parity suite を整理し、failure category と summary 出力を統一する。
9. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-02] unsupported / preview / known block / regression の診断カテゴリを registry と parity report で揃え、expected failure を明示管理できるようにする。
10. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-01] docs / plan report / archive を更新し、backend readiness・known block・gate 実行手順を追跡可能にする。
11. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-02] representative internal change に対して host lane と selfhost lane が同じ contract で検証されることを確認し、再流入 guard を固定する。

### P5: nominal ADT の言語機能としての full rollout

文脈: [docs/ja/plans/p5-nominal-adt-language-rollout.md](../plans/p5-nominal-adt-language-rollout.md)

1. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01] nominal ADT の言語機能としての full rollout を行う。
2. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-01] nominal ADT の language surface（宣言、constructor、variant access、`match`）の候補を棚卸しし、selfhost-safe な段階導入案を決める。
3. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-02] `P1-EAST-TYPEEXPR-01` と責務が衝突しないように、型基盤・narrowing 基盤・full language feature の境界を decision log に固定する。
4. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-01] `spec-east` / `spec-user` / `spec-dev` に nominal ADT declaration surface、pattern node、`match` node、diagnostic 契約を追加する。
5. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-02] exhaustiveness / duplicate pattern / unreachable branch の静的検証方針と error category を固定する。
6. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-01] frontend と selfhost parser を更新し、representative nominal ADT syntax を受理できるようにする。
7. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-02] EAST/EAST3 に ADT constructor、variant test、variant projection、`match` lowering を導入する。
8. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-01] built-in `JsonValue` lane と user-defined nominal ADT lane が同じ IR category に乗ることを representative test で確認する。
9. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-02] representative backend（まず C++）で constructor / variant check / destructuring / `match` の最小実装を入れ、silent fallback を禁止する。
10. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-01] 他 backend への rollout 順と fail-closed policy を整理し、未対応 target の診断を固定する。
11. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-02] selfhost / docs / archive / migration note を更新し、正式言語機能としての nominal ADT rollout を閉じる。
