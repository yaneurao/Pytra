# P3: compiler contract を harden し、stage / pass / backend handoff を fail-closed にする

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P3-COMPILER-CONTRACT-HARDENING-01`

背景:
- `P1-EAST-TYPEEXPR-01` と `P2-COMPILER-TYPED-BOUNDARY-01` で型意味論と carrier 境界を引き上げても、compiler 内部の handoff 契約が弱いままだと、崩れ方が backend 個別 crash や silent fallback として後段へ漏れる。
- 現状のガードは存在するが十分ではない。たとえば `tools/check_east_stage_boundary.py` は stage 越境 import / call を防ぐが、node shape や `meta` / `source_span` / type 契約までは見ていない。
- `toolchain/link/program_validator.py` の `validate_raw_east3_doc(...)` も、`kind` / `east_stage` / `schema_version` / `dispatch_mode` のような coarse 契約が中心で、node-level invariant や pass 後整合までは保証していない。
- その結果、optimizer / lowering / backend が暗黙に期待する field を局所的に仮定しがちで、仕様変更や selfhost 移行時に「どこで壊れたか」が遅く見つかる。
- Pytra を内部から改良していくなら、language feature を増やす前に「各 stage が何を受け取り、何を返してよいか」を machine-checkable にする必要がある。

目的:
- EAST3 / linked program / backend handoff の契約を validator と guard で明文化し、fail-closed にする。
- stage / pass / backend entry ごとに最低限守るべき invariant を固定し、silent fallback や未定義 shape の透過搬送を止める。
- crash したときに `source_span` / category / offending node kind が追える diagnostics 契約を強化する。
- P1/P2 で入る `TypeExpr` / typed carrier を、「入れたが誰も検証しない」状態にしない。

対象:
- `toolchain/ir/east3.py` / `toolchain/link/program_validator.py` / `toolchain/link/global_optimizer.py`
- `toolchain/ir/east2_to_east3_lowering.py` と representative EAST3 optimize pass
- `tools/check_east_stage_boundary.py` および compiler contract guard
- representative backend entry（まず C++）で受ける IR/EAST 契約
- diagnostics / regression test / selfhost 向け guard

非対象:
- `TypeExpr` 自体の schema 設計や nominal ADT 意味論の詳細設計
- compiler boundary typed 化そのもの
- user-facing な新 syntax / 新 language feature
- 全 backend の node contract を一度に完全網羅すること
- runtime helper の挙動変更を主目的にした作業

依存:
- `P1-EAST-TYPEEXPR-01` の `type_expr` 正本化方針が少なくとも決まっていること
- `P2-COMPILER-TYPED-BOUNDARY-01` の typed carrier / adapter seam 方針が決まっていること

## 必須ルール

推奨ではなく必須ルールとして扱う。

1. pass / backend / linker が受け取る document は、schema と invariant を validator で明示しなければならない。暗黙前提だけで運んではならない。
2. validator は missing field / 型不整合 / contradictory metadata を fail-closed で弾く。`unknown` や fallback へ黙って逃がしてはならない。
3. `source_span` / `repr` / diagnostic category は、保持できる node で無言欠落させてはならない。欠落を許すなら許容理由を契約に書く。
4. `TypeExpr` / `resolved_type` / `dispatch_mode` / helper metadata の ownership は中央 validator で定義し、各 backend が独自解釈してはならない。
5. stage boundary guard は import/call 監視だけでなく、semantic boundary も検証対象に含める。
6. 新しい node kind / meta key / helper protocol を導入するときは、validator と representative test を同時に追加する。
7. backend entry は「壊れた IR をそれっぽく出力する」のではなく、契約違反を明示エラーとして返す。

受け入れ基準:
- raw EAST3 / linked output / representative backend input に対する validator があり、node-level invariant の最低限を検証できる。
- `TypeExpr` / `resolved_type` / `source_span` / `meta` の代表的整合崩れが、backend crash ではなく structured diagnostic で止まる。
- `tools/check_east_stage_boundary.py` または等価 guard が stage semantic contract まで監視する。
- representative optimize/lowering/backend entry が validator hook を通し、invalid document を黙って通さない。
- 今後の P4/P5 で contract drift が再混入しにくい回帰テストが入る。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_east_stage_boundary.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/link -p 'test_program_validator.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east3*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## 実装順

順序は固定する。まず blind spot を見える化し、その後に central validator を入れ、最後に representative backend / selfhost gate へつなぐ。

1. 既存 validator / guard / blind spot の棚卸し
2. compiler contract と non-goal の固定
3. central validator primitive の導入
4. pass / linker / backend entry への組み込み
5. diagnostics / test / guard の強化
6. docs / archive / migration note の更新

## 分解

- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-01] `check_east_stage_boundary` / `validate_raw_east3_doc` / backend entry guard の現状を棚卸しし、未検証の blind spot（node shape、`type_expr` / `resolved_type`、`source_span`、helper metadata）を分類する。
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-02] `P1-EAST-TYPEEXPR-01` / `P2-COMPILER-TYPED-BOUNDARY-01` と責務が衝突しないように、schema validator / invariant validator / backend input validator の責務境界を decision log に固定する。
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-01] `spec-dev` または等価設計文書に、EAST3 / linked output / backend input の必須 field、許容欠落、diagnostic category を追加する。
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-02] `type_expr` / `resolved_type` mirror、`dispatch_mode`、`source_span`、helper metadata の整合ルールと fail-closed 方針を固定する。
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-01] `toolchain/link/program_validator.py` と周辺に central validator primitive を追加し、raw EAST3 / linked output の coarse check を node/meta invariant まで拡張する。
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-02] representative pass / lowering / linker entry に pre/post validation hook を導入し、invalid node の透過搬送を止める。
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S4-01] representative backend（まず C++）の入口で compiler contract validator を通し、backend-local crash や silent fallback を structured diagnostic へ置き換える。
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S4-02] `tools/check_east_stage_boundary.py` または後継 guard を拡張し、stage semantic contract の drift も検出できるようにする。
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S5-01] representative unit/selfhost 回帰を追加し、契約違反が expected failure として再現できるようにする。
- [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S5-02] docs / TODO / archive / migration note を更新し、今後 node/meta 追加時に validator 更新が必須であることを固定する。

## 期待 deliverable

### S1 の deliverable

- 現在の validator / guard が何を見ており、何を見ていないかの棚卸し
- 「schema」「invariant」「backend input check」の 3 層分離

### S2 の deliverable

- `TypeExpr` / `resolved_type` / `source_span` / `meta` の ownership ルール
- fail-closed にする mismatch 一覧

### S3 の deliverable

- central validator helper
- representative pass / linker / backend への hook

### S4 の deliverable

- backend crash ではなく diagnostic で止まる representative ケース
- semantic boundary guard の追加または強化

### S5 の deliverable

- 契約 drift を検知する regression
- 今後の feature 追加で validator 更新を忘れにくい docs / archive

決定ログ:
- 2026-03-09: ユーザー指示により、型基盤・typed carrier に続く内部改善として、compiler contract hardening を独立 P3 に切り出した。
- 2026-03-09: この P3 は language feature 追加ではなく、stage / pass / backend handoff の validator と fail-closed 契約を強化することを主眼に置く。
- 2026-03-09: `check_east_stage_boundary` のような境界 guard は残しつつ、import/call 監視だけでは足りないため semantic invariant まで広げる方針を固定した。
