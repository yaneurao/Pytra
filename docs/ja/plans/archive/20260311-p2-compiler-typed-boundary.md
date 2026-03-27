<a href="../../../en/plans/archive/20260311-p2-compiler-typed-boundary.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2: compiler boundary の typed 化と internal object carrier の後退

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-COMPILER-TYPED-BOUNDARY-01`

背景:
- Pytra は型注釈付き Python を主対象とする一方、compiler/selfhost の内部境界にはまだ `dict[str, object]` / `list[object]` / `make_object(...)` が広く残っている。
- `transpile_cli`、`backend_registry_static`、selfhost parser 生成物、generated compiler runtime は、compiler root、backend spec、layer option、AST node を object carrier で受け渡す lane をまだ抱えている。
- bootstrap 期には有効だったが、いまは typed Python を正とする実装方針とずれており、`make_object` を compiler 内部から retreat させる阻害要因になっている。
- 先に compiler boundary 自体を typed carrier 化しない限り、`make_object` を乱暴に削ると selfhost/compiler が壊れる。

目的:
- compiler/selfhost の既知 schema payload を nominal typed carrier へ移し、internal な `dict[str, object]` / `list[object]` / `make_object(...)` 依存を explicit adapter seam まで後退させる。
- `make_object` / `py_to` / `obj_to_*` を user-facing な `Any/object` 境界、JSON seam、legacy export seam に限定し、compiler 内部の既知 schema では使わない形へ寄せる。
- selfhost/compiler の実装境界でも「静的型付き Python を正とする」方針を一貫させる。

対象:
- `src/toolchain/frontends/transpile_cli.py` とその selfhost 展開物
- `src/runtime/cpp/native/compiler/{transpile_cli,backend_registry_static}.{h,cpp}`
- `src/runtime/cpp/generated/compiler/*` および `selfhost/runtime/cpp/pytra-gen/compiler/*`
- selfhost parser / EAST builder（主に `src/toolchain/ir/core.py` とその分割先）
- compiler boundary 向け docs / guard / regression test

非対象:
- user-facing な `Any/object` 機能そのものの廃止
- `py_runtime.h` から `make_object` overload 群を一括削除すること
- stage1 selfhost の host-Python bridge をこの計画だけで完全撤去すること
- C++ runtime 全体の再設計

## 必須ルール

1. compiler 内部で schema が確定している payload は `dict[str, object]` ではなく nominal typed carrier で表現する。
2. `dict[str, object]` / `list[object]` を許可してよいのは JSON decode、extern/hook、旧互換 adapter などの明示境界だけとする。
3. selfhost parser / EAST builder は raw `dict<str, object>{{...}}` を正規経路にしてはならない。typed node constructor または builder helper を正本にする。
4. compiler 内部の動的 JSON 値は一般 `object` helper 拡張ではなく `JsonValue` のような専用 nominal 型へ隔離する。
5. compiler 側の `make_object` / `py_to` / `obj_to_*` は `user_boundary` / `json_adapter` / `legacy_migration_adapter` に分類できるものだけを残す。
6. migration 中に新しい generic carrier を増やしてはならない。旧 adapter を残す場合は plan / decision log で除去 step を固定する。
7. backend/runtime は typed boundary の不足を `object` fallback helper 追加で救済してはならない。

## 受け入れ基準

- `load_east3_document` など compiler の正規入口が typed root carrier を正本として扱う。
- `backend_registry_static` の backend spec / layer option / IR 受け渡しが typed carrier + explicit adapter に整理される。
- selfhost parser / generated compiler path で checked-in AST node を `dict<str, object>{{... make_object(...) ...}}` で直接組み立てる経路が縮退する。
- compiler lane に残る `make_object` / `py_to` usage が user-facing `Any/object` 境界または adapter seam へ明示分類される。
- typed boundary 方針に反する差分を fail-fast で落とせる guard がある。

## S3-02 の再定義

`S3-02` は helper を 1 個ずつ増やし続ける作業ではなく、次の完了条件を満たした時点で閉じる。

1. `core.py` の `postfix/suffix parser` cluster が専用 module へ分割され、`call` / `attr` / `subscript` が単一巨大ファイルに混在しない。
2. `core.py` の `call annotation` cluster が専用 module へ分割され、`named-call` / `attr-call` / `callee-call` が単一巨大ファイルに混在しない。
3. 残る `call-arg` / `suffix tail` / `subscript tail` の helper 抽出は 5-10 個単位の bundle で処理し、1 helper = 1 commit を止める。
4. generated/selfhost residual guard と export seam を再基準化し、`make_object` を `serialization/export seam` 専用まで後退させる。
5. TODO と plan の進捗メモは cluster 要約だけに留め、helper 単位の細片ログは git history に委ねる。

## 実装順

1. 現状棚卸しと分類
2. typed end state の固定
3. Python 正本側への typed carrier 導入
4. generated/native compiler interface への mirror
5. selfhost parser / EAST builder の raw object 組み立て縮退
6. JSON / hook / legacy adapter の隔離
7. guard / regression / archive

## 分解

- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01] `transpile_cli` / `backend_registry_static` / selfhost parser / generated compiler runtime に残る `dict[str, object]` / `list[object]` / `make_object` / `py_to` usage を棚卸しし、`compiler_internal` / `json_adapter` / `extern_hook` / `legacy_bridge` に分類する。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02] `spec-dev` / `spec-runtime` / `spec-boxing` と矛盾しない typed boundary 契約と non-goal を decision log に固定する。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-01] compiler root payload（EAST document / backend spec / layer option / emit request/result）の typed carrier 仕様を決める。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-02] Python 正本へ typed carrier と薄い legacy adapter を導入する。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-03] C++ selfhost/native compiler interface へ typed carrier mirror または typed wrapper API を導入し、raw `dict<str, object>` exchange を縮小する。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] selfhost parser / EAST builder の node 構築を typed constructor / builder helper へ寄せ、`dict<str, object>{{...}}` 直組み立てを段階縮退する。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] generated compiler / selfhost runtime に残る `make_object` usage を `serialization/export seam` 専用まで後退させる。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-A] `S3-02` の完了条件を再定義し、TODO / plan の進捗メモを cluster 単位へ圧縮する。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-B] `core.py` の postfix/suffix parser cluster を分割し、`call` / `attr` / `subscript` を専用 module へ移す。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-C] `core.py` の call annotation cluster を分割し、`named-call` / `attr-call` / `callee-call` を専用 module へ移す。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-D] `call-arg` / `suffix tail` / `subscript tail` に残る helper 抽出を 5-10 個単位の bundle で消化する。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-E] generated/selfhost residual guard と export seam を再基準化し、`make_object` を `serialization/export seam` 専用まで後退させて `S3-02` を閉じる。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] JSON・extern/hook・未型付け入力の dynamic carrier を compiler typed model から切り離し、`JsonValue` / explicit adapter に隔離する。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-02] `make_object` / `py_to` / `obj_to_*` の残存 usage に分類ラベルを与え、未分類・再流入を弾く guard を追加する。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-01] selfhost build / diff / prepare / bridge 回帰を更新し、typed boundary 変更後の非退行を固定する。
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-02] docs / TODO / archive を更新し、残る `make_object` が「user boundary 専用」か「明示 adapter 専用」かを記録して閉じる。

## `core.py` 分割方針

- `core.py` は最終的に orchestration と共通 helper だけを持つ。
- `postfix/suffix parser` は `call` / `attr` / `subscript` を専用 module へ切り出す。
- `call annotation` は `named-call` / `attr-call` / `callee-call` を専用 module へ切り出す。
- `call-arg` / `suffix tail` / `subscript tail` の微細 helper は、分割後の module 側で bundle 単位に整理する。
- `test_east_core.py` の guard も cluster 単位で再編し、1 helper ごとの微細 assert を減らす。

## 期待 deliverable

### S2

- `transpile_cli` と `backend_registry_static` が typed payload を正規経路とする。
- 旧 `dict[str, object]` API は薄い adapter としてだけ残る。

### S3

- selfhost parser / EAST builder が nominal node builder を使う。
- `core.py` が単一巨大ファイルのまま helper を積み増す構成から脱し、分割済み cluster を束単位で進める。
- generated/selfhost runtime の `make_object` usage が export seam へ集約される。

### S4

- `JsonValue` や extern/hook adapter のような動的 lane だけが object carrier を保持する。
- compiler 内部の generic carrier usage が「残す理由を説明できるもの」だけになる。

### S5

- selfhost regressions と audit が typed boundary の再崩壊を検知できる。
- docs/TODO/archive で end state が追跡可能になる。

決定ログ:
- 2026-03-09: ユーザー指示により、`make_object` 全削除を直接目指すのではなく、まず compiler boundary を typed 化して internal object carrier を retreat させる P2 を追加した。
- 2026-03-09: `Any/object` の user-facing 境界は現仕様として残るため、この P2 は language feature の削除ではなく compiler/selfhost 内部の動的 carrier 整理に集中する方針を固定した。
- 2026-03-09: `typed_boundary.py`、host/static registry、native C++ wrapper を typed carrier 正本に寄せ、raw dict surface は thin legacy adapter へ縮退した。
- 2026-03-10: `S3-01` は完了した。source-of-truth 側の checked-in node 構築は `_sh_make_*` helper 契約へほぼ収束し、module root / import / expr / stmt / comprehension / f-string / trivia / span carrier は guard 付きで固定された。
- 2026-03-10: `S3-02` 前半で typed export seam は `typed_boundary.py` 中心へ集約され、selfhost entrypoint も direct typed path へ寄った。generated/selfhost residual guard と source-of-truth guard は module root / import / expr / stmt / literal / comprehension / f-string lane を広く監視している。
- 2026-03-10: ただし `core.py` は 11k 行超、`test_east_core.py` は 4k 行超まで膨らみ、1 helper = 1 commit / 1 memo の進め方は前進量に対して粒度が細かすぎる状態になった。
- 2026-03-10: 以後の `S3-02` は `S3-02-B` から `S3-02-E` の cluster 単位で進める。`TODO` は cluster 要約のみを持ち、helper 単位の細片履歴は git history と必要最小限の decision log 要約へ圧縮する。
- 2026-03-10: `core.py` 分割を deliverable に格上げし、まず `postfix/suffix parser` cluster と `call annotation` cluster を専用 module へ出す。残る `call-arg` / `suffix tail` / `subscript tail` はその後に bundle 単位で処理する。
- 2026-03-10: `S3-02-B` の最初の塊として `call-arg` / `call-suffix` parser cluster を `core_expr_call_suffix.py` へ移し、`core.py` は mixin import と postfix dispatch orchestration に寄せた。source guard も helper 単位ではなく split cluster 単位で監視する方針に切り替えた。
- 2026-03-10: `attr/subscript suffix` parser cluster も `core_expr_attr_subscript_suffix.py` へ移し、`call` / `attr` / `subscript` の suffix parser は `core.py` から専用 module へ分割し終えた。`S3-02-B` は完了として閉じ、次は `call annotation` cluster の分割へ進む。
- 2026-03-10: `S3-02-C` の最初の塊では `call_expr` / `callee_call` の orchestration を `core_expr_call_annotation.py` へ移し、`named-call` / `attr-call` の lower-level apply と shared helper は `core.py` に残す段階 split とした。source guard も split-cluster 前提へ切り替える。
- 2026-03-10: `S3-02-C` は完了として閉じる。`core.py` から `call_expr` / `callee_call` / `named-call` / `attr-call` の annotation entrypoint は `core_expr_call_annotation.py` へ移り、残る細かい helper 抽出は `S3-02-D` の bundle work に寄せる。
- 2026-03-10: `S3-02-D` の最初の bundle では `call-arg` parser cluster を `core_expr_call_args.py` へ分割し、`core_expr_call_suffix.py` は `call suffix` 本体だけを持つ形へ縮める。以後も同じ粒度で `subscript tail` と `attr/suffix` 側を切る。
- 2026-03-10: `S3-02-D` は完了として閉じる。`call-arg` は `core_expr_call_args.py`、`call suffix` は `core_expr_call_suffix.py`、`attr/subscript suffix` は `core_expr_attr_subscript_suffix.py` に整理され、残りの helper 抽出も bundle 単位へ再編した。
- 2026-03-10: `S3-02-E` の初手として、generated selfhost core に残る `make_object` usage を関数単位で再基準化した。現時点では `to_payload` を export seam、残りを parser residual として guard 化する。
- 2026-03-10: generated selfhost core の residual `make_object` guard は `export_seam` と `parser_residual` の scope に分離し、export seam の判定が集合差分ではなく helper そのものの責務として読める形へ揃えた。
- 2026-03-10: parser residual 側も `expr_parser` / `stmt_parser` / `lookup` bucket に分けて固定した。以後の `S3-02-E` は bucket 単位で residual を減らし、最後に export seam 以外を空にする。
- 2026-03-10: `expr_parser` / `stmt_parser` / `lookup` の bucket 和集合が `parser_residual` と一致し、`export_seam` と交差しないことも guard 化した。以後は bucket ごとに件数を減らすだけで進捗が測れる。
- 2026-03-10: source-of-truth の compiler lane と native wrapper では `make_object` が export seam 以外から退いたことを確認した。generated selfhost core は `to_payload` を export seam、残りを explicit `parser_residual` guard として再基準化済みなので、`S3-02` は完了として閉じ、残る分類強化は `S4-02` で扱う。
- 2026-03-10: `S4-01` の初手として、dynamic carrier の現状 inventory を `JsonValue` raw carrier、extern-marked stdlib surface、`typed_boundary.py` の runtime-hook seam、compiler-root JSON load の 4 区分へ整理し、contract test に固定した。
- 2026-03-10: `runtime_hook` は `RuntimeHookAdapter` を通る explicit seam に寄せた。typed spec は raw callable を直接保持せず、export/apply 側だけが hook 本体へ触れる。native compiler-root JSON load も `_unwrap_compiler_root_json_doc()` / `_coerce_compiler_root_json_doc()` を named adapter にして、raw `JsonObj` の unwrap をその中へ閉じた。
- 2026-03-10: Python compiler lane にも `toolchain/json_adapters.py` を追加し、frontends `load_east_document`、`east_io.load_east_from_path`、link manifest/program loader/materializer、runtime symbol index の `loads_obj(...).raw` unwrap を `load_json_object_doc()` / `export_json_object_dict()` / `unwrap_east_root_json_doc()` に集約した。
- 2026-03-10: toolchain 側の JSON load seam も `toolchain.json_adapters` に集約した。`frontends/transpile_cli` / `ir/east_io` / `link_manifest_io` / `materializer` / `program_loader` / `runtime_symbol_index` は raw `json.loads_obj(...).raw` を持たず、named adapter から `JsonObj` または exported dict を受け取る。
- 2026-03-10: `py2x` / `ir2lang` の CLI root loader も `load_json_object_doc_or_none()` を通るようにした。toolchain 外周の JSON root 読み込みも同じ adapter seam に揃い、`json.loads_obj(...)` は `toolchain.json_adapters` へ後退した。
- 2026-03-10: `program_validator.py` に残っていた `JsonObj/JsonArr/JsonValue` raw access も `toolchain.json_adapters` に寄せた。`coerce_json_object_doc()` / `export_json_object_dict()` / `json_array_length()` / `export_json_value_raw()` を通し、validator 本体は raw carrier を直接触らない。
- 2026-03-10: `extern_var_v1` も explicit adapter seam に寄せた。`toolchain/frontends/extern_var.py` は raw `dict[str, str]` の binding list を返さず、`AmbientExternBinding` carrier を通して ambient extern validation を行う。
- 2026-03-10: `ir2lang` の EAST JSON unwrap も `unwrap_east_root_json_doc()` / `export_json_object_dict()` に寄せた。toolchain 外周 CLI lane に残っていた `.raw` 直参照はこれで `toolchain.json_adapters` の外へ出なくなった。
- 2026-03-10: 空 `JsonObj` fallback と `JsonValue -> JsonObj` 既定 coercion も `toolchain.json_adapters` に集約した。`empty_json_object_doc()` / `json_value_as_object_doc_or_empty()` を通して、`py2x` / `ir2lang` / `program_validator` から direct `json.JsonObj({})` を退けた。
- 2026-03-10: `program_loader` の in-memory module doc 受理も `coerce_json_object_dict()` に統一し、`JsonObj` 特判を外した。`typed_boundary.py` 側の compiler-root `raw_module_doc/meta` 参照も `export_compiler_root_module_doc()` / `compiler_root_meta_dict()` へ閉じ、dynamic carrier の残りを named helper seam に寄せた。
- 2026-03-11: `S4-02` では compiler/toolchain lane に残る `make_object` / `py_to` / `obj_to_*` usage を再棚卸しし、実 usage が native `transpile_cli.cpp` の `obj_to_int64` / `obj_to_dict` 3 箇所だけであることを確認した。各行に `P2-object-bridge: legacy_migration_adapter` を付け、`tools/check_compiler_object_bridge_labels.py` と unit test を追加して未分類・再流入を fail-fast 化した。
- 2026-03-10: `S4-01` は完了として閉じる。dynamic carrier は `toolchain.json_adapters`、`RuntimeHookAdapter`、`AmbientExternBinding`、`pytra.std.json` の明示 seam に集約され、compiler/toolchain 本体から generic raw access は後退した。
- 2026-03-11: `S5-01` の初手として `tools/build_selfhost_stage2.py` と `tools/check_selfhost_stage2_cpp_diff.py` に pure helper を追加し、stage2 build command、stage1 fallback 条件、stage2 diff command を unit test で固定した。typed boundary 変更後も `prepare` だけでなく `build/diff` 側で selfhost regressions を捕まえる。
- 2026-03-11: `S5-01` の次の束として `tools/verify_selfhost_end_to_end.py` と `tools/build_selfhost_stage2.py` の contract test を追加した。stage2 build の `py2x-selfhost.py -> py2cpp_stage2.cpp` command と `[not_implemented]` fallback copy、verify 側の auto-target resolve / sample stdout normalization / transpile command の `--target` 付与有無を unit test で固定した。
- 2026-03-11: `S5-01` では `tools/check_selfhost_cpp_diff.py` にも pure command helper を追加し、host `py2x-selfhost` command、selfhost direct/bridge command、auto-target resolve を unit test で固定した。build/prepare だけでなく diff lane も typed-boundary 後の selfhost contract を明示 guard する。
- 2026-03-11: `S5-01` では `test_prepare_selfhost_source.py` に generated selfhost core の `make_object` residual bucket category map と和集合 invariant も追加した。`serialization_export_seam` と `expr/stmt/lookup parser residual` の境界が崩れた場合は selfhost regression として fail-fast する。
- 2026-03-11: `S5-01` の bridge lane として `tools/selfhost_transpile.py` も helper 化し、`build_bridge_env()` / `build_selfhost_cmd_base()` / `build_selfhost_transpile_cmd()` / `build_python_to_east_json_cmd()` と `main()` の JSON passthrough、`.py -> EAST JSON -> selfhost` flow を unit test で固定した。
- 2026-03-11: `S5-01` の次の束として `test_check_selfhost_stage2_cpp_diff.py` に `main()` regression を追加し、stage2 build failure、`--skip-build` での missing binary、existing stage2 binary に対する build→diff flow を unit test で固定した。stage2 diff lane は helper command だけでなく CLI orchestration まで回帰化された。
- 2026-03-11: `S5-01` の次の束として `tools/selfhost_transpile.py` に command/env helper を追加し、`.json` passthrough、`.py -> EAST JSON -> selfhost` bridge、`PYTHONPATH` 付与、`--target` 伝播を `test_selfhost_transpile_tool.py` で固定した。bridge driver lane も typed-boundary regression の unit test 対象になった。
- 2026-03-11: `S5-01` の次の束として `tools/build_selfhost.py` に command helper を追加し、`test_build_selfhost_tool.py` で stage1 transpile command、compile command、runtime source resolve、`main()` の transpile→compile flow を unit test 化した。stage1 build lane も typed-boundary regression として固定した。
- 2026-03-11: `S5-01` は `build_selfhost.py` / `build_selfhost_stage2.py` / `verify_selfhost_end_to_end.py` / `check_selfhost_cpp_diff.py` / `check_selfhost_stage2_cpp_diff.py` / `selfhost_transpile.py` の command/helper/main regression と、generated selfhost core の residual bucket invariant を unit test で固定したことで完了とした。
- 2026-03-11: `S5-02` では docs/TODO/archive を更新し、compiler/toolchain tracked source に残る object bridge は native `transpile_cli.cpp` の `legacy_migration_adapter` 3 箇所だけ、generated selfhost core の `make_object` residual は `serialization_export_seam` と explicit parser residual guard だけであることを end state として固定した。user-facing `Any/object` 境界は P2 の非対象として runtime 側に残る。
