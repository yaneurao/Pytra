<a href="../../../ja/plans/archive/20260402-p1-dart-toolchain2-emitter-bootstrap.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1: Dart toolchain2 emitter bootstrap

Last updated: 2026-04-02

## Target

- [ID: P1-DART-EMITTER-S1] Add a toolchain2 Dart emitter entry point under `src/toolchain2/emit/dart/`
- [ID: P1-DART-EMITTER-S2] Add `src/runtime/dart/mapping.json`

## Approach

1. Add a formal Dart emitter entry point on the `toolchain2` side.
2. Add an EAST3 lowering profile and runtime mapping, enabling `target_language="dart"`.
3. Connect multi-file output and runtime copy (required for parity) to `tools/check/runtime_parity_check_fast.py`.
4. Align the runtime / parity pipeline needed for the CommonRenderer-based toolchain2 canonical emitter.

## Out of scope

- Removing hardcodes from the Dart emitter body
- Full migration to a CommonRenderer base
- Passing parity for all fixtures/samples

## Acceptance Criteria

1. `lower_east2_to_east3(..., target_language="dart")` does not crash when a profile is absent.
2. `toolchain2.emit.dart.emitter.emit_dart_module()` can convert linked EAST3 to Dart.
3. The parity tool can handle the Dart emit directory structure and runtime copy.

## Decision Log

- 2026-04-02: Added the toolchain2 entry point, lower profile, runtime mapping, parity pipeline, and smoke test.
- 2026-04-02: Dependency on the old `src/toolchain/emit/dart/` was withdrawn as a violation of emitter implementation guidelines; `src/toolchain2/emit/dart/` was finalized as the canonical source, achieving fixture 140/140, stdlib 16/16, sample 18/18 PASS.
