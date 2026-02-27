# P3: Migrate Go/Swift/Kotlin Backends to Direct EAST3 Native Generation (Remove Sidecar)

Last updated: 2026-02-26

Related TODO:
- `ID: P3-GSK-NATIVE-01` in `docs/ja/todo/index.md`

Background:
- Current `py2go.py` / `py2swift.py` / `py2kotlin.py` generate sidecar JavaScript via `transpile_to_js`, and each target emits a Node bridge wrapper.
- As a result, `sample/go`, `sample/swift`, and `sample/kotlin` do not clearly show native backend code quality, and language-specific optimization opportunities are hard to apply.
- In the same direction as Java native migration (`P3-JAVA-NATIVE-01`), non-native backends need staged shrink/removal.

Goal:
- Move Go / Swift / Kotlin backends to direct `EAST3 -> <lang> native emitter` paths and remove JS sidecar bridge from the default path.

In scope:
- `src/py2go.py` / `src/py2swift.py` / `src/py2kotlin.py`
- `src/hooks/go/emitter/` / `src/hooks/swift/emitter/` / `src/hooks/kotlin/emitter/`
- `tools/check_py2go_transpile.py` / `tools/check_py2swift_transpile.py` / `tools/check_py2kotlin_transpile.py`
- Regeneration path and related docs for `sample/go`, `sample/swift`, `sample/kotlin`

Out of scope:
- Java backend (tracked by `P3-JAVA-NATIVE-01`)
- Responsibility changes in C++/Rust/C#/JS/TS backends
- Advanced optimization introduction (correctness and native parity first)

Acceptance criteria:
- Default `py2go.py` / `py2swift.py` / `py2kotlin.py` no longer generates `.js` sidecar.
- Each language backend satisfies stdout parity with Python for key `sample/py` cases.
- `sample/<lang>` output is replaced by native implementations, not preview bridge wrappers.
- Legacy sidecar path is removed or downgraded to explicit opt-in compatibility mode.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2go_transpile.py`
- `python3 tools/check_py2swift_transpile.py`
- `python3 tools/check_py2kotlin_transpile.py`
- `python3 tools/runtime_parity_check.py --case-root sample --targets go,swift,kotlin --all-samples --ignore-unstable-stdout`

Decision log:
- 2026-02-26: Initial draft created. Added low-priority migration plan to native-ize Go/Swift/Kotlin sidecar backends.

## Breakdown

- [ ] [ID: P3-GSK-NATIVE-01-S1-01] Define common migration contract (EAST3 node coverage, fail-closed on unsupported nodes, runtime boundary).
- [ ] [ID: P3-GSK-NATIVE-01-S1-02] Finalize sidecar compatibility isolation across 3 languages (default native / opt-in legacy).
- [ ] [ID: P3-GSK-NATIVE-01-S2-01] Implement Go native emitter skeleton and default switch in `py2go.py`.
- [ ] [ID: P3-GSK-NATIVE-01-S2-02] Implement base Go support for expressions/statements/classes and pass early `sample/py` cases.
- [ ] [ID: P3-GSK-NATIVE-01-S3-01] Implement Swift native emitter skeleton and default switch in `py2swift.py`.
- [ ] [ID: P3-GSK-NATIVE-01-S3-02] Implement base Swift support for expressions/statements/classes and pass early `sample/py` cases.
- [ ] [ID: P3-GSK-NATIVE-01-S4-01] Implement Kotlin native emitter skeleton and default switch in `py2kotlin.py`.
- [ ] [ID: P3-GSK-NATIVE-01-S4-02] Implement base Kotlin support for expressions/statements/classes and pass early `sample/py` cases.
- [ ] [ID: P3-GSK-NATIVE-01-S5-01] Pass transpile/smoke/parity regressions in native-default mode for all 3 languages and update CI paths.
- [ ] [ID: P3-GSK-NATIVE-01-S5-02] Regenerate `sample/go`, `sample/swift`, `sample/kotlin` and sync docs.
