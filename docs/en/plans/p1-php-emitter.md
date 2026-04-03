<a href="../../ja/plans/p1-php-emitter.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P1-PHP-EMITTER: Implement a new PHP emitter in toolchain2

Last updated: 2026-03-31
Status: S1–S4 completed; S5 (parity) not started

## Background

A PHP emitter and runtime exist in the old toolchain1, but they need to be migrated to the new toolchain2 pipeline.

## Design

- Implemented in `src/toolchain2/emit/php/` using CommonRenderer + override structure
- Reference the old `src/toolchain/emit/php/` and TS emitter (`src/toolchain2/emit/ts/`)
- Define `calls`, `types`, `env.target`, `builtin_prefix`, `implicit_promotions` in `src/runtime/php/mapping.json`
- parity check: three-stage verification (fixture + sample + stdlib) via `runtime_parity_check_fast.py --targets php`

## Decision Log

- 2026-03-31: PHP backend role established. Approach: implement toolchain2 emitter following the emitter guide.
