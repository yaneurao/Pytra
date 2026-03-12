<a href="../../ja/language/backend-parity-matrix.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Backend Parity Matrix

This page is the canonical publish target for feature × backend support-state reporting.

## Canonical Source and Drill-Down

- Treat this page as the canonical source, and keep the C++ table as a drill-down at [./cpp/spec-support.md](./cpp/spec-support.md).
- The C++ support matrix only refines the cpp lane and does not redefine the cross-backend taxonomy.
- Update this page and the tooling contract first, then sync the C++ drill-down table.
- Cells are filled in representative -> secondary -> long_tail order.

## Current Implementation Phase

- The current matrix is at the `cell_seed_manifest` phase.
- The tooling manifest now carries row-level `backend_cells` seeds: `cpp` is emitted as `supported/build_run_smoke`, reviewed representative, secondary, and long-tail cells are promoted to `supported/transpile_smoke`, and the remaining backends stay on the conservative `not_started/not_started_placeholder` seed.
- The per-cell schema is fixed: required keys are `backend` / `support_state` / `evidence_kind`, and optional keys are `details` / `evidence_ref` / `diagnostic_kind`.
- The docs page now renders the seeded 2D table, but that table is still a seed-manifest view rather than a final support claim.
- The reviewed backend-by-backend states will be filled in follow-up bundles.

## Source Of Truth

- matrix contract: [backend_parity_matrix_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_matrix_contract.py)
- conformance summary handoff: [backend_conformance_summary_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_summary_handoff_contract.py)
- parity review contract: [backend_parity_review_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_review_contract.py)
- rollout tier contract: [backend_parity_rollout_tier_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_rollout_tier_contract.py)
- docs / release note / tooling handoff: [backend_parity_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_handoff_contract.py)

## Maintenance Rule

- Backend support status is published canonically through this page and the tooling manifests; release notes should only summarize the change and link back here.
- Unsupported lanes must be recorded as `fail_closed`, `not_started`, or `experimental`, with silent fallback forbidden.
- Representative / secondary / long-tail rollout order follows the rollout-tier contract.

## Tooling Export

- matrix manifest: [export_backend_parity_matrix_manifest.py](/workspace/Pytra/tools/export_backend_parity_matrix_manifest.py)
- conformance summary manifest: [export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/tools/export_backend_conformance_summary_handoff_manifest.py)
- parity review manifest: [export_backend_parity_review_manifest.py](/workspace/Pytra/tools/export_backend_parity_review_manifest.py)
- handoff manifest: [export_backend_parity_handoff_manifest.py](/workspace/Pytra/tools/export_backend_parity_handoff_manifest.py)

## Representative Seed Matrix

- Cells are rendered as an HTML grid with background color and compact status codes.
- At this stage `cpp` plus direct fixture-backed representative, secondary, and long-tail cells are reviewed seeds; the remaining backends are conservative placeholders.

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
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">syntax.oop.virtual_dispatch</td>
        <td class="fixture">test/fixtures/oop/inheritance_virtual_dispatch_multilang.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
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
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">builtin.type.isinstance</td>
        <td class="fixture">test/fixtures/oop/is_instance.py</td>
        <td class="cell supported-build" title="supported / build_run_smoke"><code>BR</code></td>
        <td class="cell supported-transpile" title="supported / transpile_smoke"><code>TS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
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
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">stdlib.pathlib.path_ops</td>
        <td class="fixture">test/fixtures/stdlib/pathlib_extended.py</td>
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
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">stdlib.enum.enum_and_intflag</td>
        <td class="fixture">test/fixtures/stdlib/enum_extended.py</td>
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
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
      <tr>
        <td class="feature">stdlib.argparse.parse_args</td>
        <td class="fixture">test/fixtures/stdlib/argparse_extended.py</td>
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
        <td class="cell not-started" title="not_started / not_started_placeholder"><code>NS</code></td>
      </tr>
    </tbody>
  </table>
</div>
<!-- END BACKEND PARITY MATRIX TABLE -->

## Current Relative-Import Coverage

- The current relative-import coverage baseline is published canonically through [relative_import_backend_coverage.py](/workspace/Pytra/src/toolchain/compiler/relative_import_backend_coverage.py) and [check_relative_import_backend_coverage.py](/workspace/Pytra/tools/check_relative_import_backend_coverage.py).
- Today `cpp` is `build_run_locked`, while `rs/cs/go/java/js/kotlin/lua/nim/php/ruby/scala/swift/ts` are `transpile_smoke_locked`. The evidence lane stays fixed as direct native-emitter function-body transpile smoke for `go/nim/swift`, as `package_project_transpile` for the JVM package bundle on `java/kotlin/scala`, and as the representative relative-import alias-rewrite lane for `lua/php/ruby`.
- This section is a verification-coverage handoff, not a support claim. Even after representative smoke is locked, non-C++ lanes do not become fully supported automatically.
- The next rollout handoff lives in [20260312-p1-relative-import-longtail-support-implementation.md](../plans/archive/20260312-p1-relative-import-longtail-support-implementation.md): the historical bundle order remains fixed as `locked_js_ts_smoke_bundle -> native_path_bundle -> jvm_package_bundle`. `java/kotlin/scala` stay in the archived JVM bundle / `transpile_smoke_locked` baseline, and `longtail_relative_import_support_rollout` is now closed at `bundle_state=locked_representative_smoke`. `lua/php/ruby` are the representative `transpile_smoke_locked` lanes with `native_emitter_function_body_transpile` evidence, the backend-local focused smoke lanes stay fixed as `lua_relative_import_support_rollout_smoke` / `php_relative_import_support_rollout_smoke` / `ruby_relative_import_support_rollout_smoke`, and the remaining rollout backends / next rollout bundle / next verification lane / follow-up rollout bundle / follow-up verification lane are all `none`. Wildcard relative import remains `backend_specific_fail_closed`.
