<a href="../../en/plans/p2-sample-benchmark.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P2-SAMPLE-BENCHMARK: Automatically measure execution time in sample parity check and reflect it in README

Last updated: 2026-03-30
Status: Completed

## Background

`sample/README-ja.md` and `sample/README.md` include an "execution speed comparison" table, but it is currently updated by manual measurement (last measured: 2026-02-27). Since the parity check runs samples in Python and each target language, execution time can be measured automatically there and used to keep the README table up to date.

This machine is a high-spec many-core system, so single-threaded measurement is sufficiently stable.

## Design

### 1. Recording execution time

Measure Python and target language execution times during sample execution in the parity check (fast version).

Recording destination: add an `elapsed_sec` field to each case in `.parity-results/<target>_sample.json`. Python measurement results are recorded in `.parity-results/python_sample.json`.

```json
{
  "target": "go",
  "case_root": "sample",
  "results": {
    "01_mandelbrot": {
      "category": "ok",
      "timestamp": "2026-03-30T12:00:00",
      "elapsed_sec": 0.753
    }
  }
}
```

### 2. Measurement protocol

Align with existing measurement conditions or define a new protocol.

Existing conditions (as documented in `sample/README-ja.md`):
- warmup=1, repeat=5, median of `elapsed_sec` used
- Compilation time excluded

Since the parity check currently runs only once, adding repeats would make it considerably slower. Options:

1. **Record a single-run measurement directly** — fast but values may fluctuate
2. **Median of warmup=1, repeat=3** — lighter than existing but stable
3. **Enable repeat mode with a `--benchmark` flag** — normal parity uses 1 run; repeat only when benchmarking

Option 3 is the most flexible. Normal parity checks remain fast; add `--benchmark` only when updating the benchmark results.

### 3. Automatic README table generation

`tools/gen/gen_sample_benchmark.py` reads `.parity-results/*_sample.json` and rewrites the "execution speed comparison" table in `sample/README-ja.md` and `sample/README.md`.

- Only the table section is replaced; all other sections remain unchanged
- Languages/cases that have not been measured display `—`
- Measurement timestamp is shown below the table
- Japanese and English are updated simultaneously (table content is the same since it is numeric; only the headings differ by language)

### 4. Automatic regeneration

At the end of the parity check, if the mtime of `sample/README-ja.md` is more than 10 minutes old, `gen_sample_benchmark.py` is executed automatically. This is the same mechanism as the progress matrix.

## Decision Log

- 2026-03-30: Decided to measure execution time during sample execution in the parity check and reflect it automatically in the README. Judged that single-threaded measurement stability is sufficient given the many-core high-spec machine.
