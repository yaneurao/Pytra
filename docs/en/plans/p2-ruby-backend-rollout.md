# P2: Add Ruby Backend

Last updated: 2026-02-27

Related TODO:
- `ID: P2-RUBY-BACKEND-01` in `docs/ja/todo/index.md`

Background:
- User request indicates policy to add Ruby as a backend target.
- Current supported languages are `cpp/rs/cs/js/ts/go/java/swift/kotlin`, and Ruby backend is not implemented.
- If responsibility boundaries (EAST3 input, fail-closed behavior, runtime boundary) are not fixed first, there is risk of the same growth/complexity problems seen in existing backends.

Objective:
- Add native direct generation path `EAST3 -> Ruby` with `py2rb.py` as entry point and make major `sample/py` cases executable in Ruby.

Language rollout order (final):
1. Ruby (implemented in this plan)
2. Lua (file as P2 after Ruby backend completion)
3. PHP (file as P2 after Lua backend completion)

Scope:
- `src/py2rb.py`
- `src/hooks/ruby/emitter/`
- `src/runtime/ruby/pytra/` (minimum required)
- `tools/check_py2rb_transpile.py` / `test/unit/test_py2rb_smoke.py` / parity path
- `sample/ruby` and related docs

Out of scope:
- Simultaneous addition of PHP backend
- Advanced Ruby backend optimization (prioritize correctness and regression path first)
- Large design changes in existing backends (`cpp/rs/cs/js/ts/go/java/swift/kotlin`)

Acceptance Criteria:
- `py2rb.py` generates Ruby code from EAST3.
- Minimal fixtures (`add` / `if_else` / `for_range`) pass transpile and execution.
- `tools/check_py2rb_transpile.py` and smoke/parity regression paths are provided.
- Usage guide and support matrix in `sample/ruby` and `docs/ja/docs` are synchronized.

Validation Commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rb_transpile.py`
- `python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --all-samples --ignore-unstable-stdout`

Decision Log:
- 2026-02-27: Per user instruction, finalized policy to track Ruby backend addition under P2 priority in TODO.
- 2026-02-27: Per user instruction, fixed implementation order for added languages as `Ruby -> Lua -> PHP`.
- 2026-02-27: [ID: `P2-RUBY-BACKEND-01-S1-01`] Added `docs/ja/spec/spec-ruby-native-backend.md` (English translation: `docs/en/spec/spec-ruby-native-backend.md`) to document EAST3 input responsibility, fail-closed behavior, runtime boundary, and out-of-scope items.
- 2026-02-27: [ID: `P2-RUBY-BACKEND-01-S1-02`] Added `src/py2rb.py` and `src/hooks/ruby/emitter/` (`ruby_native_emitter.py`), implementing the minimum skeleton that can transpile `add/if_else/for_range`. `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v` showed `Ran 9 tests ... OK (skipped=1)` (runtime tests skipped because Ruby toolchain is not installed).
- 2026-02-27: [ID: `P2-RUBY-BACKEND-01-S2-01`] Added minimal lowerings/runtime helpers for `ListComp/RangeExpr/Slice/ObjLen/ObjStr/Unbox` and `bytearray/bytes/enumerate/range/list/dict/abs` in `ruby_native_emitter.py`; confirmed all 18 `sample/py` cases transpile and `Ran 11 tests ... OK (skipped=1)`.
- 2026-02-27: [ID: `P2-RUBY-BACKEND-01-S2-02`] Extended class/instance support: removed `self` argument, generated `attr_accessor`, synthesized dataclass `initialize`, lowered `isinstance` to `is_a?`, and switched `png|gif` attribute calls to runtime hooks. Confirmed `Ran 14 tests ... OK (skipped=1)` and 12 fixture transpilations in `test/fixtures/oop`.
- 2026-02-27: [ID: `P2-RUBY-BACKEND-01-S3-01`] Added `tools/check_py2rb_transpile.py`, confirming `checked=133 ok=133 fail=0 skipped=6`. Also added `ruby` target to `runtime_parity_check.py`, including `--targets ruby` path and Ruby entry verification in `test_runtime_parity_check_cli.py`.
- 2026-02-27: [ID: `P2-RUBY-BACKEND-01-S3-02`] Regenerated `sample/ruby` from 18 `sample/py` files; updated Ruby badge/supported-language list/sample links in `docs/ja/README.md/README.md`; appended Ruby run instructions and regression-check path to `docs/ja/how-to-use.md` and `docs/en/how-to-use.md`.

## Breakdown

- [x] [ID: P2-RUBY-BACKEND-01-S1-01] Document Ruby backend contract (input EAST3, fail-closed behavior, runtime boundary, out of scope).
- [x] [ID: P2-RUBY-BACKEND-01-S1-02] Add skeleton of `src/py2rb.py` and `src/hooks/ruby/emitter/`, and pass minimal fixtures.
- [x] [ID: P2-RUBY-BACKEND-01-S2-01] Implement basic statement/expression lowerings (assignment, branch, loop, call, minimal builtins).
- [x] [ID: P2-RUBY-BACKEND-01-S2-02] Implement support in stages for class/instance/isinstance/import (including `math` and image runtime).
- [x] [ID: P2-RUBY-BACKEND-01-S3-01] Add `check_py2rb_transpile` and smoke/parity regression path.
- [x] [ID: P2-RUBY-BACKEND-01-S3-02] Regenerate `sample/ruby` and synchronize README/how-to-use.
