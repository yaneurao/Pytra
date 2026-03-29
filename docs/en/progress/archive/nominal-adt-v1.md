<a href="../../ja/language/nominal-adt-v1.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# nominal ADT v1 Guide

Last updated: 2026-03-11

This document is the migration note for treating nominal ADT as a formal Pytra language feature and summarizes the current v1 surface and rollout state.

## canonical v1 surface

- Declare the family as a top-level `class` annotated with `@sealed`.
- Declare variants as top-level classes in the same module, each with single inheritance from the family.
- Payload variants must use `@dataclass`.
- Use variant class calls as constructors, for example `Just(1)`.
- Use `isinstance(x, Just)` narrowing followed by field access as the canonical variant-access surface.
- Built-in `JsonValue` lanes and user-defined nominal ADT lanes share the same `nominal_adt` category.

## selfhost-safe constraints

The representative v1 lane is currently fixed to the following:

- top-level same-module / family-first family and variant declarations
- mandatory `@dataclass` on payload variants
- no function-local or class-local nominal ADT declarations
- the user-facing `match/case` source surface is not yet part of canonical v1

These constraints keep the selfhost parser and representative backend aligned under fail-closed staged rollout rules.

## backend rollout status

- C++:
  - supports representative nominal ADT v1 declaration / constructor / variant check / projection
  - lowers the representative `NominalAdtMatch` lane into `if / else if`
  - fail-closes plain `Match` with `unsupported Match lane`
- Rust / C#:
  - fail-close representative nominal ADT v1 lanes with `unsupported_syntax`
- Go / Java / Kotlin / Scala / Swift / Nim / JS / TS / Lua / Ruby / PHP:
  - fail-close representative nominal ADT `Match` lanes with backend-local `unsupported stmt kind: Match`

## migration guidance

- If you currently model a closed sum type as an ad-hoc class hierarchy, move to an `@sealed` family plus top-level variant classes.
- Add `@dataclass` to every payload-carrying variant.
- For now, read variant payloads through `isinstance(...)` plus field access instead of source-level `match/case`.
- Keep the lane aligned with built-in nominal ADTs such as `JsonValue`; do not fall back to `object` or ad-hoc casts.

## Related

- v1 user surface: [spec-user](../spec/spec-user.md)
- ADT / pattern / `match` schema: [spec-east](../spec/spec-east.md)
- C++ representative support: [py2cpp Support Matrix](./cpp/spec-support.md)
