# Plan: Automatic recording of emitter lint change log (P1-LINT-CHANGELOG)

## Background

Changes in parity check PASS counts are now automatically recorded in `progress-preview/changelog.md`, but changes in emitter lint (hardcode violation detection) are not recorded. The goal is to log when the number of violations or passing categories changes per language, so that improvements and regressions can be tracked.

## Design

### When to detect changes

Immediately before `check_emitter_hardcode_lint.py` writes `emitter_lint.json`, read the existing `.parity-results/emitter_lint.json` and compare old values against the new ones.

### Recorded metric

- Use `pass_cats` (number of passing categories) as the metric equivalent to "PASS count"
  - Increase = improvement (fewer violations)
  - Decrease = regression (more violations)
- Reuse the same `_append_parity_changelog` function from parity, passing `case_root="lint"` for recording

### Format Example

```markdown
| 2026-03-31T10:25 | rs | lint | 6→8 (+2) |  |
| 2026-03-31T10:25 | cs | lint | 6→4 (-2) | regression |
```

### Implementation Location

Inside the `_write_results()` function in `check_emitter_hardcode_lint.py`, add before and after the write of `emitter_lint.json`.

1. Before writing JSON: read the existing file and retrieve `pass_cats` per language
2. After writing JSON: call `_append_parity_changelog` per language
3. Import and reuse `_append_parity_changelog` from `runtime_parity_check`

### Cooldown / Lock

The existing `_append_parity_changelog` already implements locking and cooldown (10 minutes), so calling it with `case_root="lint"` applies them automatically.
The marker file will be `.parity-results/.changelog_last_<lang>_lint`.

## Impact

- Import and before/after comparison logic added to `check_emitter_hardcode_lint.py`
- Existing `runtime_parity_check.py` / `_append_parity_changelog` unchanged
- Lint change entries will be added to `progress-preview/changelog.md`

## Decision Log

- 2026-03-31: Filed. Decided to reuse the parity changelog function with `pass_cats` as the metric.
