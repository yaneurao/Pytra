# P1: Comment fidelity policy across all languages (generated comments prohibited)

Last updated: 2026-02-28

Related TODO:
- `ID: P1-COMMENT-FIDELITY-01` in `docs/ja/todo/index.md`

Background:
- Current generated code mixes emitter-specific comments that do not exist in source (`Auto-generated` / `Runtime helpers are provided` / `TypeScript preview` / `TODO: unsupported` / `pass` replacement comments).
- Meanwhile, top-of-source comments are missing on some backends, making comment fidelity inconsistent between backends.
- Without a clear contract that "only source-derived comments are allowed," the same drift will recur when adding future emitters.

Goal:
- Enforce "output only comments derived from source" across all backends.
- Completely ban emitter-specific explanatory comments / unsupported-TODO comments, and unify unsupported handling to fail-closed (exception).
- Keep comment-output regressions continuously detectable with tests and check tools.

In scope:
- `src/hooks/*/emitter/*.py` (`cpp/rs/cs/js/ts/go/java/swift/kotlin/ruby/lua`)
- `src/py2*.py` (only necessary path updates)
- `test/unit/test_py2*smoke.py`
- (if needed) `tools/check_comment_fidelity.py`
- `sample/*` regeneration path

Out of scope:
- Changing translation/formatting rules of comment wording
- Full redesign of docstring handling
- Non-comment code formatting differences (line breaks/whitespace only)

Acceptance criteria:
- Output code does not include emitter-specific fixed comments (`Auto-generated` / `Runtime helpers are provided` / `preview` / `TODO: unsupported` / `pass` comments).
- Source top comments and pre-statement comments (`module_leading_trivia` / `leading_trivia`) are emitted without omission on supported backends.
- `pass` is represented as each language's no-op statement, or omitted when unnecessary, not as comments.
- Unsupported syntax halts with exceptions (fail-closed), not comment embedding.
- Comment-fidelity regressions pass on smoke tests for major backends.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2*smoke.py' -v`
- `python3 tools/regenerate_samples.py --langs cpp,rs,cs,js,ts,go,java,swift,kotlin,ruby,lua --force`

Decision log:
- 2026-02-28: Per user request, opened `P1-COMMENT-FIDELITY-01` with policy "across all languages, prohibit output of comments absent in source, and force source-comment reflection."
- 2026-02-28: Cross-backend inventory with `rg` extracted remaining fixed-comment output points and finalized the forbidden-pattern list (`P1-COMMENT-FIDELITY-01-S1-01` complete).
- 2026-02-28: Finalized contract to limit allowed comment sources to `module_leading_trivia` / `leading_trivia`, and fail-closed policy to stop with exceptions instead of comment embedding when unsupported (`P1-COMMENT-FIDELITY-01-S1-02` complete).
- 2026-02-28: Removed fixed-comment paths in `ts/go/java/swift/kotlin/ruby/lua`, replaced `pass` with no-op statements, and unified unsupported handling to exceptions. Confirmed regressions with 183 passing `test_py2*smoke.py` cases (`P1-COMMENT-FIDELITY-01-S2-01` complete).
- 2026-02-28: Replaced `pass` comment paths in `cpp/rs/cs/js` with no-op statements (`;` / `();`) and unified `unsupported` / `invalid` comment paths to exception stop. Confirmed regressions with passing `test_py2cpp/rs/cs/js_smoke.py` (84 cases) (`P1-COMMENT-FIDELITY-01-S2-02` complete).
- 2026-02-28: Introduced shared forbidden-comment checks into all `test_py2*smoke.py`, and pinned source-comment propagation with `sample/01` or language-specific fixtures. Confirmed pass for `python3 -m unittest discover -s test/unit -p 'test_py2*smoke.py'` (188 cases) (`P1-COMMENT-FIDELITY-01-S3-01` complete).
- 2026-02-28: Regenerated `sample/*` for all backends (`regen=184` / `fail=14` due to unsupported Lua cases), then machine-checked forbidden fixed-comment patterns and confirmed zero occurrences. Also reconfirmed regression with `test_py2*smoke.py` passing (188 cases) (S3-02 complete).

## S1-01 Inventory results (forbidden fixed-comment patterns)

Forbidden patterns:
- `pass` replacement comments (`// pass`, `# pass`, `-- pass`, `/* pass */`)
- Comments that hide unsupported syntax (`unsupported ...`, `TODO: unsupported ...`, `invalid ...`)
- Generator-derived banners (`Auto-generated ...`, `Runtime helpers are provided ...`, `TypeScript preview ...`)
- Control explanation comments (for example `// __main__ guard`)

Detected locations in major backends:
- `cpp`: `src/hooks/cpp/emitter/cpp_emitter.py`, `src/hooks/cpp/emitter/stmt.py` (`/* pass */`, `/* unsupported ... */`, `/* invalid ... */`)
- `rs`: `src/hooks/rs/emitter/rs_emitter.py` (`// pass`, `// unsupported ...`)
- `cs`: `src/hooks/cs/emitter/cs_emitter.py` (`// pass`, `// unsupported ...`)
- `js`: `src/hooks/js/emitter/js_emitter.py` (`// pass`, `// unsupported ...`, `// __main__ guard`)
- `ts`: `src/hooks/ts/emitter/ts_emitter.py` (preview/TODO fixed comments)
- `go`: `src/hooks/go/emitter/go_native_emitter.py` (`// TODO: unsupported ...`, `// pass`, `// Auto-generated ...`)
- `java`: `src/hooks/java/emitter/java_native_emitter.py` (`// TODO: unsupported ...`, `// pass`, `// Auto-generated ...`)
- `swift`: `src/hooks/swift/emitter/swift_native_emitter.py` (`// TODO: unsupported ...`, `// pass`, `// Auto-generated ...`)
- `kotlin`: `src/hooks/kotlin/emitter/kotlin_native_emitter.py` (`// TODO: unsupported ...`, `// pass`, `// Auto-generated ...`)
- `ruby`: `src/hooks/ruby/emitter/ruby_native_emitter.py` (`# TODO: unsupported ...`, `# pass`, `# Auto-generated ...`)
- `lua`: `src/hooks/lua/emitter/lua_native_emitter.py` (`-- pass`, `-- Auto-generated ...`)

Auxiliary generation paths (also cleanup targets at the same time):
- `AUTO-GENERATED` banners in `src/hooks/cpp/header/cpp_header.py`, `src/hooks/cpp/multifile/cpp_multifile.py`, and `src/hooks/cpp/runtime_emit/cpp_runtime_emit.py`.

## S1-02 Comment-output contract (explicit)

Scope:
- "Body code corresponding to input Python source" generated by `src/hooks/*/emitter/*.py`.

Allowed comment output:
- Only comments included in `east_doc["module_leading_trivia"]`.
- Only comments included in `stmt["leading_trivia"]`.
- Output format may be converted to each language's comment syntax, but text content must be limited to source-derived comments.

Forbidden comment output:
- Emitter-specific explanations (`Auto-generated`, `preview`, `Runtime helpers are provided`, etc.).
- Comments that hide unsupported syntax (`TODO: unsupported ...`, `unsupported ...`, `invalid ...`).
- `pass` replacement comments (`// pass`, `# pass`, `-- pass`, `/* pass */`).
- Control explanation comments (for example `// __main__ guard`).

Fail-closed policy:
- If unsupported syntax or invalid node shapes are detected, stop with `RuntimeError` / `ValueError` without outputting comments.
- Convert `pass` without outputting comments into language no-op statements (for example `;` / `pass` / `_ = _`) or omit when contextually unnecessary.
- Fallback by TODO comments is prohibited; unsupported cases must be surfaced explicitly as failures.

Notes:
- Banners in auxiliary generated files such as `src/hooks/cpp/header/*` and `multifile` are outside the primary scope of this contract, but will be included later under separate IDs.

## Breakdown

- [x] [ID: P1-COMMENT-FIDELITY-01-S1-01] Inventory fixed comment / `TODO` / `pass` comment output points in all emitters and pin forbidden-pattern list.
- [x] [ID: P1-COMMENT-FIDELITY-01-S1-02] Specify comment-output contract (allowed sources: only `module_leading_trivia` / `leading_trivia`) and explicitly document fail-closed policy.
- [x] [ID: P1-COMMENT-FIDELITY-01-S2-01] Remove fixed-comment output from `ts/go/java/swift/kotlin/ruby/lua` and unify to source-comment propagation only.
- [x] [ID: P1-COMMENT-FIDELITY-01-S2-02] Replace `pass` / unsupported comment paths in `cpp/rs/cs/js` with no-op or exceptions and move implementation to no generated comments.
- [x] [ID: P1-COMMENT-FIDELITY-01-S3-01] Add forbidden-comment checks and source-comment reflection tests to all `test_py2*smoke.py` and pin regressions.
- [x] [ID: P1-COMMENT-FIDELITY-01-S3-02] Regenerate `sample/*` and validate diffs to confirm no fixed comments remain in outputs for all languages.
