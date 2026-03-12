# Backend Parity Matrix

<a href="../../en/language/backend-parity-matrix.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

このページは、feature × backend の support state を公開する canonical publish target です。

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

- matrix contract: [backend_parity_matrix_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_matrix_contract.py)
- conformance summary handoff: [backend_conformance_summary_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_summary_handoff_contract.py)
- parity review contract: [backend_parity_review_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_review_contract.py)
- rollout tier contract: [backend_parity_rollout_tier_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_rollout_tier_contract.py)
- docs / release note / tooling handoff: [backend_parity_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_handoff_contract.py)

## Maintenance Rule

- backend support status はこのページと tooling manifest を正本とし、release note 側には要約とリンクだけを載せます。
- unsupported lane は `fail_closed` / `not_started` / `experimental` のいずれかで記録し、silent fallback は認めません。
- representative / secondary / long-tail の rollout tier は rollout tier contract に従います。

## Tooling Export

- matrix manifest: [export_backend_parity_matrix_manifest.py](/workspace/Pytra/tools/export_backend_parity_matrix_manifest.py)
- conformance summary manifest: [export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/tools/export_backend_conformance_summary_handoff_manifest.py)
- parity review manifest: [export_backend_parity_review_manifest.py](/workspace/Pytra/tools/export_backend_parity_review_manifest.py)
- handoff manifest: [export_backend_parity_handoff_manifest.py](/workspace/Pytra/tools/export_backend_parity_handoff_manifest.py)

## Representative Seed Matrix

- cell は HTML grid で表示し、背景色と短い code で state を見せます。
- 現段階では `cpp` に加えて、direct transpile/build smoke で裏付けた representative / secondary / long-tail cell だけを reviewed seed に上げ、他 backend は conservative placeholder seed を維持しています。

<style>
  .backend-parity-grid-wrap { overflow-x: auto; margin: 1rem 0; }
  .backend-parity-grid {
    border-collapse: collapse;
    table-layout: fixed;
    min-width: 1200px;
    font-size: 0.8rem;
    line-height: 1.25;
  }
  .backend-parity-grid th,
  .backend-parity-grid td {
    border: 1px solid #cbd5e1;
    padding: 0.45rem 0.35rem;
    text-align: center;
    vertical-align: middle;
  }
  .backend-parity-grid th {
    background: #e2e8f0;
    color: #111827;
    font-weight: 700;
  }
  .backend-parity-grid .feature,
  .backend-parity-grid .fixture {
    background: #ffffff;
    color: #111827;
    text-align: left;
    white-space: nowrap;
  }
  .backend-parity-grid .cell {
    font-weight: 700;
    min-width: 3.4rem;
  }
  .backend-parity-grid .cell code {
    background: transparent;
    color: inherit;
    font-weight: 700;
    padding: 0;
  }
  .backend-parity-grid .supported-build { background: #166534; color: #ffffff; }
  .backend-parity-grid .supported-transpile { background: #bbf7d0; color: #14532d; }
  .backend-parity-grid .not-started { background: #e5e7eb; color: #475569; }
  .backend-parity-grid .fail-closed { background: #fee2e2; color: #991b1b; }
  .backend-parity-grid .experimental { background: #fef3c7; color: #92400e; }
  .backend-parity-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 0.75rem 0 1rem;
  }
  .backend-parity-legend span {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.2rem 0.5rem;
    border: 1px solid #cbd5e1;
    border-radius: 999px;
    font-size: 0.82rem;
  }
  .backend-parity-legend code {
    background: transparent;
    padding: 0;
    font-weight: 700;
  }
</style>

<div class="backend-parity-legend">
  <span><code>BR</code> supported / build_run_smoke</span>
  <span><code>TS</code> supported / transpile_smoke</span>
  <span><code>NS</code> not_started / not_started_placeholder</span>
</div>

<!-- BEGIN BACKEND PARITY MATRIX TABLE -->
<div class="backend-parity-grid-wrap">
  <table class="backend-parity-grid">
    <thead>
      <tr>
        <th>feature_id</th>
        <th>fixture</th>
        <th>cpp</th>
        <th>rs</th>
        <th>cs</th>
        <th>js</th>
        <th>ts</th>
        <th>go</th>
        <th>java</th>
        <th>swift</th>
        <th>kt</th>
        <th>rb</th>
        <th>lua</th>
        <th>scala</th>
        <th>php</th>
        <th>nim</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="feature">syntax.assign.tuple_destructure</td>
        <td class="fixture">test/fixtures/core/tuple_assign.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">syntax.expr.lambda</td>
        <td class="fixture">test/fixtures/core/lambda_basic.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">syntax.expr.list_comprehension</td>
        <td class="fixture">test/fixtures/collections/comprehension.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">syntax.control.for_range</td>
        <td class="fixture">test/fixtures/control/for_range.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
      </tr>
      <tr>
        <td class="feature">syntax.control.try_raise</td>
        <td class="fixture">test/fixtures/control/try_raise.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">syntax.oop.virtual_dispatch</td>
        <td class="fixture">test/fixtures/oop/inheritance_virtual_dispatch_multilang.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">builtin.iter.range</td>
        <td class="fixture">test/fixtures/control/for_range.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
      </tr>
      <tr>
        <td class="feature">builtin.iter.enumerate</td>
        <td class="fixture">test/fixtures/strings/enumerate_basic.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">builtin.iter.zip</td>
        <td class="fixture">test/fixtures/signature/ok_generator_tuple_target.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">builtin.type.isinstance</td>
        <td class="fixture">test/fixtures/oop/is_instance.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">builtin.bit.invert_and_mask</td>
        <td class="fixture">test/fixtures/typing/bitwise_invert_basic.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
      </tr>
      <tr>
        <td class="feature">stdlib.json.loads_dumps</td>
        <td class="fixture">test/fixtures/stdlib/json_extended.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">stdlib.pathlib.path_ops</td>
        <td class="fixture">test/fixtures/stdlib/pathlib_extended.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">stdlib.enum.enum_and_intflag</td>
        <td class="fixture">test/fixtures/stdlib/enum_extended.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">stdlib.argparse.parse_args</td>
        <td class="fixture">test/fixtures/stdlib/argparse_extended.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">stdlib.math.imported_symbols</td>
        <td class="fixture">test/fixtures/stdlib/pytra_std_import_math.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">stdlib.re.sub</td>
        <td class="fixture">test/fixtures/stdlib/re_extended.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
    </tbody>
  </table>
</div>
<!-- END BACKEND PARITY MATRIX TABLE -->

## Current Relative-Import Coverage

- relative import の current coverage baseline は [relative_import_backend_coverage.py](/workspace/Pytra/src/toolchain/compiler/relative_import_backend_coverage.py) と [check_relative_import_backend_coverage.py](/workspace/Pytra/tools/check_relative_import_backend_coverage.py) を正本にする。
- 現時点で `build_run_locked` なのは `cpp`、`transpile_smoke_locked` なのは `rs/cs/go/java/js/kotlin/lua/nim/php/ruby/scala/swift/ts` です。`go/nim/swift` は direct native emitter の function-body transpile smoke、`java/kotlin/scala` は JVM package bundle の `package_project_transpile`、`lua/php/ruby` は representative relative import alias rewrite の `native_emitter_function_body_transpile` を証跡 lane に固定しています。
- この欄は support claim ではなく verification coverage の handoff であり、non-C++ lane は representative smoke が lock されても full support 扱いにはしない。
- next rollout handoff は [20260312-p1-relative-import-longtail-support-implementation.md](../plans/archive/20260312-p1-relative-import-longtail-support-implementation.md) を参照し、historical bundle order は `locked_js_ts_smoke_bundle -> native_path_bundle -> jvm_package_bundle` のまま固定する。`java/kotlin/scala` は archived JVM bundle として `transpile_smoke_locked` baseline に移り、`longtail_relative_import_support_rollout` は `bundle_state=locked_representative_smoke` で閉じた。`lua/php/ruby` は `native_emitter_function_body_transpile` を evidence lane にした `transpile_smoke_locked` representative lane、focused smoke lane は `lua_relative_import_support_rollout_smoke` / `php_relative_import_support_rollout_smoke` / `ruby_relative_import_support_rollout_smoke` に固定し、remaining rollout backends / next rollout bundle / next verification lane / followup rollout bundle / followup verification lane はすべて `none` とする。wildcard relative import は引き続き `backend_specific_fail_closed` として残す。
