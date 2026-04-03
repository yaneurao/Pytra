<a href="../../ja/plans/p3-trait-pure-interface.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P3-TRAIT: Introducing Trait (pure interface / multiple implementation)

Last updated: 2026-03-27
Status: Complete

## Background

Pytra supports only single inheritance, and there is no mechanism to attach behavioral contracts — such as "can draw" or "can serialize" — across multiple classes. We introduce a mechanism equivalent to Rust traits, Java interfaces, and Swift protocols.

## Design decisions

### Pure interface (no default implementations)

Traits hold only method signatures and do not have default implementations in v1. Reason: Go interfaces cannot have method bodies, and mapping default implementations to Go would require auto-generating delegation methods, significantly increasing emitter complexity.

### Nominal

Trait implementation must be declared explicitly with the `@implements` decorator. Structural subtyping (automatically treating a class as an implementor if it satisfies the methods) is not adopted. Reason: the majority of target languages (Java, C#, Kotlin, Rust, Swift) are nominal; only Go is structural. For Go, the emitter can simply omit `@implements` in its output.

### Separated from type_id

Traits do not have a `type_id`. `isinstance` for a trait is evaluated using a `trait_id` bitset. This does not affect the single-inheritance `type_id` interval-judgment tree.

### C++ Object<T> conversion constructor

In C++, traits are multiply-inherited as pure virtual classes, and a template conversion constructor is added to `Object<T>` to enable implicit upcasting from `Object<Circle>` to `Object<Drawable>`.

## Subtasks

1. [ID: P3-TRAIT-S1] parser recognizes `@trait` / `@implements` decorators and retains them in EAST1
2. [ID: P3-TRAIT-S2] resolve verifies trait implementation completeness (checks that all methods are implemented, signatures match)
3. [ID: P3-TRAIT-S3] attach `meta.trait_v1` / `meta.implements_v1` in EAST3
4. [ID: P3-TRAIT-S4] linker finalizes `trait_id` bitsets
5. [ID: P3-TRAIT-S5] `isinstance(x, Trait)` is converted to a `trait_id`-based instruction in EAST3
6. [ID: P3-TRAIT-S6] add conversion constructor to C++ `Object<T>` to realize trait upcasting
7. [ID: P3-TRAIT-S7] implement trait mapping in the C++ emitter (virtual inheritance + Object<T> conversion constructor + override)
8. [ID: P3-TRAIT-S8] implement trait mapping in the Go emitter (interface generation, structural satisfaction)
9. [ID: P3-TRAIT-S9] add trait fixtures to `test/fixture/source/py/oop/` (trait definition, multiple implementation, upcast, isinstance) + generate goldens (east1/east2/east3/east3-opt/linked) + confirm C++/Go parity

## Completion notes

- The parser retains class decorators in EAST1, passing `@trait` / `@implements(...)` through losslessly.
- Resolve handles pure interface constraints in trait bodies, trait inheritance, `@implements` completeness verification, and attaching `meta.trait_v1` / `meta.implements_v1` / `meta.trait_impl_v1`.
- The linker excludes traits from the `type_id` tree and statically resolves only trait implementation relationships. `isinstance(x, Trait)` is folded into a `bool` constant at link time; no runtime trait metadata is generated.
- C++ maps traits to pure virtual classes + `virtual public` inheritance + `override`, handled with ordinary Object<T> upcasting. No runtime trait bitset is maintained.
- Go maps traits to interfaces, and trait inheritance is mapped to interface embedding. Trait `isinstance` does not survive past link time.
- Added fixture `test/fixture/source/py/oop/trait_basic.py` and regenerated goldens. Both `python3 tools/check/runtime_parity_check.py --targets go --cmd-timeout-sec 60 trait_basic` and `--targets cpp` pass.

The target backends for v1 are limited to **C++ and Go**. Reason: covering both extremes with C++ (virtual inheritance) and Go (structural interface) is sufficient to validate the design. Other languages will be addressed in a separate task after v1 is complete.

## Acceptance Criteria

1. A pure interface can be defined with `@trait`
2. Multiple traits can be implemented with `@implements`, and a compile error is raised if any method is unimplemented
3. An implementing class can be passed as a trait-typed argument (implicit upcast)
4. `isinstance(x, Trait)` evaluates correctly
5. Parity passes for major languages including C++, Go, Rust, and Java
6. The single-inheritance `type_id` tree is not affected

## Decision Log

- 2026-03-27: Discussed trait design. Decided on pure interface (no default implementations), nominal, with `@trait` + `@implements` decorator approach. v1 is limited to pure interfaces to avoid the Go default implementation problem. For C++, trait upcasting is realized via a conversion constructor on `Object<T>`.
