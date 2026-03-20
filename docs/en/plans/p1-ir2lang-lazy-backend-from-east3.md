# P1: Introduce `ir2lang.py` (Direct EAST3 JSON Input + Target Lazy Import)

Last updated: 2026-03-03

Related TODO:
- `ID: P1-IR2LANG-LAZY-EMIT-01` in `docs/ja/todo/index.md`

Background:
- In backend regressions for `test/` and `sample/`, running `py -> EAST3` every time is costly.
- We want backend-only regressions, but current paths still depend on frontend routes (`py2x.py`), so responsibility separation is weak.
- User requirement: a script that directly converts from EAST3 in `test/ir` / `sample/ir` to target languages.
- Selfhost path is not needed for this work and is out of scope.

Goal:
- Add `ir2lang.py` so `EAST3(JSON) -> target code` can run independently from the frontend.
- Use lazy import by `--target`, loading only the required backend.
- Establish a fast backend regression path with fixed IR input.

In scope:
- Add `src/ir2lang.py`
- Add `EAST3(JSON)` input validation (fail-fast for stage2/unknown formats)
- Add `--target`-based lazy-import dispatch (reuse backend registry)
- Add layer-specific option pass-through (`--lower-option`, `--optimizer-option`, `--emitter-option`)
- Add minimal usage procedures for `test/ir` / `sample/ir` (docs)

Out of scope:
- Selfhost `ir2lang` implementation (static-import variant)
- Changes to frontend (`py -> EAST3`) implementation
- Backend feature additions or optimization-spec changes

Acceptance criteria:
- `ir2lang.py --input <east3.json> --target <lang>` performs target conversion.
- Unspecified target backends are not imported (lazy import).
- `EAST2` / invalid IR inputs fail-fast with clear errors.
- Conversion smoke passes from `test/ir` / `sample/ir` for at least major targets (`cpp/rs/js`).
- Usage is added to `docs/ja/how-to-use.md` (and `docs/en/how-to-use.md` if needed).

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 src/ir2lang.py --help`
- `python3 src/ir2lang.py --input sample/ir/01_mandelbrot.json --target cpp --output out/ir2lang_cpp_01.cpp`
- `python3 src/ir2lang.py --input sample/ir/01_mandelbrot.json --target rs --output out/ir2lang_rs_01.rs`
- `python3 src/ir2lang.py --input sample/ir/01_mandelbrot.json --target js --output out/ir2lang_js_01.js`

## Breakdown

- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S1-01] Inventory `test/ir` / `sample/ir` input format (JSON schema/stage marker/required metadata), and finalize `ir2lang` acceptance contract.
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S1-02] Define `ir2lang.py` CLI spec (required args/output destination/layer options/fail-fast conditions).
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-01] Implement `src/ir2lang.py` with EAST3 JSON loading and target dispatch.
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-02] Implement target lazy import via backend registry and avoid importing unspecified toolchain.emit.
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-03] Implement layer-specific pass-through for `--lower/--optimizer/--emitter-option`.
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S2-04] Implement fail-fast errors for EAST2/invalid IR input and standardize error messages.
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S3-01] Add `sample/ir` / `test/ir` conversion smoke for major targets and fix backend-only regression path.
- [x] [ID: P1-IR2LANG-LAZY-EMIT-01-S3-02] Add `ir2lang.py` procedure to `docs/ja/how-to-use.md` (and `docs/en/how-to-use.md` if needed).

## S1-01: Input Acceptance Contract (Final)

- `ir2lang.py` accepts JSON input only; `.py` is not accepted (frontend dependency is blocked).
- JSON root must be one of:
  - `{"ok": true, "east": {...Module...}}`
  - `{"kind": "Module", ...}`
- Required keys for accepted `Module` root:
  - `kind == "Module"`
  - `east_stage == 3` (`1/2` fail-fast)
  - `body` must be a `list`
- `schema_version`, when present, must be `int >= 1` (invalid type/value fail-fast).
- `meta` may be omitted (treated internally as `{}`); when present it must be `dict`.

## S1-02: CLI Spec (Final)

- Entry point: `python3 src/ir2lang.py`
- Required:
  - Positional argument `input` (EAST3 JSON)
  - `--target <lang>`
- Optional:
  - `-o/--output` (defaults to `input` stem + target extension)
  - `--lower-option key=value` (repeatable)
  - `--optimizer-option key=value` (repeatable)
  - `--emitter-option key=value` (repeatable)
  - `--no-runtime-hook` (suppresses runtime placement)
- fail-fast conditions:
  - Missing `--target`
  - Invalid `key=value` format
  - Unknown layer option / type mismatch (`backend_registry.resolve_layer_options`)
  - Invalid input JSON / `EAST2` / `Module` contract violations
- Exit codes:
  - Success `0`
  - User input error `2`

Decision log:
- 2026-03-03: Per user instruction, opened P1 ticket for `ir2lang.py` (direct EAST3 JSON input + lazy target import) with selfhost support explicitly out of scope.
- 2026-03-03: Finalized policy that `ir2lang.py` input is EAST3 JSON only, requiring `east_stage==3`.
- 2026-03-03: Finalized policy to adopt `py2x.py`-compatible layer-option syntax, and support backend-only verification via `--no-runtime-hook`.
- 2026-03-03: Added `src/ir2lang.py`, implementing `backend_registry` lazy dispatch, layer-option pass-through, and fail-fast EAST3 contract checks.
- 2026-03-03: Added fixtures `sample/ir/01_mandelbrot.east3.json` and `test/ir/core_add.east3.json`, and fixed backend-only regression path with `tools/check_ir2lang_smoke.py` (`cpp/rs/js`).
- 2026-03-03: Added `ir2lang.py` procedures (fixture creation/direct conversion/smoke execution) to `docs/ja/how-to-use.md` / `docs/en/how-to-use.md`.
