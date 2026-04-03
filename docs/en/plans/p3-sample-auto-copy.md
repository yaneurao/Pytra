<a href="../../en/plans/p3-sample-auto-copy.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P3-SAMPLE-AUTO-COPY: Automatically copy to sample/<lang>/ when sample parity PASSes

Last updated: 2026-03-30
Status: Not started

## Background

`sample/<lang>/` holds the showcased transpilation results for each language. Currently `regenerate_samples.py` is run manually to update them, but it is easy to forget to regenerate after improving an emitter.

The parity check converts samples and verifies their output against Python. A PASS means the code "works correctly after transpilation," so copying it directly to `sample/<lang>/` eliminates the need for manual regeneration.

## Design

### Copy conditions

- Copy only cases that **PASS** the parity check's sample execution
- Leave existing files unchanged for FAIL cases (do not overwrite with broken code)
- Do nothing if the Python execution fails

### Copy destination

Copy files from the emit directory to `sample/<lang>/`.

```
Emit directory:
  work/transpile/parity-fast/.../transpile/go/emit/01_mandelbrot.go

Copy destination:
  sample/go/01_mandelbrot.go
```

File names follow the existing naming convention (`<number>_<name>.<ext>`).

### Target languages

All languages that toolchain2 can emit (cpp, go, rs, ts, js, etc.). Create the `sample/<lang>/` directory with `mkdir -p` for languages where it does not yet exist.

### Relationship to `regenerate_samples.py`

Once the parity check handles automatic copying, the primary role of `regenerate_samples.py` (transpile + place) is absorbed by the parity check. However:

- The parity check requires Python execution (stdout comparison is needed). It cannot be used in environments where Python does not run.
- `regenerate_samples.py` can place files from emit alone (no execution required).

Keep both for now, and consider retiring `regenerate_samples.py` once parity check automatic copying is stable.

## Decision Log

- 2026-03-30: Decided to automatically copy to `sample/<lang>/` when parity PASSes. Eliminates the problem of forgetting to run `regenerate_samples.py` manually.
