# P2: compiler boundary の typed 化と internal object carrier の後退

最終更新: 2026-03-09

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P2-COMPILER-TYPED-BOUNDARY-01`

背景:
- Pytra は型注釈付き Python を主対象とするが、compiler/selfhost の内部境界にはまだ `dict[str, object]` / `list[object]` / `make_object(...)` が広く残っている。
- 現行の selfhost stage1 では、`transpile_cli` / `backend_registry_static` / selfhost parser 生成物が compiler document・backend spec・option payload・AST node を `object` carrier で受け渡している。
- この構成は bootstrap には有効だったが、typed Python を前提とする実装哲学とずれており、`make_object` を compiler 内部から後退させる障害になっている。
- `make_object` を runtime から丸ごと削る前に、まず compiler boundary 自体を typed carrier へ置き換えないと、selfhost/compiler は全面的に壊れる。

目的:
- compiler/selfhost の内部境界を nominal な typed carrier へ移し、`dict[str, object]` / `list[object]` / `make_object(...)` 依存を backend/runtime 内部 detail まで押し戻す。
- `make_object` / `py_to` / `obj_to_*` を「user-facing な `Any/object` 境界」または「明示 adapter seam」へ限定し、compiler 内部の既知 schema では使わない構成へ寄せる。
- Pytra の「静的型付き Python を正とする」方針を、selfhost/compiler 実装境界でも一貫させる。

対象:
- `src/toolchain/frontends/transpile_cli.py` とその selfhost 展開物
- `src/runtime/cpp/native/compiler/{transpile_cli,backend_registry_static}.{h,cpp}`
- `src/runtime/cpp/generated/compiler/*` および `selfhost/runtime/cpp/pytra-gen/compiler/*`
- selfhost parser / EAST builder (`src/toolchain/ir/core.py` 周辺) とその builder helper
- compiler boundary 向け docs / guard / regression test

非対象:
- user-facing な `Any/object` 機能そのものの廃止
- `py_runtime.h` から `make_object` overload 群を一括削除すること
- stage1 selfhost の host-Python bridge をこの計画だけで完全撤去すること
- C++ runtime 全体の再設計

## 必須ルール

推奨ではなく必須ルールとして扱う。

1. compiler 内部で schema が確定している payload は、`dict[str, object]` ではなく nominal typed carrier（class / dataclass / typed record）で表現する。
2. `dict[str, object]` / `list[object]` を許可してよいのは、JSON decode・extern/hook・旧互換 adapter などの明示境界だけとする。内部ロジックへ透過搬送してはならない。
3. selfhost parser / EAST builder は raw `dict<str, object>{{...}}` の組み立てを正規経路にしてはならない。typed node constructor または typed builder helper を正本にする。
4. compiler 内部の動的 JSON 値は、一般 `object` helper 拡張ではなく `JsonValue` などの専用 nominal 型へ隔離する。
5. `make_object` / `py_to` / `obj_to_*` の compiler 側 usage は、`user_boundary` / `json_adapter` / `legacy_migration_adapter` のいずれかへ分類できるものだけを残す。未分類 usage は負債として残してはならない。
6. migration 中に新しい generic carrier を増やしてはならない。古い adapter を残す場合は、どの step で消すかを plan / decision log に固定する。
7. backend/runtime は typed boundary の不足を `object` fallback helper 追加で救済してはならない。必要な型情報は frontend/lowering/builder 側で確定させる。

受け入れ基準:
- `load_east3_document` など compiler の正規入口が、raw `dict[str, object]` ではなく typed root carrier を正本として扱う。
- `backend_registry_static` の backend spec / layer option / IR 受け渡しが、raw object dict 常用ではなく typed carrier + 明示 adapter に整理される。
- selfhost parser / generated compiler path で checked-in AST node を `dict<str, object>{{... make_object(...) ...}}` で直接組み立てる経路が縮退または退役する。
- compiler lane に残る `make_object` / `py_to` usage が明示分類され、user-facing `Any/object` 境界または adapter seam 以外に新規残存しない。
- 再混入防止 guard（audit/test）が入り、typed boundary 方針に反する差分を fail-fast できる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 -m unittest discover -s test/unit/selfhost -p 'test_selfhost_virtual_dispatch_regression.py'`
- `python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`
- `git diff --check`

## 実装順

順序は固定する。先に typed contract を決め、次に adapter を入れ、その後で selfhost 生成物の raw object 組み立てを剥がす。

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
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-01] compiler root payload（EAST document / backend spec / layer option / emit request/result）の typed carrier 仕様を決める。
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-02] Python 正本（`transpile_cli.py` / registry helper / builder helper）へ typed carrier と薄い legacy adapter を導入する。
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-03] C++ selfhost/native compiler interface へ typed carrier mirror または typed wrapper API を導入し、raw `dict<str, object>` exchange を縮小する。
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] selfhost parser / EAST builder の node 構築を typed constructor / builder helper へ寄せ、`dict<str, object>{{...}}` 直組み立てを段階縮退する。
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] generated compiler / selfhost runtime に残る `make_object` usage を `serialization/export seam` 専用まで後退させる。
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] JSON・extern/hook・未型付け入力の dynamic carrier を compiler typed model から切り離し、`JsonValue` / explicit adapter に隔離する。
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-02] `make_object` / `py_to` / `obj_to_*` の残存 usage に分類ラベルを与え、未分類・再流入を弾く guard を追加する。
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-01] selfhost build / diff / prepare / bridge 回帰を更新し、typed boundary 変更後の非退行を固定する。
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-02] docs / TODO / archive を更新し、残る `make_object` が「user boundary 専用」か「明示 adapter 専用」かを記録して閉じる。

## 期待 deliverable

### S1 の deliverable

- どのファイルのどの usage が「compiler 内部に残してはいけない generic carrier」なのかを一覧化する。
- `make_object` を一括削除しない理由と、どこまでを P2 の完了条件とするかを明文化する。

### S2 の deliverable

- `transpile_cli` と `backend_registry_static` が typed payload を正規経路とする。
- 旧 `dict[str, object]` API は薄い adapter としてだけ残し、呼び出し元を順次 typed API へ寄せられる状態にする。

### S3 の deliverable

- selfhost parser / EAST builder が nominal node builder を使う。
- compiler node を構築するたびに `make_object("kind")` / `make_object(value)` を並べる checked-in path を縮退する。

### S4 の deliverable

- `JsonValue` や extern/hook adapter のような「動的であることが本質な経路」だけが object carrier を保持する。
- compiler 内部の generic carrier usage が「残す理由を説明できるもの」だけになる。

### S5 の deliverable

- selfhost regressions と audit が typed boundary の再崩壊を検知できる。
- docs/TODO/archive で end state が追跡可能になる。

決定ログ:
- 2026-03-09: ユーザー指示により、`make_object` 全削除を直接目指すのではなく、まず compiler boundary を typed 化して internal object carrier を retreat させる P2 を追加した。
- 2026-03-09: `Any/object` の user-facing 境界は現仕様として残るため、この P2 の主眼は language feature の削除ではなく、compiler/selfhost 内部の動的 carrier 整理に置く方針を固定した。
- 2026-03-09: stage1 selfhost の host-Python bridge 撤去は本 P2 の非対象とし、typed carrier 導入後に別タスクまたは後続 step で扱う方針を固定した。
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01]: `json_adapter` は JSON root decode / encode の明示 seam に限定して先に分類した。代表箇所は `src/toolchain/frontends/transpile_cli.py` の `load_east_document()` にある `.json` 入力 lane（`json.loads_obj(...).raw` を `normalize_east_root_document(...)` へ渡す経路）、`src/runtime/cpp/native/compiler/transpile_cli.cpp` の `_load_json_root_dict()`、`src/runtime/cpp/native/compiler/backend_registry_static.cpp` の `emit_source()` で `ir` を `json.dumps(make_object(ir))` して host Python へ渡す lane である。ここは typed carrier へ置換した後も最後の adapter seam として残りうる。
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01]: `legacy_bridge` は「typed 化できるのに raw object dict API を公開している」経路として固定した。代表箇所は `src/toolchain/frontends/transpile_cli.py` の `load_east_document()` にある `east_any_wrap: {"east": east_any}` と `dict_any_get_dict(...)` による dict 強制、`src/runtime/cpp/native/compiler/transpile_cli.h/.cpp` の `load_east3_document(...) -> dict<str, object>` 公開 API、`selfhost/py2cpp.py` の mirrored `dict_any_get*` 群と `tools/prepare_selfhost_source.py` がそれら helper を selfhost seed に固定 export している点である。P2 ではこの category を thin adapter に押し込め、内部正規経路から外す。
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01]: `compiler_internal` は compiler が既知 schema を持つのに generic carrier へ逃がしている payload と定義した。代表箇所は `src/toolchain/frontends/transpile_cli.py` の `extract_function_signatures_from_python_source()` が返す `dict[str, dict[str, object]]` signature map、`src/runtime/cpp/native/compiler/backend_registry_static.cpp` の `get_backend_spec()` / `resolve_layer_options()` / `lower_ir()` / `optimize_ir()`、source of truth 側 `src/toolchain/ir/core.py` の node/module builder、そして mirror である `selfhost/runtime/cpp/pytra-gen/compiler/east_parts/core.cpp` の `_sh_append_fstring_literal()` / `_sh_parse_def_sig()` / module root assembly が `dict<str, object>{{... make_object(...) ...}}` で AST node と meta を直組み立てしている経路である。S2-S3 はここを typed carrier / typed builder に置換する。
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01]: `extern_hook` は selfhost 側の `@extern` 剥離面を explicit dynamic seam として扱う。代表箇所は `selfhost/py2cpp.py` の `_is_extern_call_expr()` / `_is_extern_function_decl()` / `_is_extern_variable_decl()` / `_build_cpp_emit_module_without_extern_decls()` と、native 側 `src/runtime/cpp/native/compiler/backend_registry_static.cpp` の `apply_runtime_hook(...)` であり、いずれも typed compiler payload の正規経路ではなく S4 で `JsonValue` / explicit adapter と同列の隔離対象に置く。
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02]: `spec-boxing` と整合させ、P2 は `Any/object` 境界そのものを削除しない non-goal と固定した。`make_object(...)`、`obj_to_*`、`py_to_*` は引き続き user-facing `Any/object` 境界の契約対象であり、P2 が retreat させるのは compiler/selfhost 内部で schema が既知なのに raw object carrier へ逃がしている lane だけとする。
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02]: `spec-runtime` / `spec-dev` と整合させ、JSON の動的性を一般 `object` helper 拡張の理由にしない方針を固定した。compiler boundary で raw `dict[str, object]` / `list[object]` が残ってよいのは JSON root decode/encode の明示 adapter seam に限り、長期正規形は `JsonValue` / `JsonObj` / `JsonArr` nominal lane に接続する。typed carrier 不足を `sum(object)` / `zip(object, object)` のような fallback helper 追加で救済してはならない。
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02]: `spec-dev` の contract に従い、typed boundary の意味論は frontend/lowering 正本とし、backend/hook/native runtime が raw dict や callee 名から再解釈してはならない。特に `type_expr` を型意味論の正本、`resolved_type` を mirror、`meta.dispatch_mode` を compile 開始時に一度だけ確定する補助情報として維持し、typed carrier 化の途中でも backend/runtime 側の silent fallback や再判定は禁止する。
- 2026-03-09 [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02]: `spec-dev` にある `ModuleArtifact.metadata` / `ProgramArtifact.writer_options` の object slot は target 固有 leaf payload を許すためのものであり、compiler root payload 全体を raw `dict[str, object]` transport のまま維持してよい理由にはしない。P2 の typed carrier 対象は EAST root / backend spec / layer option / emit request/result の既知 schema に限定し、full nominal ADT rollout と stage1 host-Python bridge 全撤去は別タスクの non-goal として維持する。
