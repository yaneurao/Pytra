# P5: nominal ADT の言語機能としての full rollout

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P5-NOMINAL-ADT-ROLLOUT-01`

背景:
- `JsonValue` のような closed nominal ADT を健全に扱うには、まず EAST/IR 側で `TypeExpr`、union 分類、narrowing 契約を固める必要がある。
- その基盤は `P1-EAST-TYPEEXPR-01` の責務であり、ここを飛ばして nominal ADT の user-facing language feature を入れると、backend ごとの特例実装と `object` fallback が再増殖する。
- 一方で、長期的には `JsonValue` のような組み込み nominal ADT だけでなく、ユーザー定義の closed ADT、constructor、variant 分解、`match`、exhaustiveness check まで含めた言語機能化が必要になる。
- これらは型基盤・selfhost・代表 backend 実装・runtime 契約が揃ってから進めるべきであり、現在の未完了 P0/P1/P2 より後ろに置くのが妥当である。

目的:
- nominal ADT を Pytra の正式な言語機能として導入する。
- ユーザー定義 ADT、constructor、variant 判定/分解、`match`、exhaustiveness check を、backend 特例ではなく言語共通契約として定義する。
- `JsonValue` のような built-in nominal ADT と、将来のユーザー定義 ADT が同じ IR / lowering / backend contract に乗る状態にする。

対象:
- nominal ADT の source syntax または等価な declaration surface
- constructor / variant / destructuring / `match`
- exhaustiveness / unreachable branch / duplicate pattern の静的検証
- EAST/EAST3 上の ADT node / pattern node / narrowing node
- representative backend の codegen / runtime contract
- selfhost parser / frontend / docs / tests

非対象:
- `P1-EAST-TYPEEXPR-01` が扱う型基盤そのもの
- `P2-COMPILER-TYPED-BOUNDARY-01` が扱う compiler internal carrier 整理
- 即時の全 target 完全対応
- Python source と 100% 同一の ADT/match syntax を最初から要求すること
- 例外・dynamic cast・reflection を使った場当たり救済

依存関係:
- `P1-EAST-TYPEEXPR-01` 完了または少なくとも `TypeExpr` / nominal ADT / narrowing 契約が確定していること
- `P2-COMPILER-TYPED-BOUNDARY-01` で compiler internal の object carrier 整理方針が固まっていること
- representative backend で `JsonValue` nominal lane が動いていること

## 必須ルール

1. nominal ADT は `object` fallback の sugar にしてはならない。closed variant set を持つ型として IR で識別できることを必須にする。
2. ADT constructor / variant access / `match` は backend 直書き special case ではなく、frontend/lowering/IR を正本にする。
3. exhaustiveness check を後回しにしてもよいが、少なくとも「未網羅である」「duplicate pattern である」「到達不能である」を表せる IR/diagnostic 設計を先に決める。
4. built-in nominal ADT（例: `JsonValue`）と user-defined nominal ADT を別系統にしない。同じ node/category と lowering 契約へ収束させる。
5. backend 未対応の ADT/pattern は silent fallback ではなく fail-closed を正本にする。
6. selfhost parser が読めない syntax を先に正規 syntax として仕様化してはならない。必要なら段階導入 surface を設ける。

受け入れ基準:
- nominal ADT の宣言 surface、constructor、variant access、`match`、静的検証方針が docs/spec 上で固定される。
- built-in ADT と user-defined ADT が同じ IR category で扱える。
- representative backend で constructor / variant check / destructuring / `match` の最小 end-to-end が通る。
- selfhost path でも representative ADT case を処理できる。
- backend 未対応時は明示エラーへ寄り、`object` fallback へ逃げない。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_*adt*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_*adt*.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## 実装順

1. language surface と非対象の固定
2. ADT / pattern / match schema の固定
3. frontend/selfhost parser の対応
4. EAST2 -> EAST3 lowering と静的検証
5. representative backend 実装
6. built-in ADT と user-defined ADT の統合確認
7. multi-backend rollout / docs / archive

## 分解

- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-01] nominal ADT の language surface（宣言、constructor、variant access、`match`）の候補を棚卸しし、selfhost-safe な段階導入案を決める。
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-02] `P1-EAST-TYPEEXPR-01` と責務が衝突しないように、型基盤・narrowing 基盤・full language feature の境界を decision log に固定する。
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-01] `spec-east` / `spec-user` / `spec-dev` に nominal ADT declaration surface、pattern node、`match` node、diagnostic 契約を追加する。
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-02] exhaustiveness / duplicate pattern / unreachable branch の静的検証方針と error category を固定する。
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-01] frontend と selfhost parser を更新し、representative nominal ADT syntax を受理できるようにする。
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-02] EAST/EAST3 に ADT constructor、variant test、variant projection、`match` lowering を導入する。
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-01] built-in `JsonValue` lane と user-defined nominal ADT lane が同じ IR category に乗ることを representative test で確認する。
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-02] representative backend（まず C++）で constructor / variant check / destructuring / `match` の最小実装を入れ、silent fallback を禁止する。
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-01] 他 backend への rollout 順と fail-closed policy を整理し、未対応 target の診断を固定する。
- [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-02] selfhost / docs / archive / migration note を更新し、正式言語機能としての nominal ADT rollout を閉じる。

## 実装者向けメモ

### 先にやってはいけないこと

- `JsonValue` 専用の ad-hoc syntax を language feature として固定すること
- C++ だけ通る ADT surface を先に canonical 化すること
- exhaustiveness を未定義のまま `match` を backend special case で増やすこと

### 先に決めるべきこと

- constructor 形式
- variant 名の namespace ルール
- `match` が expression か statement か、または両方か
- wildcard / guard / nested pattern の初期範囲

### representative scope の例

- built-in: `JsonValue`
- user-defined: 2〜3 variant の closed ADT 1個
- pattern: literal-free variant match + payload bind

決定ログ:
- 2026-03-09: ユーザー指示により、nominal ADT の full language feature rollout は `P1-EAST-TYPEEXPR-01` の基盤整備とは分離し、最終段の `P5` として管理する方針を追加した。
- 2026-03-09: この P5 は user-defined ADT syntax、constructor、`match`、exhaustiveness check、multi-backend rollout を対象とし、型基盤そのものは扱わないと固定した。
- 2026-03-09: built-in `JsonValue` と user-defined ADT を別系統 feature にしない。IR/lowering/backend contract は最終的に同一 category へ収束させる方針を固定した。
