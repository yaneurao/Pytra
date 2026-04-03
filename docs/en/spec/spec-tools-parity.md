<a href="../../ja/spec/spec-tools-parity.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# `tools/` — Cross-Language Parity Check

[Back to index](./spec-tools.md)

## 1. Tool Reference

- `tools/check/runtime_parity_check.py`
  - Purpose: Run runtime equalization checks across multiple target languages.
  - Main options: `--targets <langs>` (comma-separated), `--case-root {fixture,sample}`, `--category <subdir>` (filter by fixture subdirectory, e.g., `oop`, `control`, `typing`), `--all-samples`, `--opt-level`, `--cpp-codegen-opt`, `--cmd-timeout-sec`, `--summary-json`
  - Note: `--category` limits execution to cases under `test/fixture/source/py/<category>/`. Use this when you want to run regression checks by category without running all 132+ fixtures.
  - Note: Unstable timing lines like `elapsed_sec` / `elapsed` / `time_sec` are excluded from comparison by default.
  - Note: Artifact comparison requires exact matches for presence + size + CRC32 on artifacts reported via `output:`.
  - Note: Before each case runs, same-named artifacts under `sample/out`, `test/out`, and `out` are deleted to prevent stale-output mixups.
  - Note: On timeout, the process group is killed as a unit so child processes like `*_swift.out` are not left orphaned.
- `tools/check/runtime_parity_check_fast.py`
  - Purpose: A fast version of `runtime_parity_check.py`. Replaces the transpile stage with in-memory API calls to the toolchain2 Python API, eliminating process startup and intermediate file I/O.
  - Main options: Same as `runtime_parity_check.py` (`--targets`, `--case-root`, `--category`, `--all-samples`, `--opt-level`, `--cmd-timeout-sec`, `--summary-json`)
  - Limitation: `--cpp-codegen-opt` is not supported. Supported targets are currently `cpp` and `go`.
  - Usage: `PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py [options]`
- `tools/check/check_all_target_sample_parity.py`
  - Purpose: Run the canonical parity groups (`cpp`, `js_ts`, `compiled`, `scripting_mixed`) in order and confirm full target sample parity.
  - Main options: `--groups`, `--opt-level`, `--cpp-codegen-opt`, `--summary-dir`
- `tools/check/check_noncpp_backend_health.py`
  - Purpose: Aggregate the post-linked-program non-C++ backend health gate by family and report `primary_failure` / `toolchain_missing` / family broken/green status in one command.
  - Main options: `--family`, `--targets`, `--skip-parity`, `--summary-json`
- `tools/gen/export_backend_test_matrix.py`
  - Purpose: Run `tools/unittest/emit/**` and shared starred smoke tests, then regenerate the JA/EN backend test matrix docs.

## 2. Parity Check Speed-Up: In-Memory Pipeline

### Current Problem

`runtime_parity_check.py` launches `python src/pytra-cli.py ...` as a subprocess for each case and exchanges intermediate files (`.east1` → `.east2` → `.east3` → linked JSON → emit) via disk. The main cause of the hours-long runtime for 132 fixtures × multiple languages is this subprocess startup + disk I/O overhead.

### Solution

Each stage of toolchain2 exposes a dict-in / dict-out Python API:

```python
from toolchain2.parse.py.parse_python import parse_python_file       # → dict (EAST1)
from toolchain2.resolve.py.resolver import resolve_east1_to_east2     # → dict (EAST2)
from toolchain2.optimize.optimizer import optimize_east3_document     # → dict (EAST3-opt)
from toolchain2.link.linker import link_modules                       # → LinkResult
from toolchain2.emit.go.emitter import emit_go_module                 # → str (Go source)
from toolchain2.emit.cpp.emitter import emit_cpp_module               # → str (C++ source)
```

By calling these APIs directly instead of CLI subprocesses in parity checks, disk writes of intermediate files can be eliminated. Running parse → resolve → compile → optimize → link → emit in-memory within a single process provides a significant speedup.

### Migration Approach

1. Change the transpile stage in `runtime_parity_check.py` from CLI invocations to direct Python API calls
2. Continue using subprocesses for the compile + run stages (`g++`, `go run`, etc.) — target language compilers remain external processes
3. Keep the conventional CLI-based execution via a `--cli-mode` flag so API-call and CLI results can be cross-verified

Implementation: `tools/check/runtime_parity_check_fast.py` (a fast version that loads the registry once and shares it across all cases)

### Usage

```bash
# Run only the oop category with C++
PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py \
  --category oop --targets cpp

# Run all fixtures with Go
PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py \
  --targets go

# Run 18 sample cases with C++
PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py \
  --case-root sample --targets cpp

# Specify individual cases
PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py \
  class inheritance super_init --targets cpp

# Benchmark mode (measure sample execution time and record in .parity-results/)
PYTHONPATH=src:tools/check python3 tools/check/runtime_parity_check_fast.py \
  --targets go,cpp --case-root sample --benchmark

# Manually update the sample/README table from benchmark results
python3 tools/gen/gen_sample_benchmark.py
```

Note: `PYTHONPATH=src:tools/check` is required to resolve toolchain2 and runtime_parity_check modules.

`--benchmark` uses warmup=1, repeat=3, and takes the median. Normal parity checks still run once. Results are recorded in `elapsed_sec` for each case in `.parity-results/<target>_sample.json`, and `gen_sample_benchmark.py` is automatically run at the end of the parity check (only when 10+ minutes have passed since the last generation).

Reference: `docs/ja/plans/plan-pipeline-redesign.md` §3.5 "Performance Know-How: In-Memory Pipeline"

## 3. Smoke Test Operations

- The source of truth for common smoke tests (CLI success, `--east-stage 2` rejection, `load_east`, add fixture) is `tools/unittest/common/test_py2x_smoke_common.py`.
- Language-specific smoke suites (`tools/unittest/emit/<lang>/test_py2*_smoke.py`) keep only language-specific emitter/runtime contracts and must not reimplement common cases.
- Each language smoke suite must have a responsibility-boundary comment (`Language-specific smoke suite...`), verified statically by `tools/check/check_noncpp_east3_contract.py`.
- The canonical `PYTHONPATH` for smoke execution is `src:.:test/unit`. Some smoke suites read helpers directly under `test/unit` (e.g., `comment_fidelity.py`), so `test/unit` must not be dropped.
- The recommended regression order is the following 3 commands:
  - `PYTHONPATH=src:.:test/unit python3 -m unittest discover -s tools/unittest/common -p 'test_py2x_smoke*.py'`
  - `python3 tools/check/check_noncpp_east3_contract.py --skip-transpile`
  - `python3 tools/check/check_py2x_transpile.py --target <lang>` (for each target language)

## 4. Non-C++ Backend Health Matrix (Post Linked Program)

- Evaluate the non-C++ backend recovery baseline in the order: `static_contract -> common_smoke -> target_smoke -> transpile -> parity`.
- Run `parity` only for targets that passed every earlier gate. Targets with earlier failures must not be counted as parity failures.
- Keep `toolchain_missing` separate from `parity_fail`, using the `runtime_parity_check.py` skip as the infra baseline.
- In the 2026-03-08 snapshot, Wave 1 has `js/ts` as green and `rs/cs` as `toolchain_missing`. Wave 2 (`go/java/kotlin/swift/scala`) and Wave 3 (`ruby/lua/php/nim`) are all `toolchain_missing` for all 18 sample parity cases.
- Daily family-level health checks are run with commands like `python3 tools/check/check_noncpp_backend_health.py --family wave1`; a family is `green` when `broken_targets == 0`. `toolchain_missing` does not break the family; it is shown in a separate counter.
- `tools/run/run_local_ci.py` includes `python3 tools/check/check_noncpp_backend_health.py --family all --skip-parity`, permanently placing smoke/transpile gates that do not depend on parity into daily regression.
- `tools/run/run_local_ci.py` also includes `python3 tools/check/check_jsonvalue_decode_boundaries.py`, stopping increments where JSON artifact boundaries in selfhost/host slip back to raw `json.loads(...)`.

## 5. Full Target Sample Parity Completion Condition

- The canonical parity target order is `cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim`. This must match the return order of `list_parity_targets()`.
- "All-target parity green" means that when running `python3 tools/check/runtime_parity_check.py --targets cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim --case-root sample --ignore-unstable-stdout --opt-level 2 --cpp-codegen-opt 3`, every target and all 18 sample cases finish as `ok` only.
- In the full-green judgment, `toolchain_missing` is not treated as an exception. The following must all be 0: `case_missing`, `python_failed`, `python_artifact_missing`, `toolchain_missing`, `transpile_failed`, `run_failed`, `output_mismatch`, `artifact_presence_mismatch`, `artifact_missing`, `artifact_size_mismatch`, `artifact_crc32_mismatch`.
- Even when checking target groups separately, the criterion is the same:
  - baseline target: `python3 tools/check/runtime_parity_check.py --targets cpp --case-root sample --opt-level 2 --cpp-codegen-opt 3`
  - JS/TS: `python3 tools/check/runtime_parity_check.py --targets js,ts --case-root sample --ignore-unstable-stdout --opt-level 2`
  - compiled targets: `python3 tools/check/runtime_parity_check.py --targets rs,cs,go,java,kotlin,swift,scala --case-root sample --ignore-unstable-stdout --opt-level 2`
  - scripting / mixed targets: `python3 tools/check/runtime_parity_check.py --targets ruby,lua,php,nim --case-root sample --ignore-unstable-stdout --opt-level 2`
- The canonical wrapper for daily full-target reruns is `python3 tools/check/check_all_target_sample_parity.py --summary-dir work/logs/all_target_sample_parity`. The wrapper runs the 4 groups above in order and writes the merged result to `all-target-summary.json`.

## 6. Debian 12 Parity Bootstrap Snapshot

- As of 2026-03-08, the current machine assumed Debian 12 (`bookworm`) with `root` for the bootstrap.
- Bootstrap commands for compiled targets:
  - `apt-get update`
  - `apt-get install -y rustc mono-mcs golang-go openjdk-17-jdk kotlin scala nim`
  - `apt-get install -y binutils-gold gcc git libcurl4-openssl-dev libedit-dev libpython3-dev libsqlite3-dev uuid-dev gnupg2`
  - `curl -fL -o /opt/swift-6.2.2-RELEASE-debian12.tar.gz https://download.swift.org/swift-6.2.2-release/debian12/swift-6.2.2-RELEASE/swift-6.2.2-RELEASE-debian12.tar.gz`
  - `tar -xf /opt/swift-6.2.2-RELEASE-debian12.tar.gz -C /opt`
  - `ln -sfn /opt/swift-6.2.2-RELEASE-debian12/usr/bin/swift /usr/local/bin/swift`
  - `ln -sfn /opt/swift-6.2.2-RELEASE-debian12/usr/bin/swiftc /usr/local/bin/swiftc`
- Bootstrap commands for scripting / mixed targets:
  - `apt-get install -y ruby lua5.4 php-cli`
- After bootstrapping, `runner_needs` measurement confirmed that `cpp,rs,cs,js,ruby,lua,php,ts,go,java,swift,kotlin,scala,nim` all report `OK`.
