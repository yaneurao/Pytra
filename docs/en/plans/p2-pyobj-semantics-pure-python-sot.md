<a href="../../ja/plans/p2-pyobj-semantics-pure-python-sot.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2 draft: move `PyObj` semantics back toward a pure-Python SoT

Last updated: 2026-03-14

Related TODO:
- none (backlog draft / not yet promoted)

Related:
- [p2-runtime-sot-linked-program-integration.md](./p2-runtime-sot-linked-program-integration.md)
- [p2-runtime-helper-generics-under-linked-program.md](./p2-runtime-helper-generics-under-linked-program.md)
- [p2-cpp-pyruntime-upstream-fallback-shrink.md](./p2-cpp-pyruntime-upstream-fallback-shrink.md)

Notes:

- This document is an unscheduled design memo and is not being promoted into `docs/ja/todo/index.md` yet.
- Its purpose is to pin down the blockers and a realistic split if we want to push `PyObj` and its derived classes closer to a pure-Python SoT.
- It does not assume that we should immediately recreate the full `PyObj` class hierarchy as pure-Python classes.

Background:
- In the current C++ runtime, the `PyObj` base lives in [gc.h](../../src/runtime/cpp/native/core/gc.h) and acts as a native ABI core that includes `RcObject`, `RcHandle<T>`, virtual dispatch, and type IDs.
- `PyIntObj`, `PyFloatObj`, `PyBoolObj`, `PyStrObj`, `PyListObj`, `PyDictObj`, `PySetObj`, and the iterator objects live as handwritten classes in [py_runtime.h](../../src/runtime/cpp/native/core/py_runtime.h).
- At the same time, the long-term runtime direction is to expand the pure-Python SoT. However, [generated/core/README.md](../../src/runtime/cpp/generated/core/README.md) explicitly forbids pushing C++-specific ownership/ABI glue such as `gc`, object/container representation, RC/GC, and exception/I/O aggregation into `generated/core`.
- Because of that, any attempt to "pure-Python-ize `PyObj`" will fail unless we first separate leaf semantics from the native ABI core.

Objective:
- Clarify which parts of the `PyObj` area can move back into a pure-Python SoT and which parts should remain as native ABI core.
- Define a staged plan that starts with semantics such as `truthy`, `len`, `str`, and iterator behavior instead of trying to port the entire class hierarchy.
- Make the prerequisites explicit for how far `PyListObj` / `PyDictObj` and iterator-style objects could move once linked runtime integration and helper-limited generics exist.

In scope:
- `src/runtime/cpp/native/core/gc.h`
- `src/runtime/cpp/native/core/py_types.h`
- `Py*Obj` and iterator classes inside `src/runtime/cpp/native/core/py_runtime.h`
- the boundary between `generated/core`, linked runtime, and helper generics

Out of scope:
- implementing this right now
- turning `RcHandle<T>`, `RcObject`, or `PyObj` themselves into pure-Python classes
- user-facing generic classes or class templates
- applying the same shift to Rust/C#/other backends all at once

Acceptance criteria (for a future implementation):
- the split between native ABI core and semantics that can move into a pure-Python SoT is explicit
- leaf semantics such as `PyIntObj`, `PyFloatObj`, `PyBoolObj`, and `PyStrObj` can be expressed as generated helpers instead of handwritten class logic
- blockers versus linked-runtime/generics dependencies are explicit for `PyListObj`, `PyDictObj`, and iterator-style objects
- the boundary stays compatible with the rule that `generated/core` must not become a bloat bucket

## 1. Conclusion

As of 2026-03-14, the realistic direction is not to regenerate the full `PyObj` class hierarchy as pure-Python classes.  
The first viable split is:

- keep native:
  - `RcObject`
  - `RcHandle<T>`
  - `PyObj`
  - type-ID registry, subtype checks, and low-level ownership
- move toward pure-Python SoT:
  - truthy/str/len/iter semantics for `PyIntObj`, `PyFloatObj`, `PyBoolObj`, `PyStrObj`
  - later, selected container/iterator helper semantics

In short, the first step is not "move the classes," but "move the class semantics and leave native classes as thin shells."

## 2. What blocks this

### 2.1 Native ABI core

The `PyObj` base is not just a Python object model. It is a C++ ABI core with refcounting and virtual dispatch.

- `RcObject` owns an atomic refcount
- `RcHandle<T>` owns copy/move/adopt/upcast behavior
- `PyObj` owns virtual `py_truthy`, `py_try_len`, `py_iter_or_raise`, `py_next_or_stop`, and `py_str`

That layer belongs to [gc.h](../../src/runtime/cpp/native/core/gc.h) and is not a direct pure-Python SoT target.

### 2.2 Template/generic dependency

The basic runtime representation depends on templates such as `object = rc<PyObj>`, `rc<list<T>>`, `dict<K, V>`, and `set<T>`.  
Even the current linked-runtime generic draft only targets helper-limited generic functions at first, not generic classes.[p2-runtime-helper-generics-under-linked-program.md](./p2-runtime-helper-generics-under-linked-program.md)

So it is too early to model something like `class PyListObj[T]` directly in a pure-Python SoT.

### 2.3 RTTI and C++-specific mechanisms

Objects such as `PyListIterObj` depend on `dynamic_cast`, function-local statics, and macros such as `PYTRA_DECLARE_CLASS_TYPE`.  
Those are poor fits for direct Python-AST-to-C++ regeneration and are more naturally treated as native companions.

### 2.4 The `generated/core` boundary

[generated/core/README.md](../../src/runtime/cpp/generated/core/README.md) explicitly says that `gc`, object/container representation, RC/GC, and exception/I/O aggregation do not belong in `generated/core`.  
So "move the whole `PyObj` hierarchy into generated/core because we want a pure-Python SoT" would break that boundary.

### 2.5 Linked runtime integration is not here yet

Runtime SoT is still mainly handled as pre-generated artifacts.  
The long-term architecture is to load runtime SoT into the linked program as ordinary modules, but that path is still only a draft.[p2-runtime-sot-linked-program-integration.md](./p2-runtime-sot-linked-program-integration.md)

Without that, even SoT-ized helpers are still likely to look like fixed generated artifacts with ABI boundaries, which limits the payoff.

## 3. Recommended architecture

### 3.1 Native shell plus generated semantics

The recommended first stage is:

- keep the native classes
- make each class a thin shell
- delegate `truthy`, `str`, `len`, `iter`, and similar semantics to generated helpers

Conceptually:

```cpp
class PyIntObj : public PyObj {
public:
    explicit PyIntObj(int64 v) : PyObj(PYTRA_TID_INT), value(v) {}
    int64 value;

    bool py_truthy() const override { return pyobj_semantics::int_truthy(value); }
    ::std::string py_str() const override { return pyobj_semantics::int_str(value); }
};
```

Here, `pyobj_semantics::*` would be low-level helpers generated from a pure-Python SoT.

### 3.2 Use function-level SoT, not class-level SoT

If we try to recreate `PyIntObj` itself as a pure-Python class too early, inheritance, virtual layout, ownership, and native metadata become immediate problems.  
So the SoT side should start as functions rather than classes:

```python
def py_int_truthy(v: int) -> bool:
    return v != 0

def py_int_str(v: int) -> str:
    return str(v)

def py_str_truthy(s: str) -> bool:
    return len(s) != 0

def py_str_len(s: str) -> int:
    return len(s)
```

That granularity is much easier to push into a SoT without dragging in class generics or native layout.

## 4. What can move first

### 4.1 Easier first targets

- `PyIntObj`
- `PyFloatObj`
- `PyBoolObj`
- `PyStrObj` truthy/len/str behavior

These have simple value fields and can be rewritten into helper calls relatively cleanly.

### 4.2 Still-heavy targets

- `PyListObj`
- `PyDictObj`
- `PySetObj`
- `PyListIterObj`
- `PyDictKeyIterObj`
- `PyStrIterObj`

Reasons:

- they depend on container ownership like `list<object>` / `dict<str, object>` / `set<object>`
- iterators rely on `object` handles plus `dynamic_cast`
- without helper generics, it is awkward to write natural `list[T]` / `dict[K, V]` semantics in the SoT

## 5. What changes once linked runtime and helper generics exist

In the long run, linked runtime integration plus helper-limited generics would make container-style SoT extraction much more realistic.

- runtime helpers could enter the ordinary call graph
- `list[T]`, `dict[K, V]`, and `tuple[T, U]` helpers become natural to write in pure Python
- `object` fallback can shrink
- collection helpers still living in `py_runtime.h` become easier to move back into the SoT

Even then, though, it is still natural to leave `RcObject`, `RcHandle<T>`, and `PyObj` themselves in the native ABI core.

## 6. A staged rollout

### Phase 1: design only

- freeze the split between `native ABI core` and `semantic helpers` in spec/plan form
- inventory candidate leaf semantics

### Phase 2: scalar/string leaf extraction

- move truthy/str/len behavior for `PyIntObj`, `PyFloatObj`, `PyBoolObj`, and `PyStrObj` into pure-Python SoT helpers
- reduce the native classes to thin shells

### Phase 3: iterator/container helper draft

- test SoT-ization feasibility on simpler iterator semantics such as `PyStrIterObj`
- keep `PyListObj` / `PyDictObj` blocked until helper-limited generics are available

### Phase 4: re-evaluate after linked runtime integration

- once linked runtime integration and helper generics exist, re-evaluate container/iterator SoT extraction
- decide whether the meaning layer and the ownership/ABI layer can be separated further

## 7. Decision criteria

Something is easier to move into a pure-Python SoT when:

- it does not need native layout knowledge
- it does not require generic classes/templates

Something should probably stay native when:

- it directly owns refcount/ownership behavior
- it depends on `dynamic_cast` or virtual layout
- it uses function-local statics or macros for class metadata
- it would violate the `generated/core` boundary

Decision log:
- 2026-03-14: After reviewing the idea of regenerating `PyObj` and its derived classes from pure Python, the main blocker was identified as the native ABI core around `RcObject/RcHandle/PyObj`, not the leaf semantics themselves.
- 2026-03-14: The preferred first step was fixed as "move leaf semantics into pure-Python SoT helpers and keep native classes as thin shells" rather than "make the classes themselves pure Python."
