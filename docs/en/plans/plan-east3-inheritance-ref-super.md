# Plan: Consistent ref semantics for inherited classes + super() resolution in EAST3 (P0-EAST3-INHERIT)

## Background

The `inheritance_virtual_dispatch_multilang` fixture causes the Rust emitter to produce a conflict between `Rc<RefCell<LoudDog>>` and `Box<dyn AnimalMethods>`. The root cause is in EAST3 lowering.

### Problem 1: The base class in an inheritance hierarchy gets `class_storage_hint: "value"`

Current EAST3 state:

| Class | base | class_storage_hint |
|---|---|---|
| `Animal` | (none) | `"value"` |
| `Dog` | `Animal` | `"ref"` |
| `LoudDog` | `Dog` | `"ref"` |

If `Dog` inherits from `Animal` and becomes `ref`, then `Animal` must also be `ref`; otherwise the type semantics are inconsistent. With `a: Animal = LoudDog()`, value/ref semantics clash.

In C++, types with a vtable pointer cannot be values (slicing problem). Go uses interfaces for implicit ref. Rust uses `Box<dyn Trait>` for ref. In all these languages, base classes that participate in an inheritance hierarchy require reference semantics.

### Problem 2: `super()` remains unresolved in EAST3

For `super().speak()` inside `LoudDog.speak`:

- `super()`'s `resolved_type` is `"unknown"`
- `super().speak()`'s `resolved_type` is also `"unknown"`
- The emitter cannot know the return type and collapses to `Box<dyn Any>`

`super()` can be resolved statically: `super()` for `LoudDog` is `Dog`, and `Dog.speak()`'s return type is `str`. This should be finalized in EAST3.

## Design

### Fix for Problem 1

In EAST3 lowering (the `class_storage_hint` determination logic), **also promote base classes that have derived classes to `ref`**:

1. Collect all class definitions
2. Walk inheritance relationships and promote any base class with at least one derived class to `ref`
3. Apply transitively (if A ← B ← C, then both A and B become `ref`)

This unifies the entire inheritance hierarchy under `ref`, allowing the emitter to handle them consistently with `Rc<RefCell<T>>` / `shared_ptr<T>` / interface.

### Fix for Problem 2

In EAST3 lowering (or EAST2 resolve), resolve `super()`:

1. Detect `Call(Name("super"))`
2. Look up `base` of the current class and finalize the type of super
3. Set the receiver type on the `Attribute` node of `super().method()` to the base class
4. Resolve the method's return type from the base class's method definition

Add the following to the `super()` Call node in EAST3:
- `resolved_type`: base class name (e.g. `"Dog"`)
- `resolved_type` of the chained method call: method return type

## Impact

- May affect all fixtures that use inheritance
- C++ already operates vtable-based, so ref promotion is natural
- Go is unaffected (uses interfaces)
- Rust enables unification of `Box<dyn Trait>` / `Rc`
- Full parity check across all languages for fixture + sample is required

## Implementation Order

1. Promote `class_storage_hint` of inherited base classes to `ref` in EAST3 lowering
2. Resolve the type of `super()` in EAST3 lowering (or EAST2 resolve)
3. Confirm no regressions in all-language fixture parity
4. Confirm that `inheritance_virtual_dispatch_multilang` passes compile + run parity in Rust
