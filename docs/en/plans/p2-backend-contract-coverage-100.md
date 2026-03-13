# P2: fix backend contract coverage at 100% with bundle-based coverage tracking

Last updated: 2026-03-14

Related TODO:
- `docs/ja/todo/index.md` `ID: P2-BACKEND-CONTRACT-COVERAGE-100-01`

Background:
- The current `docs/ja/language/backend-parity-matrix.md` is the canonical support matrix for representative features. It is not a full inventory of every test suite.
- The support matrix rows come from a curated `feature_id + representative_fixture` inventory, while `test/unit/backends/*` already exercises fixtures such as `property_method_call` and `list_bool_index` across many backends. That leaves a gap between real coverage and what the docs show.
- `test/ir` is an EAST3(JSON)-driven backend-only smoke suite, `test/integration` is a backend-specific integration suite, and `test/transpile` contains artifact-comparison fixtures, but those suites are not directly attached to the parity-matrix row taxonomy.
- As a result, the current docs/tooling cannot answer, in one place, which large test bundles verify which `feature/lane/backend` cells, which already-tested fixtures are still unpublished, or how close coverage is to 100%.

Objective:
- Keep the support matrix as the canonical `feature x backend support-state` claim, but add a separate bundle-based coverage matrix/inventory for verification coverage.
- Define coverage at 100% as contract coverage, not line/branch coverage: every `feature x required_lane x backend` must belong to at least one coverage bundle.
- Connect `test/unit`, `test/ir`, `test/integration`, and `test/transpile` to an explicit bundle taxonomy so "already tested but not visible" becomes rare.

In scope:
- Representative feature/lane contracts in `backend_feature_contract_inventory.py` and `backend_conformance_inventory.py`
- `docs/ja|en/language/backend-parity-matrix.md` plus future coverage docs/exports
- `test/unit/common`, `test/unit/backends`, `test/ir`, `test/integration`, and `test/transpile`
- Coverage bundle taxonomy, manifest, checker, export tooling, and mirrored docs
- Inventorying fixtures that already have multi-backend smoke coverage but are not yet promoted into the representative inventory

Out of scope:
- Making every backend feature fully supported in one step
- Reaching 100% Python line coverage or branch coverage
- Redesigning the existing support-state taxonomy (`supported`, `fail_closed`, `not_started`, `experimental`)
- Mixing backend-specific integration suites into cross-backend support claims

Acceptance criteria:
- The role split between the support matrix and the coverage matrix is explicit in docs and tooling contracts.
- For contract coverage, every `feature_id x required_lane x backend` cell maps to at least one coverage bundle or an explicit non-applicable / backend-specific lane rule.
- The coverage bundle taxonomy has at least `frontend`, `emit`, `runtime`, `import_package`, `ir2lang`, and `integration` style responsibilities, and each bundle records its source suite, harness, and evidence lane.
- The live suites under `test/unit`, `test/ir`, `test/integration`, and `test/transpile` are either connected to the coverage taxonomy or explicitly documented as intentional exclusions.
- Multi-backend smoke fixtures such as `property_method_call` and `list_bool_index` are either promoted into the support matrix or recorded as coverage-only representatives.
- A checker fails when a new feature or suite lands without a coverage-bundle mapping for the required `feature/lane/backend` cells.

Validation commands (planned):
- `python3 tools/check_todo_priority.py`
- `rg -n "property_method_call|list_bool_index|test/ir|test/integration|test/transpile|support matrix|coverage matrix" src tools test docs -g '!**/archive/**'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_*coverage*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends -p 'test_py2*_smoke.py'`
- `python3 tools/check_ir2lang_smoke.py`
- `git diff --check`

## Coverage Bundle Policy

- `support_matrix`: publishes representative feature support claims. It answers support-state questions and does not try to be a full suite inventory.
- `coverage_matrix`: publishes verification coverage. It shows which bundle verifies each `feature x lane x backend` cell.
- `frontend` bundle: owns parse, east, and east3-lowering coverage.
- `emit` bundle: owns backend emitter source-generation smoke/compare coverage.
- `runtime` bundle: owns representative runtime parity and stdlib runtime strategy coverage.
- `import_package` bundle: owns relative-import, package-layout, and multi-file ownership coverage.
- `ir2lang` bundle: owns frontend-independent backend-only smoke driven from `test/ir`.
- `integration` bundle: owns backend-specific execution, GC, and linker/integration coverage from suites such as `test/integration`.

## Definition Of 100%

- 100% means contract coverage for `feature x required_lane x backend`, not line or branch coverage.
- `required_lane` comes from the conformance inventory lane policy.
- Each coverage cell must fix at least `bundle_id`, `suite_kind`, `harness_kind`, or `evidence_ref`.
- Even when a support claim is not `supported`, the coverage claim may still point to `fail_closed`, `not_started`, or `experimental` verification bundles.
- Backend-specific integration stays out of the support matrix and is modeled as backend-specific coverage lanes in the coverage matrix.

## Breakdown

- [ ] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S1-01] Inventory the live representative contracts plus `test/unit`, `test/ir`, `test/integration`, and `test/transpile`, and classify candidate coverage bundles.
- [ ] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S1-02] Freeze the role split between the support matrix and the coverage matrix, together with the definition of 100% contract coverage, in docs/tooling contracts.
- [ ] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S2-01] Introduce the coverage bundle taxonomy plus a machine-readable manifest/checker so `feature x lane x backend` bundle ownership becomes verifiable.
- [ ] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S2-02] Connect `test/unit`, `test/ir`, `test/integration`, and `test/transpile` to the coverage bundles and make unmapped suites explicit.
- [ ] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S2-03] Classify already-used multi-backend fixtures that are missing from the support matrix into promotion candidates versus coverage-only representatives.
- [ ] [ID: P2-BACKEND-CONTRACT-COVERAGE-100-01-S3-01] Sync docs, exports, checkers, and the English mirror so new features/suites fail fast when coverage mapping is missing.

Decision log:
- 2026-03-14: Opened after confirming that `backend-parity-matrix` is a representative support-claim page rather than a full suite inventory, so bundle-based coverage tracking needs to exist as a separate canonical surface.
