# P5-RS-CLI-COMMON: Migrate Rust cli.py to the common runner

Last updated: 2026-04-03

## Background

Among all 17 language cli.py files, only Rust does not use the common runner (`toolchain2.emit.common.cli_runner`) and retains a 235-line custom implementation. The custom parts are the following two:

1. **type_id table generation**: `_generate_type_id_table_rs` generates a Rust version of `PYTRA_TID_*` constants. Creates a constant table from the manifest's `type_id_resolved_v1`.
2. **package mode**: The `--package` option generates `Cargo.toml` + `src/lib.rs` + `src/main.rs`. Used for selfhost.

## Prerequisites

- **P0-ISINSTANCE-DETID fully complete**: `PYTRA_TID_*` is completely removed from EAST3, and the Rust emitter has migrated to `expected_type_name`-based approach. This makes type_id table generation unnecessary.
- **Rust emitter has migrated to native judgment** (`if let` / `match`) equivalent to `x is Type`.

## Approach

1. Remove type_id table generation (becomes unnecessary per the prerequisites)
2. Move runtime copy (`_copy_rs_runtime_files`) to `post_emit`
3. Move package mode (`Cargo.toml` + `lib.rs` + `main.rs` generation) to `post_emit`
4. Delegate manifest reading, module loop, and argument parsing to the common runner
5. The `--package` option is either added to the common runner's `_parse_args`, or read from `sys.argv` inside Rust's `post_emit`

## Intended cli.py after completion

```python
from toolchain2.emit.common.cli_runner import run_emit_cli
from toolchain2.emit.rs.emitter import emit_rs_module

def _post_emit_rs(output_dir: Path) -> None:
    _copy_rs_runtime(output_dir)
    if _is_package_mode():
        _write_cargo_toml(output_dir)
        _write_lib_rs(output_dir)
        _write_main_rs(output_dir)

def main() -> int:
    import sys
    return run_emit_cli(emit_rs_module, sys.argv[1:], default_ext=".rs", post_emit=_post_emit_rs)
```

## Subtasks

1. [ ] [ID: P5-RS-CLI-S1] Migrate the Rust emitter to `expected_type_name`-based approach (Rust version of P0-ISINSTANCE-DETID)
2. [ ] [ID: P5-RS-CLI-S2] Remove `_generate_type_id_table_rs` and `_manifest_type_id_table`
3. [ ] [ID: P5-RS-CLI-S3] Move runtime copy and package mode to `post_emit` and delegate to the common runner
4. [ ] [ID: P5-RS-CLI-S4] Confirm no regression in Rust parity

## Decision Log

- 2026-04-03: Migrated all 17 language cli.py files to the common runner. Only Rust retains a custom implementation. Filed a plan to migrate after type_id table deprecation.
