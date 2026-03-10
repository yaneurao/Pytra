# P2: compiler boundary の typed 化と internal object carrier の後退

最終更新: 2026-03-10

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
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] JSON・extern/hook・未型付け入力の dynamic carrier を compiler typed model から切り離し、`JsonValue` / explicit adapter に隔離する。
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-02] `make_object` / `py_to` / `obj_to_*` の残存 usage に分類ラベルを与え、未分類・再流入を弾く guard を追加する。
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-01] selfhost build / diff / prepare / bridge 回帰を更新し、typed boundary 変更後の非退行を固定する。
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-02] docs / TODO / archive を更新し、残る `make_object` が「user boundary 専用」か「明示 adapter 専用」かを記録して閉じる。

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
