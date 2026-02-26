# P3: Migrate Java Backend to Direct EAST3 Native Generation (Remove Sidecar)

Last updated: 2026-02-26

Related TODO:
- `ID: P3-JAVA-NATIVE-01` in `docs-ja/todo/index.md`

Background:
- Current `py2java.py` generates sidecar JavaScript via `transpile_to_js`, and Java output is a Node bridge wrapper.
- `sample/java` therefore tends to be thin bridge-oriented output, making Java-native backend quality hard to evaluate.
- From the user viewpoint, "choosing Java but not getting actual Java implementation output" is confusing, so migration to direct EAST3 generation is required.

Goal:
- Move Java backend to direct `EAST3 -> Java native emitter` generation and remove sidecar JS dependency from the default path.

In scope:
- `src/py2java.py` (generation path switch; stop default sidecar output)
- `src/hooks/java/emitter/` (native emitter implementation)
- `tools/check_py2java_transpile.py` / `test/unit/test_py2java_smoke.py` (verification updates)
- Regeneration path and related docs for `sample/java`

Out of scope:
- Simultaneous native migration of Go/Swift/Kotlin backends
- Full Java runtime redesign (except minimal required API additions)
- Advanced optimization for Java backend (correctness and parity first)

Acceptance criteria:
- Default `py2java.py` does not generate `.js` sidecar and outputs Java code runnable without the bridge.
- For key `sample/py` cases, `java` execution output matches Python baseline (verifiable through existing parity path).
- `sample/java` output is replaced from preview summaries to native executable logic.
- Sidecar path is removed or reduced to explicit opt-in compatibility mode; default is fixed native.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2java_transpile.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2java_*.py'`
- `python3 tools/runtime_parity_check.py --case-root sample --targets java --all-samples --ignore-unstable-stdout`

Decision log:
- 2026-02-26: Initial draft created. Added implementation plan for staged removal of Java sidecar bridge dependency.
- 2026-02-26: Per user instruction, lowered priority and updated Java native migration task identifiers to the low-priority band.
- 2026-02-26: [ID: `P3-JAVA-NATIVE-01-S1-01`] Added `docs-ja/spec/spec-java-native-backend.md` (translation: `docs/spec/spec-java-native-backend.md`) to formalize input EAST3 responsibility, fail-closed behavior, runtime boundary, and preview-vs-native diffs.
- 2026-02-26: [ID: `P3-JAVA-NATIVE-01-S1-02`] Added `src/hooks/java/emitter/java_native_emitter.py` with native skeleton emission for `Module/FunctionDef/ClassDef` (body placeholder by design), then added minimal-route tests in `test_py2java_smoke.py`; no regression in `tools/check_py2java_transpile.py`.
- 2026-02-26: [ID: `P3-JAVA-NATIVE-01-S1-03`] Added `--java-backend {native,sidecar}` in `py2java.py`, switched default generation to native (`transpile_to_java_native`), and restricted sidecar output to explicit compatibility mode (`--java-backend sidecar`). Updated CLI smoke tests for native default and sidecar compatibility checks.
- 2026-02-26: [ID: `P3-JAVA-NATIVE-01-S2-01`] Expanded `java_native_emitter` body lowering for `Return/Expr/AnnAssign/Assign/AugAssign/If/ForCore` and core expressions (`Name/Constant/UnaryOp/BinOp/Compare/BoolOp/Attribute/Call`), and added `if_else` / `for_range` lowering checks in `test_py2java_smoke.py`.
- 2026-02-26: [ID: `P3-JAVA-NATIVE-01-S2-01`] Improved basic OOP lowering consistency: map `self` references to `this`, lower class-name calls to constructor form (`new ClassName(...)`), and preserve unknown identifier annotations as class types instead of collapsing to `Object`; extended `inheritance` expectations in `test_py2java_smoke.py`.
- 2026-02-26: [ID: `P3-JAVA-NATIVE-01-S2-01`] Added simple return-flow analysis (`_block_guarantees_return`) to avoid duplicate fallback `return` insertion when both `if/else` branches already return; locked with `test_py2java_smoke.py` assertion that `if_else` output does not include `return 0L;`.

## Breakdown

- [x] [ID: P3-JAVA-NATIVE-01-S1-01] Document Java backend contract (responsibility for input EAST3 nodes, fail-closed behavior on unsupported nodes, runtime boundary) and clarify diff from preview output.
- [x] [ID: P3-JAVA-NATIVE-01-S1-02] Add native emitter skeleton in `src/hooks/java/emitter` and pass minimal executable route for module/function/class.
- [x] [ID: P3-JAVA-NATIVE-01-S1-03] Add backend switch wiring in `py2java.py`, make native the default, and isolate legacy sidecar into compatibility mode.
- [ ] [ID: P3-JAVA-NATIVE-01-S2-01] Implement native emitter support for expressions/statements (arithmetic, conditionals, loops, function calls, built-in primitive types) and pass early `sample/py` cases.
- [ ] [ID: P3-JAVA-NATIVE-01-S2-02] Connect class/instance/isinstance paths and runtime hooks to native route and pass OOP cases.
- [ ] [ID: P3-JAVA-NATIVE-01-S2-03] Provide minimal compatibility for `import math` and image runtime calls (`png`/`gif`) to handle practical sample cases.
- [ ] [ID: P3-JAVA-NATIVE-01-S3-01] Pass `check_py2java_transpile`, unit smoke, and parity in native-default mode; lock regression detection.
- [ ] [ID: P3-JAVA-NATIVE-01-S3-02] Regenerate `sample/java` and replace preview summary outputs with native implementation outputs.
- [ ] [ID: P3-JAVA-NATIVE-01-S3-03] Update Java descriptions in `docs-ja/how-to-use.md` / `docs-ja/spec/spec-import.md` from sidecar assumptions and sync operational instructions.
