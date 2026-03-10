# P5: nominal ADT の言語機能としての full rollout

最終更新: 2026-03-11

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

- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-01] nominal ADT の language surface（宣言、constructor、variant access、`match`）の候補を棚卸しし、selfhost-safe な段階導入案を決める。
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-02] `P1-EAST-TYPEEXPR-01` と責務が衝突しないように、型基盤・narrowing 基盤・full language feature の境界を decision log に固定する。
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-01] `spec-east` / `spec-user` / `spec-dev` に nominal ADT declaration surface、pattern node、`match` node、diagnostic 契約を追加する。
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-02] exhaustiveness / duplicate pattern / unreachable branch の静的検証方針と error category を固定する。
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-01] frontend と selfhost parser を更新し、representative nominal ADT syntax を受理できるようにする。
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-02] EAST/EAST3 に ADT constructor、variant test、variant projection、`match` lowering を導入する。
- [x] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-01] built-in `JsonValue` lane と user-defined nominal ADT lane が同じ IR category に乗ることを representative test で確認する。
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

### S1-01 候補棚卸し

- 候補A: 既存 `class` + 単一継承 + `@dataclass` を使い、sealed base と top-level variant class を並べる
  - 例: `@sealed class Result: ...`, `@dataclass class Ok(Result): value: T`, `@dataclass class Err(Result): error: E`
  - 長所: 既存 parser/selfhost が受理できる surface を最大限流用できる
  - 短所: `Result.Ok(...)` のような namespace 付き sugar は別途必要
- 候補B: base class の内側に variant class をネストする
  - 例: `class Result: @dataclass class Ok(Result): ...`
  - 長所: family のまとまりは見やすい
  - 短所: selfhost / symbol 解決 / backend name mangling の影響が大きい
- 候補C: `enum` 風または `adt` 専用 block を新設する
  - 例: `adt Result: Ok(value: T); Err(error: E)`
  - 長所: ADT としての意図は最も明瞭
  - 短所: parser / selfhost / formatter / diagnostics を一度に増やす必要があり、初手には重い
- 候補D: `match` も含めて新しい expression-first surface を一気に入れる
  - 例: `match expr { Ok(v) => ... }`
  - 長所: ADT の体験は高い
  - 短所: statement/expr 両系統の grammar と lowering を同時に抱え、selfhost-safe ではない

### S1-01 決定

- canonical な初期 declaration surface は候補Aとする
  - sealed family は既存 `class` を使って宣言する
  - variant は top-level class として宣言し、base nominal ADT を単一継承する
  - payload を持つ variant は既存 `@dataclass` surface を使う
- canonical な初期 constructor surface は通常の class call とする
  - 例: `Ok(value=1)` または positional constructor
  - `Result.Ok(...)` / factory DSL / macro 的 sugar は後段に回す
- canonical な初期 variant access surface は `isinstance` + field access とする
  - 例: `if isinstance(x, Ok): return x.value`
  - `JsonValue.as_*` lane と競合する general dynamic helper は増やさない
- `match` は statement-first で段階導入し、初期 surface には含めない
  - Stage A では `isinstance` narrowing + field access を正本とする
  - Stage B で Python-like `match/case` statement を representative surface として導入する
  - Stage C で `match` expression、guard pattern、nested pattern を検討する
- variant namespace rule は v1 では「top-level variant 名が canonical」で固定する
  - `Result.Ok` のような namespace sugar や nested variant declaration は Stage C 以降の検討対象とする

### selfhost-safe な段階導入案

1. Stage A: 既存 `class` / `@dataclass` / `isinstance` だけで nominal ADT family を宣言・利用できるようにする
2. Stage B: 同じ variant class 群を対象に `match/case` statement を導入する
3. Stage C: `match` expression、guard、nested pattern、namespace sugar を追加する
4. Stage D: `adt` block や `Result.Ok` のような concise sugar を必要なら別 surface として検討する

### S1-01 完了条件メモ

- parser/selfhost 追加前の canonical surface は「既存 class/dataclass の再利用」に限定する
- `match` は language feature の目標には含めるが、statement-first の後段導入とする
- new syntax を初手で増やす案（nested variant / `adt` block / expression-first match）は採用しない

### S1-02 責務境界

- P1 が持つもの: 型基盤
  - `TypeExpr` schema
  - `OptionalType` / `UnionType(union_mode=dynamic)` / `NominalAdtType` の分類
  - `type_expr` と `resolved_type` mirror の主従
  - `JsonValue` を nominal closed ADT lane として扱う IR 契約
- P1 が持つもの: narrowing 基盤
  - `isinstance` / decode helper / variant test 相当の generic narrowing semantics
  - EAST2 -> EAST3 における narrowing / decode / type-predicate metadata
  - validator が見る `semantic_tag` / nominal 名 / fail-closed mismatch 契約
- P5 が持つもの: full language feature
  - nominal ADT declaration surface
  - constructor / variant access / destructuring / pattern / `match`
  - exhaustiveness / duplicate pattern / unreachable branch の user-facing diagnostic
  - selfhost parser が読む ADT / pattern / `match` syntax
  - representative backend が user-defined nominal ADT を end-to-end で通す surface 契約

### S1-02 handoff ルール

1. `TypeExpr` kind、union lane、nominal ADT category、generic narrowing metadata を変える変更は P1 側の責務とする。
2. user code がどう書くか、parser が何を受理するか、`match` / pattern / constructor の surface をどう見せるかは P5 側の責務とする。
3. Stage A の `class` / `@dataclass` / `isinstance` bridge は P5 の representative surface に含めてよいが、`isinstance` 自体の generic type-predicate semantics を P5 で再定義してはならない。
4. built-in `JsonValue.as_*` / `get_*` の decode-first semantics は P1 が固定した IR/narrowing 契約を正とし、P5 はそれを user-defined ADT syntax と同じ IR category に寄せる段階だけを扱う。
5. P5 が新しい source surface を導入するときに新 `TypeExpr` kind や新 generic narrowing lane が必要になった場合、その基盤追加は P1 後継の型基盤タスクへ戻し、P5 だけで抱え込まない。

### representative scope の例

- built-in: `JsonValue`
- user-defined: 2〜3 variant の closed ADT 1個
- pattern: literal-free variant match + payload bind

決定ログ:
- 2026-03-09: ユーザー指示により、nominal ADT の full language feature rollout は `P1-EAST-TYPEEXPR-01` の基盤整備とは分離し、最終段の `P5` として管理する方針を追加した。
- 2026-03-09: この P5 は user-defined ADT syntax、constructor、`match`、exhaustiveness check、multi-backend rollout を対象とし、型基盤そのものは扱わないと固定した。
- 2026-03-09: built-in `JsonValue` と user-defined ADT を別系統 feature にしない。IR/lowering/backend contract は最終的に同一 category へ収束させる方針を固定した。
- 2026-03-11: `S1-01` として language surface 候補を棚卸しし、initial rollout は既存 `class` + 単一継承 + `@dataclass` + `isinstance` を canonical surface にする方針を固定した。
- 2026-03-11: `match` は language goal に含めるが、selfhost-safe な初期導入には含めず、statement-first の Stage B として後段導入に回す方針を固定した。
- 2026-03-11: `Result.Ok` や `adt` block のような concise sugar は canonical v1 では採用せず、parser/selfhost/backend が安定した後段で再評価する方針を固定した。
- 2026-03-11: `S1-02` として、`TypeExpr` schema・union lane・nominal ADT category・generic narrowing metadata は P1 の責務、declaration/constructor/pattern/`match` の source surface と user-facing diagnostic は P5 の責務と固定した。
- 2026-03-11: Stage A の `class` / `@dataclass` / `isinstance` bridge は P5 の representative surface に含めるが、`isinstance` 自体の generic type-predicate semantics と `JsonValue` decode-first IR 契約は P1 の成果物を再利用し、P5 で再定義しない方針を固定した。
- 2026-03-11: `S2-01` として、`spec-user` に Stage A の `@sealed` family / top-level variant / `isinstance` access surface を追加し、`spec-east` に `ClassDef.meta.nominal_adt_v1` と `Match` / `MatchCase` / `VariantPattern` / `PatternBind` / `PatternWildcard` schema を追加し、`spec-dev` に nominal ADT / `match` 導入時の fail-closed diagnostic 契約を固定した。
- 2026-03-11: `S2-02` として、closed nominal ADT family に対する `Match` は exhaustive 必須、duplicate pattern / unreachable branch は `semantic_conflict` で fail-closed とし、coverage summary は `Match.meta.match_analysis_v1` で保持する方針を固定した。
- 2026-03-11: `S3-01` の representative parser として、selfhost parser は `@sealed` family、same-module に先行定義された family からの variant、payload variant の `@dataclass` 必須、`ClassDef.meta.nominal_adt_v1` 付与までを受理する方針で進めることにした。
- 2026-03-11: `S3-01` では imported family や family より前に定義された variant までは扱わず、まず same-module / family-first の representative case を正本にすることにした。
- 2026-03-11: `S3-01` を閉じ、representative parser case は `@sealed` family、same-module family-first variant、payload variant の `@dataclass` 必須、`ClassDef.meta.nominal_adt_v1` 生成、misuse の fail-closed 診断まで通す方針で固定した。
- 2026-03-11: `S3-02` では constructor / family-variant test に加えて、variant-typed receiver からの field access を `NominalAdtProjection` metadata 付き `Attribute` として固定し、branch-local narrowing projection と `match` lowering は後続 slice に分離した。
- 2026-03-11: `S3-02` の第一段として、same-module nominal ADT family/variant 宣言表を参照し、user-defined variant constructor call を `NominalAdtCtorCall`、`isinstance(..., Variant/Family)` を `nominal_adt_test_v1` / `narrowing_lane_v1.predicate_category=nominal_adt` 付き representative lane へ seeded する方針を固定した。
- 2026-03-11: `S3-02` では variant projection / `match` lowering まで一気に進めず、constructor と variant test の representative metadata lane を先に test で固定してから次段へ進むことにした。
- 2026-03-11: `S3-02` を閉じ、representative nominal ADT `Match` は EAST3 で `NominalAdtMatch` metadata、`VariantPattern` は `NominalAdtVariantPattern` metadata、payload bind は field-type 付き `PatternBind` metadata を持つ方針で固定した。
- 2026-03-11: `S4-01` を閉じ、built-in `JsonValue` decode lane の `receiver_type.category` と user-defined nominal ADT `Match` subject の `subject_type.category` は、ともに `nominal_adt` を使う representative test で固定した。
