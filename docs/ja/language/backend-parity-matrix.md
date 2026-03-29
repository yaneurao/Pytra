<a href="../../en/language/backend-parity-matrix.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# Backend Parity Matrix

このページは、feature × backend の support state を公開する canonical publish target です。

## Support Matrix と Coverage Surface の分離

- このページは support matrix の canonical publish target であり、bundle-based coverage matrix そのものではありません。
- `feature x required_lane x backend` の contract coverage seed と ownership は [backend-coverage-matrix.md](./backend-coverage-matrix.md) を別 surface として公開し、`backend-test-matrix.md` は backend-owned suite health の publish target に留めます。
- bundle-based coverage の live surface は [backend-coverage-matrix.md](./backend-coverage-matrix.md) を使います。
- coverage 100% の定義は line/branch coverage ではなく、`feature x required_lane x backend` ごとの contract coverage です。

## Canonical Source と Drill-Down

- このページを正本とし、C++ 専用の詳細表は drill-down として [./cpp/spec-support.md](./cpp/spec-support.md) に置きます。
- C++ 詳細表は cpp lane だけを細かく補う補助資料で、cross-backend taxonomy 自体はこのページで定義します。
- このページと tooling contract を先に更新し、その後で C++ の詳細表を同期します。
- representative -> secondary -> long_tail の順で cell を埋めます。

## 現在の実装段階

- 現在の matrix は `cell_seed_manifest` 段階です。
- tooling manifest には row ごとの `backend_cells` seed があり、`cpp` は `supported/build_run_smoke`、review 済みの representative / secondary / long-tail cell は `supported/transpile_smoke`、それ以外は conservative な `not_started/not_started_placeholder` seed で出力されます。
- per-cell schema は fixed 済みで、required key は `backend` / `support_state` / `evidence_kind`、optional key は `details` / `evidence_ref` / `diagnostic_kind` です。
- docs page には seeded 2 次元 table を載せていますが、これは final support claim ではなく seed manifest の可視化です。
- backend ごとの reviewed state は follow-up bundle で埋めます。

## Source Of Truth

- matrix contract: [backend_parity_matrix_contract.py](/workspace/Pytra/src/toolchain/misc/backend_parity_matrix_contract.py)
- conformance summary handoff: [backend_conformance_summary_handoff_contract.py](/workspace/Pytra/src/toolchain/misc/backend_conformance_summary_handoff_contract.py)
- parity review contract: [backend_parity_review_contract.py](/workspace/Pytra/src/toolchain/misc/backend_parity_review_contract.py)
- rollout tier contract: [backend_parity_rollout_tier_contract.py](/workspace/Pytra/src/toolchain/misc/backend_parity_rollout_tier_contract.py)
- docs / release note / tooling handoff: [backend_parity_handoff_contract.py](/workspace/Pytra/src/toolchain/misc/backend_parity_handoff_contract.py)

## Maintenance Rule

- backend support status はこのページと tooling manifest を正本とし、release note 側には要約とリンクだけを載せます。
- unsupported lane は `fail_closed` / `not_started` / `experimental` のいずれかで記録し、silent fallback は認めません。
- representative / secondary / long-tail の rollout tier は rollout tier contract に従います。

## Tooling Export

- matrix manifest: [export_backend_parity_matrix_manifest.py](/workspace/Pytra/tools/gen/export_backend_parity_matrix_manifest.py)
- conformance summary manifest: [export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/tools/gen/export_backend_conformance_summary_handoff_manifest.py)
- parity review manifest: [export_backend_parity_review_manifest.py](/workspace/Pytra/tools/gen/export_backend_parity_review_manifest.py)
- handoff manifest: [export_backend_parity_handoff_manifest.py](/workspace/Pytra/tools/gen/export_backend_parity_handoff_manifest.py)

## Representative Seed Matrix

- cell は plain Markdown table で表示し、emoji と短い code で state / evidence を見せます。
- 現段階では `cpp` に加えて、direct transpile/build smoke で裏付けた representative / secondary / long-tail cell だけを reviewed seed に上げ、他 backend は conservative placeholder seed を維持しています。
- `🟩 BR`: supported / build_run_smoke
- `🟦 TS`: supported / transpile_smoke
- `⬜ NS`: not_started / not_started_placeholder
- `🟥 FC`: fail_closed / contract_guard or diagnostic_guard
- `🟨 EX`: experimental / preview_guard
- GitHub の Markdown render では `<style>` や inline style が sanitization で落ちるため、このページは CSS なしで読める table を使います。

<!-- BEGIN BACKEND PARITY MATRIX TABLE -->

| feature_id | fixture | cpp | rs | cs | js | ts | go | java | swift | kt | rb | lua | scala | php | nim |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| syntax.assign.tuple_destructure | test/fixtures/core/tuple_assign.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| syntax.expr.lambda | test/fixtures/core/lambda_basic.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| syntax.expr.list_comprehension | test/fixtures/collections/comprehension.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| syntax.control.for_range | test/fixtures/control/for_range.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| syntax.control.try_raise | test/fixtures/control/try_raise.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| syntax.oop.virtual_dispatch | test/fixtures/oop/inheritance_virtual_dispatch_multilang.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| builtin.iter.range | test/fixtures/control/for_range.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| builtin.iter.enumerate | test/fixtures/strings/enumerate_basic.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| builtin.iter.zip | test/fixtures/signature/ok_generator_tuple_target.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| builtin.type.isinstance | test/fixtures/oop/is_instance.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| builtin.bit.invert_and_mask | test/fixtures/typing/bitwise_invert_basic.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| stdlib.json.loads_dumps | test/fixtures/stdlib/json_extended.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| stdlib.pathlib.path_ops | test/fixtures/stdlib/pathlib_extended.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| stdlib.enum.enum_and_intflag | test/fixtures/stdlib/enum_extended.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| stdlib.argparse.parse_args | test/fixtures/stdlib/argparse_extended.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| stdlib.math.imported_symbols | test/fixtures/stdlib/pytra_std_import_math.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| stdlib.re.sub | test/fixtures/stdlib/re_extended.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |

<!-- END BACKEND PARITY MATRIX TABLE -->

## Current Relative-Import Coverage

- relative import の current coverage baseline は [relative_import_backend_coverage.py](/workspace/Pytra/src/toolchain/misc/relative_import_backend_coverage.py) と [check_relative_import_backend_coverage.py](/workspace/Pytra/tools/check/check_relative_import_backend_coverage.py) を正本にする。
- 現時点で `build_run_locked` なのは `cpp`、`transpile_smoke_locked` なのは `rs/cs/go/java/js/kotlin/lua/nim/php/ruby/scala/swift/ts` です。`go/nim/swift` は direct native emitter の function-body transpile smoke、`java/kotlin/scala` は JVM package bundle の `package_project_transpile`、`lua/php/ruby` は representative relative import alias rewrite の `native_emitter_function_body_transpile` を証跡 lane に固定しています。
- この欄は support claim ではなく verification coverage の handoff であり、non-C++ lane は representative smoke が lock されても full support 扱いにはしない。
- ordinary relative import の historical handoff は [20260312-p1-relative-import-longtail-support-implementation.md](../plans/archive/20260312-p1-relative-import-longtail-support-implementation.md) を参照する。historical bundle order は `locked_js_ts_smoke_bundle -> native_path_bundle -> jvm_package_bundle` のまま固定し、`java/kotlin/scala` は archived JVM bundle、`lua/php/ruby` は long-tail representative lane として `transpile_smoke_locked` baseline に残る。

## Current Relative-Wildcard-Import Coverage

- relative wildcard import の final handoff は [relative_wildcard_import_native_rollout_contract.py](/workspace/Pytra/src/toolchain/misc/relative_wildcard_import_native_rollout_contract.py) と [check_relative_wildcard_import_native_rollout_contract.py](/workspace/Pytra/tools/check/check_relative_wildcard_import_native_rollout_contract.py) を正本にする。
- `cpp` は representative `from .helper import *` を `build_run_locked + multi_file_build_run` に固定し、non-C++ native backend では `go/java/kotlin/lua/nim/php/ruby/scala/swift` を representative module-graph bundle の `transpile_smoke_locked + module_graph_bundle_transpile` に固定した。focused smoke lane は `go_relative_wildcard_import_rollout_smoke` / `java_relative_wildcard_import_rollout_smoke` / `kotlin_relative_wildcard_import_rollout_smoke` / `lua_relative_wildcard_import_rollout_smoke` / `nim_relative_wildcard_import_rollout_smoke` / `php_relative_wildcard_import_rollout_smoke` / `ruby_relative_wildcard_import_rollout_smoke` / `scala_relative_wildcard_import_rollout_smoke` / `swift_relative_wildcard_import_rollout_smoke` の 9 本で固定する。
- rollout bundle order は `native_path_bundle -> jvm_package_bundle -> longtail_native_bundle` のまま archive し、single-file `load_east3_document(...)` direct lane と unresolved / duplicate / root-escape wildcard case は引き続き `backend_specific_fail_closed` を維持する。
- この欄も support claim ではなく verification coverage handoff であり、今回の native rollout 対象外だった `rs/cs/js/ts` を full support とみなすものではない。
