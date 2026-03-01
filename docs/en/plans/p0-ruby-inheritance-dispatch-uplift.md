# P0: Ruby Inheritance Method Dynamic Dispatch Improvement

Last updated: 2026-03-01

Related TODO:
- `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-RUBY` in `docs/ja/todo/index.md`

Background:
- Ruby can handle inheritance itself, but lowering for `super` calls is insufficient.

Goal:
- Correctly lower `super().__init__` / `super().method` into Ruby `super`.

In scope:
- `src/hooks/ruby/emitter/ruby_native_emitter.py`

Out of scope:
- Performance optimization of Ruby runtime

Acceptance criteria:
- `super` calls are emitted in line with Python semantics.
- Fixture parity matches.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets ruby`

Breakdown:
- [ ] Add a `super`-specific branch in call lowering.
- [ ] Verify argument forwarding for `initialize`-style paths.
- [ ] Add fixture regression.

Decision log:
- 2026-03-01: Ruby policy is to fill the missing `super` lowering as top priority.
