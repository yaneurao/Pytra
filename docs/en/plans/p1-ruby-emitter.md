<a href="../../ja/plans/p1-ruby-emitter.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1-RUBY-EMITTER: Implement a new Ruby emitter in toolchain2

Last updated: 2026-03-31
Status: S1–S3 completed; S4–S6 not started

## Background

A Ruby emitter and runtime exist in the old toolchain1, but they need to be migrated to the new toolchain2 pipeline.

## Design

- Implemented in `src/toolchain2/emit/ruby/` using CommonRenderer + override structure
- Reference the old `src/toolchain/emit/ruby/` and TS emitter (`src/toolchain2/emit/ts/`)
- Define `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` in `src/runtime/ruby/mapping.json`
- parity check: three-stage verification (fixture + sample + stdlib) via `runtime_parity_check_fast.py --targets ruby`

## Decision Log

- 2026-03-31: Ruby backend role established. Approach: implement toolchain2 emitter following the emitter guide.
- 2026-03-31: S1–S3 completed. Implemented a new emitter in `src/toolchain2/emit/ruby/`. Created mapping.json. Emit succeeded for all 1031 linked fixtures (0 failures). Added Ruby emit/runtime copy/run dispatch to the parity check tooling.
