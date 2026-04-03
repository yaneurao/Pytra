# Plan: mod structure output for Rust selfhost (P9-RS-MOD)

## Background

When linking toolchain2 (150+ modules) with a flat `include!` for Rust selfhost, top-level type names such as `EmitContext` collide across multiple emitter modules, causing `rustc` to fail.

`include!` is "glue for when combining everything into one file is inconvenient" and is not a way to structure a multi-module program. The output should follow Rust's design philosophy using a `mod` + `use` structure.

## Current Problem

```
// flat include! — all modules are expanded into the same scope
include!("toolchain2_emit_cs_emitter.rs");   // pub struct EmitContext { ... }
include!("toolchain2_emit_go_emitter.rs");   // pub struct EmitContext { ... }  ← collision
include!("toolchain2_emit_ts_emitter.rs");   // pub struct EmitContext { ... }  ← collision
```

## Design

### Target Structure

```
work/selfhost/build/rs/
  src/
    main.rs                           # entry point
    lib.rs                            # list of mod declarations
    toolchain2_emit_cs/
      mod.rs                          # pub struct EmitContext { ... }
    toolchain2_emit_go/
      mod.rs                          # pub struct EmitContext { ... }  ← separate mod, no collision
    toolchain2_emit_ts/
      mod.rs
    toolchain2_compile/
      mod.rs
    toolchain2_link/
      mod.rs
    ...
  Cargo.toml
```

### Usage

```rust
// from main.rs or other modules
use crate::toolchain2_emit_cs::EmitContext as CsEmitContext;
use crate::toolchain2_emit_go::EmitContext as GoEmitContext;
```

### Emitter Changes

1. **ProgramWriter / multifile_writer** adds a mode to output `mod` structure for Rust
   - 1 EAST module = 1 Rust `mod` directory (or 1 file)
   - Automatically generate `pub mod <module_name>;` declarations in `lib.rs`
   - Generate `use crate::<module>::<symbol>;` for cross-module references

2. **Rust emitter** changes
   - Replace `include!` generation with `mod` + `use` generation
   - Emit `use crate::` paths for cross-module references
   - Consolidate module-level initialization function calls in `main.rs`

3. **Automatic `Cargo.toml` generation**
   - `pytra-cli2.py -build --target rs` generates `Cargo.toml`
   - Configure edition and dependencies (standard library only)

### Impact on Other Languages

This problem is not Rust-specific. Looking ahead:

- **Java**: 1 module = 1 package (already emitting `package` statements)
- **C#**: 1 module = 1 namespace
- **Go**: 1 module = 1 package (Go already works with package separation)

By giving CommonRenderer / ProgramWriter a shared concept of "1 module = 1 target-language namespace unit", each language's emitter only needs to provide the namespace syntax. However, this task targets Rust only; commonalization is a separate task.

## Comparison with the Prefix Hack

| Aspect | Prefix hack (`CsEmitContext`) | mod structure |
|---|---|---|
| Type names | Diverge from Python | Match Python |
| selfhost meaning | Undermined (same code doesn't run) | Preserved |
| Name collisions | Avoided manually (risk of gaps) | Resolved at language level |
| `cargo build` | Depends on `include!`, no dependency analysis | Works naturally |
| Future extensibility | Technical debt grows | Standard approach |

## Implementation Order

1. Add a mod structure output mode to the Rust emitter's multifile_writer
2. Implement automatic generation of `lib.rs` / `Cargo.toml`
3. Implement emission of cross-module `use crate::` paths
4. Switch `pytra-cli2.py -build --target rs` to use the mod structure
5. Confirm that the selfhost build (`cargo build`) succeeds
6. Confirm parity with `run_selfhost_parity.py --selfhost-lang rs`
