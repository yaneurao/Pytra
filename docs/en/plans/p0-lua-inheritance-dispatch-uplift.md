# P0: Improve Lua inheritance-method dynamic dispatch

Last updated: 2026-03-01

Related TODO:
- `ID: P0-MULTILANG-INHERIT-DISPATCH-01-S2-LUA` in `docs/ja/todo/index.md`

Background:
- The Lua backend has `setmetatable` inheritance, but lacks lowering for `super`-equivalent calls.

Goal:
- Emit explicit parent-method calls in Lua to ensure consistent inherited-call behavior.

Scope:
- `src/hooks/lua/emitter/lua_native_emitter.py`

Out of scope:
- General optimization of Lua runtime

Acceptance criteria:
- A helper/emission rule for `super` calls is introduced.
- Fixture parity matches.

Verification commands:
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2lua_smoke.py' -v`
- `PYTHONPATH=src python3 tools/runtime_parity_check.py inheritance_virtual_dispatch_multilang --targets lua`

Breakdown:
- [ ] Lower `super` calls to explicit parent-table calls.
- [ ] Verify consistency with the `setmetatable` inheritance chain.
- [ ] Add fixture regressions.

Decision log:
- 2026-03-01: Fixed policy to prioritize implementing `super` lowering on top of metatable inheritance in Lua.
