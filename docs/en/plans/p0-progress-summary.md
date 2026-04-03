<a href="../../ja/plans/p0-progress-summary.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P0-PROGRESS-SUMMARY: Auto-generate an overall backend summary page

Last updated: 2026-03-30
Status: Completed (count display fix still needed)

## Background

Each matrix (fixture / sample / stdlib / selfhost / emitter lint) lives on a separate page, requiring users to navigate between pages to understand the overall picture. A single-page summary that gives a bird's-eye view of all languages is needed.

## Design

### Summary table

One row per language, showing fixture / sample / stdlib / selfhost / emitter lint status.

```
| Language | fixture | sample | stdlib | selfhost | lint |
|---|---|---|---|---|---|
| C++ | 🟩 146/146 | 🟩 18/18 | 🟩 10/10 | ⬜ | 🟩 0 |
| Go | 🟩 147/147 | 🟩 18/18 | 🟩 10/10 | ⬜ | 🟥 27 |
| Rust | 🟥 100/146 | ⬜ | ⬜ | ⬜ | 🟥 6 |
| TS | 🟩 125/146 | 🟥 10/18 | ⬜ | ⬜ | 🟥 6 |
```

Cell format:
- fixture / sample / stdlib: `🟩 PASS/total` or `🟥 PASS/total` or `⬜` (not run)
- selfhost: `🟩` / `🟥` / `⬜` (taken from the Python row of the selfhost matrix)
- lint: `🟩 0` (no violations) or `🟥 N` (N violations) or `⬜` (no emitter)

### Generation

`gen_backend_progress.py` generates this via `_build_summary_matrix()`. Output destinations:
- `docs/ja/progress/backend-progress-summary.md`
- `docs/en/progress/backend-progress-summary.md`

### Mutual exclusion

The automatic regeneration triggered at the end of parity checks (`_maybe_regenerate_progress`, `_maybe_regenerate_benchmark`, `_maybe_refresh_selfhost_python`, `_maybe_run_emitter_lint`) is controlled by `.parity-results/.gen.lock`. If the lock cannot be acquired, the step is skipped.

## Decision Log

- 2026-03-30: Confirmed the need for a summary page. Decided to consolidate fixture/sample/stdlib/selfhost/emitter lint onto a single page.
- 2026-03-30: Decided to use `.parity-results/.gen.lock` for mutual exclusion.
- 2026-03-30: S1–S4 completed. However, each cell in the summary does not display `PASS/total` counts (e.g. `123/128`). This needs to be fixed.
