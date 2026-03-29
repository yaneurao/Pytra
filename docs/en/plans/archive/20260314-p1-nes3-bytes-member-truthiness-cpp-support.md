<a href="../../../ja/plans/archive/20260314-p1-nes3-bytes-member-truthiness-cpp-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: stop the `!bytes` residual for member-based `bytes` truthiness in the C++ lane

Last updated: 2026-03-14

Related TODO:
- `docs/ja/todo/index.md` `ID: P1-NES3-BYTES-MEMBER-TRUTHINESS-CPP-01`

Background:
- The Pytra-NES3 repro [`materials/refs/from-Pytra-NES3/cartridge_like.py`](../../../materials/refs/from-Pytra-NES3/cartridge_like.py) uses `if not self.chr_rom:`.
- Representative `bytes` truthiness support already exists, but as of 2026-03-13 the C++ lane still leaks member access as `!(this->chr_rom)`, which fails because `bytes` lowers to `list<unsigned char>`.
- The archived task locked the representative lane for local names and conditional expressions, but the attribute/member lane still diverges from that contract.

Objective:
- Align member/attribute-based `bytes` truthiness with the existing `len`-based representative contract.
- Lock the residual exposed by `cartridge_like.py` with focused regressions and compile smoke.

In scope:
- C++ emitter / conditional lowering for `bytes` field and attribute truthiness
- Compile smoke for `materials/refs/from-Pytra-NES3/cartridge_like.py`
- Regression, docs, and TODO sync for this `bytes` truthiness residual

Out of scope:
- Redesigning the `bytes` runtime type
- Simultaneous extension to `bytearray` or `memoryview`
- Non-C++ backends

Acceptance criteria:
- The generated C++ for `cartridge_like.py` compiles.
- `if not self.chr_rom` no longer emits raw `!bytes`.
- Existing representative `bytes` truthiness regressions keep passing while the member lane joins the same contract.

Validation commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `bash ./pytra materials/refs/from-Pytra-NES3/cartridge_like.py --target cpp --output-dir /tmp/pytra_nes3_cartridge_like`
- `g++ -std=c++20 -O0 -c /tmp/pytra_nes3_cartridge_like/src/cartridge_like.cpp -I /tmp/pytra_nes3_cartridge_like/include -I /workspace/Pytra/src -I /workspace/Pytra/src/runtime/cpp`
- `git diff --check`

## Breakdown

- [x] [ID: P1-NES3-BYTES-MEMBER-TRUTHINESS-CPP-01-S1-01] Locked the current failure and residual scope for the member/attribute lane in focused regressions, the plan, and TODO.
- [x] [ID: P1-NES3-BYTES-MEMBER-TRUTHINESS-CPP-01-S2-01] Lowered member/attribute-based `bytes` truthiness through a `len`-based C++ condition.
- [x] [ID: P1-NES3-BYTES-MEMBER-TRUTHINESS-CPP-01-S3-01] Synced compile smoke and docs wording to the representative contract.

Decision log:
- 2026-03-13: Split out as a follow-up limited to the member lane because the Pytra-NES3 repro is a residual beyond the archived representative support.
- 2026-03-14: Routed the `UnaryOp(Not)` fallback through `render_cond` instead of raw `render_expr`, so `if not self.chr_rom` now joins the existing `bytes` truthiness contract via `py_len(...)`.
- 2026-03-14: Added the focused regression `test_cli_pytra_nes3_cartridge_like_bytes_member_truthiness_syntax_checks` and verified compile-green behavior through both `python3 src/py2x.py --target cpp --multi-file --output-dir /tmp/pytra_nes3_cartridge_like_py2x` and the selfhosted `bash ./pytra ... --target cpp --output-dir /tmp/pytra_nes3_cartridge_like_selfhost` lane.
