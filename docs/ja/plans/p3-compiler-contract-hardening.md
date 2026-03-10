# P3: compiler contract を harden し、stage / pass / backend handoff を fail-closed にする

最終更新: 2026-03-11

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

## S1 棚卸し結果

### 既存 guard / validator の現状

| 系統 | 現在見ているもの | いま見ていないもの |
| --- | --- | --- |
| `tools/check_east_stage_boundary.py` | `east2.py` と `code_emitter.py` に対する import / call の stage 越境 | document shape、`type_expr` / `resolved_type` mirror、`source_span` / `repr`、helper metadata、pass / backend entry の semantic drift |
| `validate_raw_east3_doc(...)` | top-level `kind=Module`、`east_stage=3`、`body` list、`schema_version>=1`、`meta.dispatch_mode`、`meta.linked_program_v1` 禁止、`sync_type_expr_mirrors(...)` | 再帰的 node shape、node-level `source_span` / `repr` 必須性、helper metadata category、`dispatch_mode` の node/meta 整合、pass 後 drift |
| `validate_link_input_doc(...)` | manifest-level schema、`target` / `dispatch_mode` / `entry_modules` / `modules` の required field | 各 module の EAST3 payload shape、options payload の semantic 契約 |
| `validate_link_output_doc(...)` | manifest-level schema、helper module metadata の有無、`global` / `diagnostics` の top-level required key | `global` payload の内部 shape、embedded IR/EAST artifact の invariant、diagnostic item schema |
| `program_loader.py` | raw EAST3 load 時の `validate_raw_east3_doc(...)` | optimizer / linker / template specialization 後の再検証 |
| `backend_registry.py` / `backend_registry_static.py` | backend spec / option schema / typed carrier coercion | `lower_ir_typed` / `optimize_ir_typed` / `emit_source_typed` / `emit_module_typed` 入力 IR の contract。host lane は `suppress_exceptions=True` で backend-local error を空文字 fallback へ逃がしうる |

### blind spot の分類

- `node shape`
  - raw EAST3 は top-level `Module` だけ検証され、代表 node kind の必須 field / field type / child shape が未検証。
- `type_expr` / `resolved_type`
  - mirror sync はあるが、どの stage で何を canonical とみなすか、`unknown` をどこまで許すか、backend entry で何を必須とするかが未固定。
- `source_span` / `repr`
  - top-level 以外の node で required / optional が定義されておらず、欠落が backend crash や poor diagnostic として遅延検知される。
- `helper metadata`
  - runtime helper / linked helper / dispatch helper が埋める `meta` key 群に central validator がなく、producer/consumer の暗黙契約に依存している。
- `stage semantic drift`
  - `check_east_stage_boundary.py` は import/call policing に留まり、`east2 -> east3 -> linked output -> backend input` の semantic boundary drift を見ていない。
- `backend input`
  - representative backend の入口には compiler-contract validator がなく、malformed IR は backend-local exception または silent fallback で表面化する。

## S1 責務境界

- `schema validator`
  - 対象: raw EAST3 / linked input / linked output / backend input artifact の serialization/container shape。
  - 役割: required top-level field、enum domain、list/object shape、helper module top-level metadata、`type_expr` mirror の構文的一致を検証する。
  - 非役割: node-level semantic invariant、target-specific backend assumption。

- `invariant validator`
  - 対象: schema を通過した EAST3 / linked output / representative IR。
  - 役割: node kind ごとの必須 field、`source_span` / `repr` の保持契約、`dispatch_mode` / `resolved_type` / helper metadata の整合、pass 後に壊れてはいけない relationship を検証する。
  - 非役割: backend ごとの lowering detail や emit strategy。

- `backend input validator`
  - 対象: representative backend entry（まず C++）の直前。
  - 役割: backend が分岐に使う lowered kind、required metadata、target-local unsupported category を structured diagnostic に変える。
  - 非役割: raw doc coercion や carrier migration。そこは `P2` の責務。

### P1 / P2 との境界

- `P1-EAST-TYPEEXPR-01`
  - `TypeExpr` schema と mirror format の設計を持つ。P3 はその canonical contract を validator に落とすだけで、意味論自体は拡張しない。
- `P2-COMPILER-TYPED-BOUNDARY-01`
  - carrier / adapter seam を thin にする。P3 は seam を越えた後の document / IR contract を fail-closed にする。
- `P3`
  - 「何を受け取ってよいか」を machine-checkable に固定する。carrier の型上げや language surface 追加は行わない。

## S2 契約文書

- `docs/ja/spec/spec-dev.md` `1.2.2` を raw EAST3 / linked output / backend input の required field と許容欠落の正本に固定した。
- `docs/ja/spec/spec-dev.md` `1.2.3` を `type_expr` / `resolved_type` mirror、`dispatch_mode`、`source_span`、helper metadata の fail-closed mismatch policy の正本に固定した。
- `docs/ja/spec/spec-dev.md` `1.2.4` を schema / invariant / backend-input validator の diagnostic category 最小集合の正本に固定した。

## 分解

- [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-01] `check_east_stage_boundary` / `validate_raw_east3_doc` / backend entry guard の現状を棚卸しし、未検証の blind spot（node shape、`type_expr` / `resolved_type`、`source_span`、helper metadata）を分類する。
- [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-02] `P1-EAST-TYPEEXPR-01` / `P2-COMPILER-TYPED-BOUNDARY-01` と責務が衝突しないように、schema validator / invariant validator / backend input validator の責務境界を decision log に固定する。
- [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-01] `spec-dev` または等価設計文書に、EAST3 / linked output / backend input の必須 field、許容欠落、diagnostic category を追加する。
- [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-02] `type_expr` / `resolved_type` mirror、`dispatch_mode`、`source_span`、helper metadata の整合ルールと fail-closed 方針を固定する。
- [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-01] `toolchain/link/program_validator.py` と周辺に central validator primitive を追加し、raw EAST3 / linked output の coarse check を representative な node/meta invariant まで拡張した。
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
- 2026-03-11: `S1-01` 棚卸しでは、現行 guard が top-level schema と import/call policing に偏っており、node shape・`source_span`・helper metadata・backend input 契約が未検証であることを確認した。
- 2026-03-11: `S1-02` では責務境界を 3 層に固定した。schema validator は serialization/container shape、invariant validator は node/meta relationship、backend input validator は target-local fail-closed diagnostics を担当する。
- 2026-03-11: `S2-01` は `spec-dev` `1.2.2` と `1.2.4` を正本にし、raw EAST3 / linked output / backend input の required field、許容欠落、diagnostic category を固定した。
- 2026-03-11: `S2-02` は `spec-dev` `1.2.3` を正本にし、`type_expr` / `resolved_type` mirror、`dispatch_mode`、`source_span`、helper metadata の矛盾を fail-closed で扱うことを固定した。
- 2026-03-11: `S3-01` の最初の slice では `program_validator.py` に recursive raw EAST3 invariant helper を追加し、nested `meta.dispatch_mode` drift、`repr` type mismatch、`source_span` shape/reversed-range を central validator で止める形にした。
- 2026-03-11: 続く `S3-01` slice では linked output 側にも shape validator を追加し、`global.call_graph` などの object/list shape と `diagnostics.warnings/errors` の string item 契約を central validator で止める形にした。
- 2026-03-11: raw EAST3 representative node は synthetic provenance がない限り `source_span` 必須とし、linked output `diagnostics` では non-empty string に加えて `source_span` を持つ object item も許容する方針にした。
- 2026-03-11: 次の `S3-01` slice では raw EAST3 の top-level `body` item を object + `kind` + `source_span` 必須に寄せ、linked output `diagnostics` は non-empty string または `source_span` shape を持つ object のみ許可する方針に拡張した。
- 2026-03-11: さらに `S3-01` で linked output diagnostic object に `category` / `message` の non-empty string を必須化し、structured diagnostic 契約も central validator の責務に含めた。
- 2026-03-11: さらに `S3-01` で linked output `global.type_id_table` の int value、`call_graph` の `list[str]`、`sccs` の non-empty `list[list[str]]` を central validator で fail-closed にした。
- 2026-03-11: さらに `S3-01` で linked output diagnostic object の `category` を `spec-dev` `1.2.4` の最小集合に制限し、unknown category の流入も central validator で fail-closed にした。
- 2026-03-11: さらに `S3-01` で raw EAST3 の `meta.generated_by` を synthetic provenance 専用の non-empty string に制限し、missing `source_span` を許す escape hatch も中央 validator で型付きに固定した。
- 2026-03-11: `S3-01` はここで完了扱いにした。central primitive は raw EAST3 の body node / `kind` / `source_span` / nested `meta.dispatch_mode` と linked output の helper metadata / `global` shape / diagnostic object contract を見る状態まで到達したので、次は hook を差し込む `S3-02` へ進む。
- 2026-03-11: `S3-02` の representative hook は `toolchain/ir/east3.py` と `toolchain/link/global_optimizer.py` に先行投入した。raw EAST3 validator の strict `source_span` 契約は default に残しつつ、stage/linker hook では `require_source_spans=False` を使って synthetic node 混在でも `kind` / `body item shape` / `dispatch_mode` drift を fail-closed で止め、link-output 側は `validate_link_output_doc(...)` を return 前に必須化した。
