<a href="../../ja/plans/p5-backend-progress.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P5-BACKEND-PROGRESS: Automatic accumulation of parity results + auto-generation of a progress page

Last updated: 2026-03-30
Status: Complete

## Background

Pytra is developing 4 backends (C++/Go/Rust/TS) in parallel, and there is no way to track each backend's fixture parity / sample parity / selfhost progress. Parity checks take several hours, so full runs cannot be done frequently, and the results of partial runs are lost without being accumulated.

A progress page that lets outside observers judge "is this project actively progressing?" is needed.

## Design

### 1. Automatic result accumulation

`runtime_parity_check.py` / `runtime_parity_check_fast.py` unconditionally write results to `.parity-results/` upon completion.

- File: `.parity-results/<target>_<case-root>.json` (e.g., `go_fixture.json`, `cpp_sample.json`)
- If a file already exists, merge per case (update, not overwrite)
- Each case is timestamped
- `--summary-json` remains as an additional output destination (for compatibility)

JSON format:

```json
{
  "target": "go",
  "case_root": "fixture",
  "results": {
    "add": {
      "category": "ok",
      "timestamp": "2026-03-29T14:23:01"
    },
    "class": {
      "category": "ok",
      "timestamp": "2026-03-29T14:23:05"
    },
    "pytra_runtime_png": {
      "category": "run_failed",
      "detail": "out/ directory missing",
      "timestamp": "2026-03-28T10:15:30"
    }
  }
}
```

- When a partial run is performed with `--category oop`, only the oop case timestamps are updated; results for other categories remain unchanged
- When a new fixture is added, it simply has no entry in the JSON. At aggregation time it is detected as "not run"
- `work/` is in `.gitignore`, so result files themselves are not committed

### 2. selfhost results

selfhost runs through a separate path from parity check (`pytra-cli2 -build`, `g++`, `go build`, `cargo build`, `tsc`). Results are recorded in `.parity-results/selfhost_<lang>.json`.

JSON format:

```json
{
  "selfhost_lang": "go",
  "stages": {
    "emit": {"status": "ok", "timestamp": "2026-03-29T15:00:00"},
    "build": {"status": "fail", "detail": "3 compile errors", "timestamp": "2026-03-29T15:01:00"},
    "parity": {"status": "not_reached", "timestamp": ""}
  },
  "emit_targets": {
    "cpp": {"status": "ok", "timestamp": "2026-03-29T15:00:10"},
    "go": {"status": "ok", "timestamp": "2026-03-29T15:00:20"},
    "rs": {"status": "not_tested", "timestamp": ""},
    "ts": {"status": "not_tested", "timestamp": ""}
  }
}
```

### 3. Progress page generation

`tools/gen/gen_backend_progress.py` reads `.parity-results/*.json`, cross-references against the fixture and sample lists, and generates Markdown.

Output locations (both Japanese and English are generated simultaneously — manually translating machine-generated content is inefficient, so the script outputs both languages directly):

- `docs/ja/progress/backend-progress.md` — bridge page (legend + links to the 3 matrices + related links). Written by hand.
- `docs/ja/progress/backend-progress-fixture.md` — fixture parity matrix. Machine-generated.
- `docs/ja/progress/backend-progress-sample.md` — sample parity matrix. Machine-generated.
- `docs/ja/progress/backend-progress-selfhost.md` — selfhost matrix. Machine-generated.
- Same 4 files are also generated under `docs/en/progress/` (with the bridge page heading in English).

#### Fixture parity matrix

A table of all cases × all languages. Status icons:

| Icon | Meaning |
|---|---|
| 🟩 | PASS (emit + compile + run + stdout match) |
| 🟥 | FAIL (transpile_failed / run_failed / output_mismatch) |
| 🟨 | TM (toolchain_missing) |
| 🟪 | TO (timeout) |
| ⬜ | Not run |

```
| Category | Case | C++ | Go | Rust | TS |
|---|---|---|---|---|---|
| core | add | 🟩 | 🟩 | 🟩 | 🟩 |
| core | fib | 🟩 | 🟩 | 🟥 | ⬜ |
| oop | class | 🟩 | 🟩 | 🟩 | 🟩 |
| ... | ... | ... | ... | ... | ... |
| | **Total** | 🟩115 🟥31 | 🟩146 | 🟩80 🟥20 ⬜46 | 🟩50 ⬜96 |
```

#### Sample parity matrix

18 samples × all languages. Same format as fixture.

#### selfhost matrix

A cross-table of selfhost language × emit target language. Displays progress in stages.

| Icon | Meaning |
|---|---|
| ⬜ | Not started |
| 🟨 | emit OK |
| 🟧 | build OK |
| 🟩 | parity PASS |

```
| selfhost language \ emit target | C++ | Go | Rust | TS |
|---|---|---|---|---|
| Python (original) | 🟩 | 🟩 | 🟨 | 🟨 |
| C++ selfhost | ⬜ | ⬜ | ⬜ | ⬜ |
| Go selfhost | ⬜ | ⬜ | ⬜ | ⬜ |
| Rust selfhost | ⬜ | ⬜ | ⬜ | ⬜ |
| TS selfhost | ⬜ | ⬜ | ⬜ | ⬜ |
```

The ultimate goal is 🟩 in every cell.

#### Freshness warnings

Cases with timestamps more than 7 days old receive a ⚠ marker, prompting re-execution.

### 4. Link from README

Add a link to the progress page in README.md, around the area above the Changelog section.

```markdown
## Backend Progress

[fixture / sample / selfhost progress matrices](docs/ja/progress/backend-progress.md)
```

## Operational flow

1. Each person runs a parity check (partial runs are fine)
2. Results are automatically accumulated in `.parity-results/`
3. Run `python3 tools/gen/gen_backend_progress.py` at any time
4. `docs/ja/progress/backend-progress.md` is updated
5. Commit and push

## Decision Log

- 2026-03-29: Decided on the approach of automatically accumulating parity check results in a designated folder and generating a progress page with an aggregation script. Results are written unconditionally within the script to prevent forgetting the `--summary-json` option.
- 2026-03-29: Approach of merging and accumulating partial run results (e.g., `--category oop`). When a fixture is newly added, it simply has no entry in the JSON and is detected as "not run" at aggregation time.
- 2026-03-29: The selfhost matrix is a cross-table of "selfhost language × emit target language." The ultimate goal is to be able to selfhost all languages in all languages.
- 2026-03-30: P5-PROGRESS S1–S4 complete. Implemented `_save_parity_results()` in runtime_parity_check.py and reused from the fast version. Japanese/English progress pages generated by `tools/gen/gen_backend_progress.py`. Added link in README.md. The selfhost format matches the specification in this plan; gen_backend_progress.py reads `selfhost_<lang>.json` and displays the matrix.
