# TODO（未完了）

> `docs/ja/` が正（source of truth）です。`docs/en/` はその翻訳です。

<a href="../../en/todo/index.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

最終更新: 2026-03-10

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

### P2: compiler boundary を typed 化し、internal object carrier と `make_object` 依存を後退させる

文脈: [docs/ja/plans/p2-compiler-typed-boundary.md](../plans/p2-compiler-typed-boundary.md)

1. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01] compiler boundary を typed 化し、internal object carrier と `make_object` 依存を後退させる。
2. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01] `transpile_cli` / `backend_registry_static` / selfhost parser / generated compiler runtime に残る `dict[str, object]` / `list[object]` / `make_object` / `py_to` usage を棚卸しし、`compiler_internal` / `json_adapter` / `extern_hook` / `legacy_bridge` に分類する。
3. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02] `spec-dev` / `spec-runtime` / `spec-boxing` と矛盾しない typed boundary 契約と non-goal を decision log に固定する。
4. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-01] compiler root payload（EAST document / backend spec / layer option / emit request/result）の typed carrier 仕様を決める。
5. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-02] Python 正本へ typed carrier と薄い legacy adapter を導入する。
6. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-03] C++ selfhost/native compiler interface へ typed carrier mirror または typed wrapper API を導入し、raw `dict<str, object>` exchange を縮小する。
7. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] selfhost parser / EAST builder の node 構築を typed constructor / builder helper へ寄せ、`dict<str, object>{{...}}` 直組み立てを段階縮退する。
8. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] generated compiler / selfhost runtime に残る `make_object` usage を `serialization/export seam` 専用まで後退させる。
9. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-A] `S3-02` の完了条件を再定義し、`TODO` / plan の進捗メモを cluster 単位へ圧縮する。
10. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-B] `core.py` の postfix/suffix parser cluster を分割し、`call` / `attr` / `subscript` を専用 module へ移す。
11. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-C] `core.py` の call annotation cluster を分割し、`named-call` / `attr-call` / `callee-call` を専用 module へ移す。
12. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-D] `call-arg` / `suffix tail` / `subscript tail` に残る helper 抽出を 5-10 個単位の bundle で消化し、1 helper = 1 commit を止める。
13. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-E] generated/selfhost residual guard と export seam を再基準化し、`make_object` を `serialization/export seam` 専用まで後退させて `S3-02` を閉じる。
14. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] JSON・extern/hook・未型付け入力の dynamic carrier を compiler typed model から切り離し、`JsonValue` / explicit adapter に隔離する。
15. [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-02] `make_object` / `py_to` / `obj_to_*` の残存 usage に分類ラベルを与え、未分類・再流入を弾く guard を追加する。
16. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-01] selfhost build / diff / prepare / bridge 回帰を更新し、typed boundary 変更後の非退行を固定する。
17. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-02] docs / TODO / archive を更新し、残る `make_object` が「user boundary 専用」か「明示 adapter 専用」かを記録して閉じる。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02] `S1-S2` では object carrier の分類、typed boundary の non-goal、typed carrier の field 契約、host/static/native wrapper を固定し、公開 raw dict surface を thin legacy adapter へ後退させた。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] checked-in node 構築は `_sh_make_*` builder helper にほぼ揃い、module root / import / expr / stmt / comprehension / f-string / trivia / span carrier は source-of-truth 側で helper 契約化された。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] host/static/native の typed export seam は `typed_boundary.py` 中心へ集約され、selfhost entrypoint も direct typed path へ寄った。version gate と entrypoint contract で再流入を監視している。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] generated/selfhost residual guard は module root / import / expr / stmt / literal / comprehension / f-string lane まで広がっており、source-of-truth 側でも raw inline `kind` や open-coded dict residual を fail-fast で監視している。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] `call` / `attr` / `subscript` / `call-arg` 周辺の helper 化はかなり進んだが、`core.py` と `test_east_core.py` が肥大化し、helper 1 個ごとの commit と進捗メモでは全体前進量に対して粒度が細かすぎる状態になった。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] 以後の `S3-02` は `S3-02-B` から `S3-02-E` の cluster 単位で進め、`TODO` には cluster 要約のみを残す。helper 単位の微細履歴は plan の decision log と git history に委ねる。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-B] postfix/suffix parser cluster は `core_expr_call_suffix.py` と `core_expr_attr_subscript_suffix.py` へ分割し、`core.py` 側は mixin import と postfix dispatch orchestration を中心に持つ形へ整理した。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-C] `call_expr` / `callee_call` / `named-call` / `attr-call` の annotation entrypoint は `core_expr_call_annotation.py` へ移り、`core.py` 側は shared helper と lower-level apply に縮んだ。残りの微細 helper 抽出は `S3-02-D` で扱う。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-D] `call-arg` は `core_expr_call_args.py`、`call suffix` は `core_expr_call_suffix.py`、`attr/subscript suffix` は `core_expr_attr_subscript_suffix.py` に寄り、残る helper 抽出も bundle 単位へ整理した。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-E] generated selfhost core の residual `make_object` guard は `export_seam` と `parser_residual` を別 scope で固定し、さらに parser residual を `expr_parser` / `stmt_parser` / `lookup` bucket へ分けた。bucket の和集合が parser residual と一致し、export seam と交差しないことも test で固定した。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-E] source-of-truth の compiler lane と native wrapper では `make_object` が export seam 以外から退き、generated selfhost core も `export_seam=to_payload` と explicit `parser_residual` guard へ再基準化できたため、`S3-02` は完了として閉じ、残る分類強化は `S4-02` へ送る。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] dynamic carrier の現状は `JsonValue` raw carrier、extern-marked stdlib surface、`typed_boundary.py` の runtime hook seam、compiler-root JSON load に集約されることを contract test で固定した。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] `typed_boundary.py` の runtime hook lane は `RuntimeHookAdapter` へ寄せ、typed spec から raw callable を直接持たずに export/apply seam で扱う形へ整理した。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] native compiler-root JSON load も `_unwrap_compiler_root_json_doc()` / `_coerce_compiler_root_json_doc()` に集約し、raw `JsonObj` unwrap を named adapter の内側へ閉じた。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] toolchain 側の JSON load seam も `toolchain.json_adapters` に集約し、`frontends/transpile_cli` / `ir/east_io` / `link_*` / `runtime_symbol_index` から raw `json.loads_obj(...).raw` を退けた。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] Python compiler lane の `loads_obj(...).raw` は `toolchain/json_adapters.py` の `load_json_object_doc()` / `export_json_object_dict()` / `unwrap_east_root_json_doc()` に寄せ、frontends/link/ir/runtime-index で raw `JsonObj` unwrap を共通 seam に閉じた。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] CLI root loader の `py2x` / `ir2lang` も `load_json_object_doc_or_none()` を通るようにし、toolchain 外周の JSON root 読み込みを同じ adapter seam に揃えた。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] `extern_var_v1` は `AmbientExternBinding` carrier を通るようにし、ambient extern validation が raw `dict[str, str]` ではなく explicit adapter seam だけを見る形へ寄せた。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] `ir2lang` の EAST JSON unwrap も `unwrap_east_root_json_doc()` / `export_json_object_dict()` に寄せ、outer CLI lane に残っていた `.raw` 直参照を toolchain adapter seam の外へ出した。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] 空 `JsonObj` fallback と `JsonValue -> JsonObj` 既定変換も `toolchain.json_adapters` に集約し、`py2x` / `ir2lang` / `program_validator` から direct `json.JsonObj({})` を退けた。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] `program_validator.py` に残っていた `JsonObj/JsonArr/JsonValue` raw access も `toolchain.json_adapters` に寄せ、validator 本体は object/array/value helper 経由でのみ dynamic carrier を扱うようにした。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] `program_loader` の in-memory module doc 受理も `coerce_json_object_dict()` に統一し、`typed_boundary.py` の compiler-root raw/meta 参照は helper 内へ閉じた。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] これで dynamic carrier は `toolchain.json_adapters`・`RuntimeHookAdapter`・`AmbientExternBinding`・`pytra.std.json` の明示 seam に集約され、compiler/toolchain 本体から generic raw access は後退した。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-02] compiler/toolchain lane に残る `make_object` / `py_to` / `obj_to_*` usage は native `transpile_cli.cpp` の legacy import seam だけに絞られたため、`P2-object-bridge: legacy_migration_adapter` ラベルと `tools/check_compiler_object_bridge_labels.py` guard を追加し、未分類・再流入を fail-fast 化した。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-01] selfhost build/parity regression として `build_selfhost_stage2.py` の stage1->stage2 command/fallback と `verify_selfhost_end_to_end.py` の auto-target/stdout normalization を unit test で固定し始めた。
- 進捗メモ: [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-01] selfhost `prepare` / `verify` に加えて `build_selfhost_stage2` / `check_selfhost_stage2_cpp_diff` の command・fallback も unit test 化し、typed boundary 変更後の stage2 build/diff regressions を固定し始めた。

### P3: compiler contract を harden し、stage / pass / backend handoff を fail-closed にする

文脈: [docs/ja/plans/p3-compiler-contract-hardening.md](../plans/p3-compiler-contract-hardening.md)

1. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01] compiler contract を harden し、stage / pass / backend handoff を fail-closed にする。
2. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-01] `check_east_stage_boundary` / `validate_raw_east3_doc` / backend entry guard の現状を棚卸しし、未検証の blind spot（node shape、`type_expr` / `resolved_type`、`source_span`、helper metadata）を分類する。
3. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-02] `P1-EAST-TYPEEXPR-01` / `P2-COMPILER-TYPED-BOUNDARY-01` と責務が衝突しないように、schema validator / invariant validator / backend input validator の責務境界を decision log に固定する。
4. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-01] `spec-dev` または等価設計文書に、EAST3 / linked output / backend input の必須 field、許容欠落、diagnostic category を追加する。
5. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-02] `type_expr` / `resolved_type` mirror、`dispatch_mode`、`source_span`、helper metadata の整合ルールと fail-closed 方針を固定する。
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
