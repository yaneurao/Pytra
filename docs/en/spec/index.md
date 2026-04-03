<a href="../../ja/spec/index.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Specification Entry Point

### For Users

| Topic | Link | Description |
|---|---|---|
| Usage specification | [spec-user.md](./spec-user.md) | How to use, input constraints, how to run tests |
| Python compatibility | [spec-python-compat.md](./spec-python-compat.md) | Differences from Python, unsupported syntax |
| pylib modules | [spec-pylib-modules.md](./spec-pylib-modules.md) | List of available modules and functions |

### Language Specification

| Topic | Link | Description |
|---|---|---|
| Type system / type_id | [spec-type_id.md](./spec-type_id.md) | Single inheritance, isinstance, POD exact match |
| tagged union | [spec-tagged-union.md](./spec-tagged-union.md) | `type X = A \| B` declaration and code generation |
| ADT | [spec-adt.md](./spec-adt.md) | Union type lowering strategy per language, enum/variant/sealed class |
| Trait | [spec-trait.md](./spec-trait.md) | `@trait` / `@implements`, pure interface |
| Exception handling | [spec-exception.md](./spec-exception.md) | raise/try/except, native_throw and union_return |
| Boxing/Unboxing | [spec-boxing.md](./spec-boxing.md) | Type conversion at Any/object boundaries |
| Object\<T\> | [spec-object.md](./spec-object.md) | Design specification for the reference-type wrapper |
| import | [spec-import.md](./spec-import.md) | Import resolution rules |
| Built-in functions | [spec-builtin-functions.md](./spec-builtin-functions.md) | Built-in function declaration specification |
| @template | [spec-template.md](./spec-template.md) | Template (generics) specification |
| Iterable/Iterator | [spec-iterable.md](./spec-iterable.md) | for-loop iteration contract, dynamic protocol |
| @runtime / @extern | [spec-runtime-decorator.md](./spec-runtime-decorator.md) | Specification for `@runtime` and `@extern`, auto-derivation rules, argument passing |
| Opaque types | [spec-opaque-type.md](./spec-opaque-type.md) | Type contract for `@extern class` (no rc, no boxing) |
| GC | [spec-gc.md](./spec-gc.md) | RC-based GC policy |

### EAST (Intermediate Representation)

| Topic | Link | Description |
|---|---|---|
| EAST unified spec | [spec-east.md](./spec-east.md) | Current canonical document. Type inference, node spec, narrowing |
| EAST1 | [spec-east1.md](./spec-east1.md) | Parse output contract (types unresolved) |
| EAST2 | [spec-east2.md](./spec-east2.md) | Resolve output contract (types finalized) |
| EAST3 Optimizer | [spec-east3-optimizer.md](./spec-east3-optimizer.md) | Optimization pass responsibilities and contracts |
| Linker | [spec-linker.md](./spec-linker.md) | Multi-module linking, type_id finalization |

### Backend / Emitter

| Topic | Link | Description |
|---|---|---|
| Emitter guidelines | [spec-emitter-guide.md](./spec-emitter-guide.md) | Contracts and prohibitions common to all emitters |
| Language profile | [spec-language-profile.md](./spec-language-profile.md) | Lowering profile, CommonRenderer |
| runtime mapping | [spec-runtime-mapping.md](./spec-runtime-mapping.md) | mapping.json format |
| Runtime | [spec-runtime.md](./spec-runtime.md) | Runtime layout, include conventions |

### For Developers

| Topic | Link | Description |
|---|---|---|
| Development environment setup | [spec-setup.md](./spec-setup.md) | Steps to generate golden / runtime east immediately after cloning |
| Implementation specification | [spec-dev.md](./spec-dev.md) | Implementation policy, module structure |
| Folder responsibilities | [spec-folder.md](./spec-folder.md) | What goes where |
| stdlib canonicalization | [spec-stdlib-signature-source-of-truth.md](./spec-stdlib-signature-source-of-truth.md) | Contract making pytra/std the canonical source for type specifications |
| tools index | [spec-tools.md](./spec-tools.md) | List of tools/ scripts and their purposes |
| AI agent operations | [spec-agent.md](./spec-agent.md) | Codex / Claude Code work rules, TODO workflow |
| Design philosophy | [spec-philosophy.md](./spec-philosophy.md) | Background on the EAST-centric design |
| Archived specs | [archive/index.md](./archive/index.md) | Archive of retired specifications |

## AI Agent Startup Checklist

- On startup, AI agents (Codex / Claude Code) should read `docs/ja/spec/index.md` as the entry point, then review the [AI agent operations spec](./spec-agent.md) and [TODO](../todo/index.md).
