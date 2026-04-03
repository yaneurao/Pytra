# Plan: Automatic recording of parity change log (P0-PARITY-CHANGELOG)

## Background

Even when parity check results regress, the progress matrix does not make it apparent. The goal is to automatically log the moment when PASS counts change so that it is possible to track what changed and when.

## Design

### Output Location

Append to `docs/{ja,en}/progress-preview/changelog.md`.

- `progress-preview/` is outside git management (auto-generated)
- It is manually copied to `progress/` roughly once a week, at which point it enters git
- The changelog is copied along with it, so the history is preserved in git

### Format

```markdown
# Parity Changelog

| Datetime | Language | case-root | Change | Notes |
|---|---|---|---|---|
| 2026-03-31T10:15 | cpp | fixture | 126→131 (+5) | |
| 2026-03-31T08:45 | rs | fixture | 81→0 (-81) | regression |
```

- New rows are inserted immediately after the table header so that the newest row appears at the top
- Nothing is appended when there is no change
- On a decrease, the Notes column says `regression`

### When to Record

When `runtime_parity_check_fast.py` saves results to `.parity-results/`:

1. Retrieve the previous PASS count from the existing `.parity-results/<target>_<case-root>.json`
2. Compare with the current PASS count
3. If there is a change, append a row to `progress-preview/changelog.md`

### Implementation Location

Near the `_save_parity_results()` call in `runtime_parity_check_fast.py`. Simply read the existing JSON, count PASS entries, and compare with the new result.

## Impact

- Changelog append logic added to `runtime_parity_check_fast.py`
- Same addition to `runtime_parity_check.py` (non-fast version)
- `progress-preview/changelog.md` is created as a new file
- No impact on existing parity check behavior (append only)
