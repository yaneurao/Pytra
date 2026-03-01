# P3: Roll Out Container Reference-Management Model to non-C++ Backends

Last updated: 2026-03-01

Related TODO:
- `ID: P3-MULTILANG-CONTAINER-REF-01` in `docs/ja/todo/index.md`

Background:
- In the C++ backend, `cpp_list_model=pyobj` adopts a policy that reference-manages containers at `object` boundaries while reducing typed and non-escape paths to value types.
- In non-C++ backends, memory models and container implementations are split per language, and the equivalent policy ("dynamic boundaries use reference management, typed known non-escape paths use value types") is not explicitly handled.
- This difference causes variance in output quality, optimization behavior, and maintainability, reducing design consistency across backends.

Objective:
- Roll out the same abstract policy used in C++ to non-C++ backends (`rs/cs/js/ts/go/java/kotlin/swift/ruby/lua`).
- The policy is not "port RC implementation everywhere," but "unify reference-management boundary spec + common typed/non-escape value-reduction rules."

Scope:
- Spec/IR layer: `src/pytra/compiler/east_parts/*` (propagation of container ownership-form metadata)
- Backends: `src/hooks/{rs,cs,js,ts,go,java,kotlin,swift,ruby,lua}/emitter/*`
- Runtime support: `src/runtime/{rs,cs,go,java,kotlin,swift,ruby,lua}/**` (only where needed)
- Validation:
  - `test/unit/test_*emitter*.py`
  - `tools/runtime_parity_check.py` (with target backend selection)
  - Regenerated diffs in `sample/*`

Out of scope:
- Additional redesign for C++ backend (full revamp of existing `cpp_list_model`)
- New PHP backend addition
- Whole selfhost-completion task (this plan is limited to container reference-management policy)

Acceptance Criteria:
- A common spec for non-C++ backends around "reference-management boundary / value reduction" is documented, and IR metadata contract is defined.
- Pilot implementation is complete in at least `rs` + one GC backend, and locked by regression tests.
- Rollout steps and blockers for remaining backends are trackable as TODO child tasks.
- Major sample/parity cases confirm non-regressive behavior.

Validation Commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_*emitter*.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py --case-root sample --targets rs,cs,go,java,kotlin,swift,ruby,lua`
- `python3 tools/check_todo_priority.py`

Breakdown:
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-01] Inventory current container ownership models by backend (value/reference/GC/ARC) and create a gap matrix.
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S1-02] Specify common terms and judgment rules for "reference-management boundary", "typed/non-escape reduction", and "escape conditions".
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-01] Create minimal extension design to retain/propagate container ownership hints in EAST3 node metadata.
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S2-02] Define backend-neutral ownership decision APIs available in `CodeEmitter` base.
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-01] Implement pilot in Rust backend and add split between `object` boundary and typed value paths.
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-02] Implement pilot in a GC backend (Java or Kotlin) and verify reduction under the same rules.
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S3-03] Add regression tests for the two pilot backends (unit + sample fragments) and lock recurrence detection.
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-01] Roll out sequentially to `cs/js/ts/go/swift/ruby/lua` and absorb runtime-dependency differences per backend.
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S4-02] Run parity/smoke to confirm non-regression, and record unmet items separately as blockers.
- [ ] [ID: P3-MULTILANG-CONTAINER-REF-01-S5-01] Add operation rules (reference-management boundary and rollback procedure) to `docs/ja/how-to-use.md` and backend specs.

Decision Log:
- 2026-03-01: Per user request, newly created P3 plan to roll out the container reference-management policy already adopted in C++ to non-C++ backends.
- 2026-03-01: Chosen policy is not "force-port `rc` to each language," but "unify abstract rules: dynamic boundaries use reference management; typed known non-escape paths use value types."
