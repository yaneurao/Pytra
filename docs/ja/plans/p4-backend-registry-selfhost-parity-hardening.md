# P4: backend_registry の正本化と selfhost parity gate の強化

最終更新: 2026-03-11

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01`

背景:
- host 実行系の `toolchain/compiler/backend_registry.py` と selfhost/static 系の `toolchain/compiler/backend_registry_static.py` は、backend spec・runtime copy・emitter wiring・option schema をかなり重複して持っている。
- この重複は bootstrap には有効だったが、backend surface を更新するたびに片側だけ修正する drift を生みやすい。
- selfhost 側にも確認ツールはある。`build_selfhost.py`、`build_selfhost_stage2.py`、`verify_selfhost_end_to_end.py`、`check_multilang_selfhost_suite.py` などが存在するが、運用上は補助ツール寄りで、変換器内部の変更に対する常設 gate としてはまだ弱い。
- さらに、current selfhost path には direct route / host Python bridge / preview lane など複数の暫定経路が混在し、どこまでが expected block でどこからが regression かが分かりづらい。
- P2/P3 で typed boundary と contract を強化しても、registry の SoT と selfhost parity gate が弱いままだと、host lane と selfhost lane の divergence が再発する。

目的:
- backend spec / runtime copy / layer option schema / writer rule の正本を一本化し、host registry と selfhost/static registry の drift を減らす。
- selfhost parity を「参考情報」ではなく、compiler 内部改良の非退行を守る gate として強化する。
- stage1 / stage2 / direct-route / multilang selfhost の failure category を整理し、どの失敗が既知 block でどの失敗が regression かを明確にする。

関連レポート:
- [P4 Selfhost Parity Readiness Report](./p4-selfhost-parity-readiness-report.md)

対象:
- `toolchain/compiler/backend_registry.py`
- `toolchain/compiler/backend_registry_static.py`
- backend spec / runtime copy / option schema / writer helper の共有化
- `tools/build_selfhost.py` / `build_selfhost_stage2.py` / `verify_selfhost_end_to_end.py`
- `tools/check_multilang_selfhost_stage1.py` / `check_multilang_selfhost_multistage.py` / `check_multilang_selfhost_suite.py`
- selfhost parity docs / reports / guard

非対象:
- typed carrier 設計そのもの
- host-Python bridge の完全撤去
- すべての backend を直ちに multistage selfhost 成功へ持ち上げること
- backend language feature の新規実装
- runtime の全面再設計

依存:
- `P2-COMPILER-TYPED-BOUNDARY-01` の boundary ownership が固まっていること
- `P3-COMPILER-CONTRACT-HARDENING-01` の validator / diagnostic 契約が少なくとも representative lane で使えること

## 必須ルール

推奨ではなく必須ルールとして扱う。

1. backend capability / runtime copy / option schema / writer rule の正本は 1 箇所に固定し、host/static へ手書き重複させてはならない。
2. host registry と selfhost/static registry が異なる挙動を持つ場合は、「意図的差分」か「drift」かを明示しなければならない。
3. selfhost parity の failure category は `known_block` / `not_implemented` / `regression` などに分類し、曖昧な preview 文言だけで終わらせてはならない。
4. stage1 / stage2 / direct-route / multilang の representative gate は、release 前または大きな compiler 内部変更前に定常実行できる形へ寄せる。
5. unsupported target / unsupported mode は、registry と parity report の両方で同じ診断カテゴリを返すべきである。
6. runtime copy list や backend spec を更新したときは、shared SoT と parity report の両方を更新しなければならない。
7. selfhost parity は「全部通るまで merge しない」ではなくてもよいが、既知 block と regression を区別できない状態を放置してはならない。

受け入れ基準:
- backend spec / runtime copy / option schema / writer metadata の正本が shared 化され、host/static registry の手書き重複が減る。
- drift を検知する guard または diff test が入り、片側だけ更新された registry surface を検知できる。
- selfhost parity suite に stage1 / stage2 / direct e2e / multilang representative lane の failure category が揃う。
- representative compiler 変更で、どの selfhost failure が expected block でどの failure が regression か追える。
- docs / report / archive で selfhost readiness と known block の文脈が追跡可能になる。

確認コマンド（予定）:
- `python3 tools/check_todo_priority.py`
- `python3 tools/build_selfhost.py`
- `python3 tools/build_selfhost_stage2.py --skip-stage1-build`
- `python3 tools/verify_selfhost_end_to_end.py --skip-build`
- `python3 tools/check_multilang_selfhost_suite.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_*selfhost*.py'`
- `git diff --check`

## 実装順

順序は固定する。まず drift source を棚卸しし、次に SoT を一本化し、その後に parity gate を強化する。

1. registry drift と parity blind spot の棚卸し
2. canonical backend spec / runtime metadata の固定
3. host/static registry の shared 化
4. selfhost parity gate / report / failure category の強化
5. docs / archive / migration note の更新

## 分解

- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-01] `backend_registry.py` と `backend_registry_static.py` の重複 surface（backend spec、runtime copy、writer rule、option schema、direct-route behavior）を棚卸しし、intentional difference と drift 候補を分類した。
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-02] `build_selfhost` / `stage2` / `verify_selfhost_end_to_end` / `multilang selfhost` の現状 gate と blind spot を整理し、known block / regression の分類方針を decision log に固定した。
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-01] backend capability / runtime copy / option schema / writer metadata の canonical SoT を定義し、host/static の両方がそこから構成される形へ寄せた。
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-02] intentional difference を許す境界（例: host-only lazy import、selfhost-only direct route）と、その diagnostics 契約を固定した。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-01] host registry / static registry を shared metadata または generator 経由へ寄せ、手書き重複を縮退する。
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-02] registry drift guard または diff test を追加し、片側だけ更新された backend surface を fail-fast で検知した。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-01] stage1 / stage2 / direct e2e / multilang selfhost の representative parity suite を整理し、failure category と summary 出力を統一する。
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-02] unsupported / preview / known block / regression の診断カテゴリを registry と parity report で揃え、expected failure を明示管理できるようにする。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-01] docs / plan report / archive を更新し、backend readiness・known block・gate 実行手順を追跡可能にする。
- [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-02] representative internal change に対して host lane と selfhost lane が同じ contract で検証されることを確認し、再流入 guard を固定する。

## 期待 deliverable

### S1 の deliverable

- host/static registry の drift 候補一覧
- selfhost parity の blind spot 一覧

### S2 の deliverable

- backend registry SoT の設計
- intentional difference と diagnostics 契約

### S3 の deliverable

- shared metadata / generator / adapter
- drift guard

### S4 の deliverable

- selfhost parity summary のカテゴリ統一
- stage1 / stage2 / direct-route / multilang の representative gate

### S5 の deliverable

- readiness と known block を追跡できる docs/report
- 今後の internal 改修で host/selfhost divergence を検知する再流入 guard

決定ログ:
- 2026-03-09: ユーザー指示により、backend registry の重複と selfhost parity 運用を内部改善タスクとして独立 P4 に切り出した。
- 2026-03-09: この P4 は backend language feature 追加ではなく、registry の SoT 一本化と selfhost non-regression gate の強化を主眼に置く。
- 2026-03-09: host lane と selfhost lane の差分を全面禁止するのではなく、intentional difference と drift を区別し、両者を report / guard で管理する方針を固定した。
- 2026-03-11: `P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-01` の棚卸しとして、intentional difference は host 側の lazy import (`importlib`, `_TARGET_LOADERS`, `_SPEC_CACHE`)、static 側の eager import (`_BACKEND_SPECS`, `_BACKEND_RUNTIME_SPECS`)、および `build_resolved_backend_spec(..., suppress_emit_exceptions=True/False)` に限定して扱うと決めた。
- 2026-03-11: drift 候補は 4 系統に分類した。`_runtime_*` / `_copy_runtime_file` / `_copy_php_runtime` の runtime copy 実装重複、backend metadata table（`target_lang`, `extension`, `lower/optimizer/emit`, `runtime_hook`, C++ `default_options` / `option_schema`）、emit wrapper 差分（host `_load_*_spec` / `_make_unary_emit` と static `_emit_*`）、default writer 注入（lazy `_load_callable(...)` と direct `write_single_file_program`）である。
- 2026-03-11: `resolve_layer_options_*`, `lower_ir_*`, `optimize_ir_*`, `emit_module_*`, `emit_source_*`, `get_program_writer_*`, `apply_runtime_hook_*` の execution surface は `typed_boundary` helper でほぼ共有済みであり、P4 の主対象は execute path ではなく backend metadata 構築と runtime/report path の SoT 一本化だと判断した。
- 2026-03-11: `P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-02` の棚卸しでは、`build_selfhost.py` は stage-boundary preflight + transpile + compile の fail-fast gate だが category を返さず、`build_selfhost_stage2.py` は `[not_implemented]` fallback reuse だけを特別扱いし、`verify_selfhost_end_to_end.py` は direct-route parity を `build/transpile/compile/run/stdout` の plain `[FAIL ...]` と `failures=N` に畳んでいて expected block を持たないことを blind spot として固定した。
- 2026-03-11: 同じ棚卸しで、`check_multilang_selfhost_stage1.py` は `stage1/mode/stage2/note` で preview/toolchain-missing を表すが category 列がなく、`check_multilang_selfhost_multistage.py` は `category` 列を持つ一方で `check_multilang_selfhost_suite.py` の summary と direct-route lane に統一されていないことを blind spot として固定した。
- 2026-03-11: 分類方針として、selfhost parity report が扱う category は最低でも `pass` / `known_block` / `preview_only` / `toolchain_missing` / `not_implemented` / `regression` に正規化し、build-only gate は内部で raw exit code を返しても report 層では同じ category へ写像する方針にした。
- 2026-03-11: representative gate の役割は、`build_selfhost.py` を stage1 preflight build、`build_selfhost_stage2.py` と `check_selfhost_stage2_cpp_diff.py` を stage2 drift/build、`verify_selfhost_end_to_end.py` を direct-route parity、`check_multilang_selfhost_stage1.py` / `check_multilang_selfhost_multistage.py` / `check_multilang_selfhost_suite.py` を multilang readiness summary と整理し、S4 では summary format と failure category をこの役割に沿って統一すると決めた。
- 2026-03-11: `P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-02` では representative gate を 4 系統に固定した。`build_selfhost.py` は C++ stage1 build gate、`build_selfhost_stage2.py` と `check_selfhost_stage2_cpp_diff.py` は C++ stage2/self-diff gate、`verify_selfhost_end_to_end.py` は C++ direct-route stdout parity gate、`check_multilang_selfhost_stage1.py` / `check_multilang_selfhost_multistage.py` / `check_multilang_selfhost_suite.py` は non-C++ parity report gate と扱う。
- 2026-03-11: blind spot も 4 系統に分類した。`build_selfhost.py` / `build_selfhost_stage2.py` は raw exit code と fallback warning に依存して structured category を返さないこと、`verify_selfhost_end_to_end.py` は小さい固定ケースの stdout parity に偏り artifact diff と failure taxonomy を持たないこと、`check_selfhost_cpp_diff.py` と direct-route lane が `allow-not-implemented` のような mode で expected block を外部化していること、multilang suite は `preview_only` / `toolchain_missing` / `self_retranspile_fail` などの category を持つ一方で C++ lane と summary vocabulary が揃っていないことである。
- 2026-03-11: 以後の parity report は top-level で `pass` / `known_block` / `toolchain_missing` / `regression` を使い、detail category として `preview_only` / `not_implemented` / `unsupported_by_design` / `self_retranspile_fail` / `stage2_compile_fail` / `sample_transpile_fail` / `direct_parity_fail` を保持する方針にした。意図的 block は `known_block` に正規化し、以前に pass していた representative lane の失敗、unexpected fallback、artifact/stdout diff、missing output は `regression` と扱う。
- 2026-03-11: `P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-01` の最初の slice として `toolchain/compiler/backend_registry_metadata.py` を追加し、backend target order、`target_lang` / `extension` / `runtime_mode` / `program_writer_kind`、および C++ `default_options` / `option_schema` を shared metadata row に集約した。
- 2026-03-11: host 側の `_load_*_spec()` と static 側の `_BACKEND_SPECS` は `build_backend_spec_row(...)` 経由で metadata row を参照する形へ寄せた。これにより backend spec row の table duplication は縮退したが、runtime copy function body と emit/runtime callable wiring 自体はまだ host/static で別実装なので、S2-01 は継続しつつ S3-01 の shared 化対象として残す。
- 2026-03-11: 同じ `S2-01` の次の slice で、shared metadata は table row だけでなく `lower_ref` / `optimizer_ref` / `emit_ref` / `emit_kind` / `runtime_hook_key` / `program_writer_key` と runtime file descriptor まで持つ形へ拡張した。host registry は lazy import を維持したまま `_load_backend_spec(target)` で canonical ref/descriptor を読み、static registry も `_build_backend_spec(target)` と `_STATIC_CALLABLES` 経由で同じ descriptor を解決する形へ寄せた。残る intentional difference は import/evaluation の eager vs lazy と `suppress_emit_exceptions=True/False` である。
- 2026-03-11: `S2-01` の完了条件は満たしたと判断した。canonical SoT は `backend_registry_metadata.py` に固定され、backend target order、spec metadata row、lower/optimizer/emit ref、runtime hook descriptor、program writer ref を host/static の両方が参照する形になったため、次は intentional difference と diagnostics 契約を `S2-02` で固定する。
- 2026-03-11: `S2-02` の最初の契約として、host/static の intentional difference は `importlib + _SPEC_CACHE` による lazy import と `_STATIC_CALLABLES + _BACKEND_RUNTIME_SPECS` による eager resolve、そして `suppress_emit_exceptions=True/False` に限定すると固定した。unsupported target の診断は両 lane で同じ `RuntimeError("unsupported target: ...")` を返し、runtime hook / program writer / emit ref の不整合は canonical metadata layer 側の key/ref 解決エラーとして露出させる。
- 2026-03-11: `S2-02` の次の slice では diagnostics 契約を追加で固定し、host 側の backend symbol ref 解決失敗も static 側と同じ `RuntimeError("unsupported backend symbol ref: ...")` に正規化した。runtime hook key / program writer key / backend symbol ref は host/static で同じ canonical error を返す。
- 2026-03-11: `S2-02` の diagnostics 契約として、canonical metadata layer の unknown `runtime_hook_key` / `program_writer_key` は `RuntimeError("unsupported ... key: ...")` で fail-fast する test を追加した。registry 側はこの metadata error を隠蔽せず、そのまま drift/設定ミスとして扱う。
- 2026-03-11: さらに `S2-02` で、metadata descriptor 自体が壊れて `runtime_hook kind` / `emit kind` が不正になった場合も host/static 両方で同じ `RuntimeError("unsupported ... kind: ...")` を返す contract test を追加した。kind-level diagnostics も eager/lazy 差分の外側では一致させる。
- 2026-03-11: `S2-02` は完了と判断した。intentional difference は lazy import / eager resolve / `suppress_emit_exceptions` のみに固定され、unsupported target / metadata key / backend symbol ref / kind-level diagnostics は host/static 両 lane で同じ canonical error text を返す guard が入った。
- 2026-03-11: `S3-01` の最初の slice として、host/static に完全重複していた runtime copy / php runtime copy / default output path / no-op runtime hook helper を `toolchain/compiler/backend_registry_shared.py` へ切り出した。intentional difference は lazy/eager callable resolve に限定し、pure helper の手書き重複は shared module へ寄せる方針にした。
- 2026-03-11: `S3-01` の次の slice では、host/static に残っていた `identity_ir` / `empty_emit` も `backend_registry_shared.py` へ移した。typed boundary の pure adapter は intentional difference に含めないと決め、registry layer 側の lazy/eager 差分だけを残す。
- 2026-03-11: `S3-01` の次の cluster として、host/static でまだ重複していた emit wrapper (`cpp/java/unary`) と backend spec assemble を `backend_registry_shared.py` の `build_*_emit` / `build_emit_from_target` / `build_runtime_bound_backend_spec` 経由へ寄せた。registry 側の意図的差分は callable resolver と `suppress_emit_exceptions` に限定する。
- 2026-03-11: 続く `S3-01` の cluster で、`runtime_hook key -> descriptor -> copy/js/php hook` の wiring も `backend_registry_shared.py` の `build_runtime_hook_from_key` へ寄せた。host/static には js shim 実装本体だけを残し、runtime file copy descriptor 解決は shared helper に一本化した。
- 2026-03-11: さらに `S3-01` で、`_load_backend_spec` / `_build_backend_spec` と `_normalize_backend_runtime_spec` の共通部分も `backend_registry_shared.py` の `build_runtime_bound_backend_spec` / `normalize_runtime_backend_spec` へ寄せた。host/static の違いは resolver と `suppress_emit_exceptions` / default writer 注入だけに縮める。
- 2026-03-11: 次の `S3-01` cluster では、`default_output_path`、`resolve_layer_options_*`、`lower/optimize/emit`、program artifact / writer / runtime hook までの typed execution wrapper 群も `backend_registry_shared.py` の `*_with_backend_spec` helper へ寄せた。これで host/static に残る大きな差分は eager-vs-lazy callable resolve、spec cache shape、default writer 注入、`suppress_emit_exceptions` まで縮んだ。
- 2026-03-11: 続く `S3-01` cluster では、host/static registry から未使用の `typed_boundary` execution import と dead adapter を外し、contract test も shared execution wrapper 前提へ更新した。registry 側の direct `typed_boundary` 依存は carrier 型、`coerce_backend_spec`、`export_resolved_backend_spec_any` まで縮める。
- 2026-03-11: `S3-01` は完了と判断した。host/static に残る差分は lazy/eager callable resolve、`_SPEC_CACHE` と `_BACKEND_RUNTIME_SPECS` の cache shape、default writer 注入、`suppress_emit_exceptions` の intentional difference に限られ、runtime copy・emit wrapper・backend spec assemble・typed execution wrapper の手書き重複は shared helper 側へ後退した。
- 2026-03-11: `S3-02` では `test_backend_registry_drift_guard.py` を追加し、host/static registry の public function signature、`backend_registry_shared` import、`typed_boundary` import、intentional private helper/state difference を AST ベースで固定した。これにより片側だけ helper/import/private cache を更新した場合は unit test が fail-fast する。
- 2026-03-11: `S3-02` は完了と判断した。canonical backend metadata parity は既存の metadata/contract test が、registry source topology parity は新しい drift guard test が担当する形で、backend surface の一方更新を representative lane で検知できる。
- 2026-03-11: `S4-01` の最初の cluster として `tools/selfhost_parity_summary.py` を追加し、`check_multilang_selfhost_suite.py` の stage1/multistage summary を `pass / known_block / toolchain_missing / regression` の top-level category と detail category に正規化する helper 経由へ寄せた。まず multilang summary から vocabulary を固定し、次の cluster で direct/stage2 側へ広げる。
- 2026-03-11: `S4-01` の次の cluster では `verify_selfhost_end_to_end.py` に direct parity summary helper を追加し、`[not_implemented]` を含む selfhost transpile failure を `known_block/not_implemented`、stdout mismatch を `regression/direct_parity_fail` に正規化した。`check_selfhost_stage2_sample_parity.py` は同 tool を使うため、この cluster で direct/stage2 lane も shared summary vocabulary を共有する。
- 2026-03-11: 同じ `S4-01` で `check_selfhost_stage2_sample_parity.py` 自身にも `stage2` lane summary を追加し、build failure・missing binary・verify exit を `stage2_build_fail` / `missing_output` / `direct_parity_fail` に正規化した。direct e2e 側は all-pass 時も `subject=all category=pass` を返すので、multilang / direct / stage2 wrapper の summary surface が同じ renderer に揃った。
- 2026-03-11: 続く `S4-01` cluster で `check_selfhost_cpp_diff.py` に `stage2-diff` summary helper を追加し、`allow-not-implemented` skip を `known_block/not_implemented`、expected diff file に列挙された mismatch を `known_block`、unexpected C++ artifact diff を `regression/stage2_diff_fail` に正規化した。これで multilang / direct / stage2-diff の representative parity suite が同じ top-level category を共有する。
- 2026-03-11: `S4-01` は完了と判断した。`check_multilang_selfhost_suite.py`、`verify_selfhost_end_to_end.py`、`check_selfhost_stage2_sample_parity.py`、`check_selfhost_cpp_diff.py`、`check_selfhost_stage2_cpp_diff.py` が共通の summary helper と top-level category vocabulary を共有し、all-pass 集計も含めて representative parity suite の出力面が揃ったため、残課題は `S4-02` の registry/report 間 category 整合に移る。
- 2026-03-11: さらに `check_selfhost_stage2_sample_parity.py` が使う `build_stage2_summary_row()` を `tools/selfhost_parity_summary.py` に追加し、stage2 sample parity の build/missing-binary/verify-fail も `stage2` lane の shared summary vocabulary に寄せた。これで representative stage2 lane は wrapper 側でも stable な summary block を返す。
- 2026-03-11: 同じ `S4-01` の次の cluster で `check_selfhost_cpp_diff.py` から local `_build/_print` summary wrapper を外し、`build_stage2_diff_summary_row()` と `render_summary_block()` を直接使う形へ揃えた。これで stage2-diff lane の summary mapping は shared helper 側だけが持つ。
- 2026-03-11: 続く `S4-01` で `print_summary_block()` を `tools/selfhost_parity_summary.py` に追加し、direct e2e / stage2 sample / stage2 diff / multilang suite の summary 出力も同じ printer helper へ寄せた。これで representative parity lane は vocabulary だけでなく render path も共有する。
- 2026-03-11: `S4-02` の最初の slice として `tools/selfhost_parity_summary.py` に `classify_known_block_detail()` を追加し、`[unsupported_by_design]` と registry 側の `unsupported target:` 診断を `known_block/unsupported_by_design` へ正規化した。これで direct e2e と stage2-diff parity lane は expected unsupported failure を regression 扱いせず共有 vocabulary 上で管理できる。
- 2026-03-11: 続く `S4-02` の cluster で `toolchain/compiler/backend_registry_diagnostics.py` を追加し、registry/parity が共有する top-level category 正規化と diagnostic text 推定を一本化した。`unsupported target/profile/non-cpp build target` は `unsupported_by_design -> known_block`、`unsupported backend symbol ref/runtime hook key/emit kind` は `regression` と定義し、registry の error text も同 helper の message builder に寄せた。
- 2026-03-11: 次の `S4-02` cluster では multistage selfhost report の `runner_not_defined` を `unsupported_by_design` へ寄せ、expected failure と regression を raw category の段階から分離した。`check_multilang_selfhost_suite.py` 側ではこの detail が `known_block` に正規化されることを test で固定した。
- 2026-03-11: `S4-02` の次の cluster で parity 側の known-block detail 判定も `backend_registry_diagnostics.py` の `KNOWN_BLOCK_DETAIL_CATEGORIES` / `infer_diagnostic_detail_from_text()` に揃えた。これで `preview backend ...` は direct e2e / stage2-diff でも `known_block/preview_only` に正規化され、registry 側の `classify_registry_diagnostic()` も `preview_only` / `toolchain_missing` をそのまま top-level category へ写像する。
- 2026-03-11: 続く `S4-02` で parity note 判定の正本も `backend_registry_diagnostics.py` の `classify_parity_note_detail()` に寄せた。`check_multilang_selfhost_suite.py` の stage1 summary は preview/toolchain/unsupported note をこの helper から受け取り、`selfhost_parity_summary.py` の known-block 判定も同じ helper を再利用する。
- 2026-03-11: `S4-02` は完了と判断した。registry 側の diagnostics helper、direct e2e / stage2-diff parity summary、multilang selfhost summary が `unsupported_by_design` / `preview_only` / `toolchain_missing` / `regression` を同じ shared vocabulary で扱い、expected failure を代表 lane 全体で同じ category contract として追跡できるようになった。
- 2026-03-11: `S5-01` の最初の slice として `docs/ja/plans/p4-selfhost-parity-readiness-report.md` を追加し、representative gate の実行順、shared category contract、current known block の読み方を 1 枚へ集約した。P4 plan から report へ直接飛べるようにし、gate 実行手順を decision log から探さなくても辿れる入口を用意した。
- 2026-03-11: 続く `S5-01` で docs index と `plans/README.md` に readiness report 導線の規約を追加した。report は plan にぶら下がる補助文書として扱い、P4 の入口を `docs/ja/index.md` からも辿れるようにした。
- 2026-03-11: `S5-01` の最後の slice で readiness report に archive handoff を明記した。P4 完了時は plan / report / todo archive を同じ完了日で結び直す前提を report 側にも残し、`archive/index.md` と日次 archive への追記先を固定した。
- 2026-03-11: `S5-02` の最初の slice として `test_backend_registry_selfhost_contract_guard.py` を追加し、shared diagnostics の representative case（`unsupported_by_design` / `preview_only` / `toolchain_missing`）が host registry、direct e2e、stage2 diff、multilang summary の 4 lane で同じ contract に落ちることを 1 本の guard で固定する方針にした。
- 2026-03-11: 続く `S5-02` で `tools/check_selfhost_contract_reentry_guard.py` を追加し、representative internal change で先に走らせる host lane (`test_py2x_entrypoints_contract.py`) と selfhost lane (`test_prepare_selfhost_source.py`, `test_selfhost_build_verify_tools.py`, `test_check_selfhost_cpp_diff.py`, `test_check_selfhost_stage2_cpp_diff.py`) を 1 コマンドへ束ねた。`run_local_ci.py` と readiness report もこの command を参照する形へ揃えた。
- 2026-03-11: 同じ `S5-01` の follow-up として representative gate を再実行し、`direct_e2e=pass` / `stage2_diff=pass` と multilang `stage1_transpile_fail` snapshot を readiness report と `todo/archive/20260311.md` に固定した。これで gate 実行順だけでなく、その日の representative status も docs / archive の両方から追跡できる。
