// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/typing.py
// generated-by: src/py2cpp.py

#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/typing.h"


namespace pytra::std::typing {

    /* Minimal typing shim for selfhost-friendly imports.

This module is intentionally small and runtime-light. It provides names used in
type annotations so core modules avoid direct stdlib `typing` imports.
 */
    
    
    str Any = "Any";
    
    str List = "List";
    
    str Set = "Set";
    
    str Dict = "Dict";
    
    str Tuple = "Tuple";
    
    str Iterable = "Iterable";
    
    str Sequence = "Sequence";
    
    str Mapping = "Mapping";
    
    str Optional = "Optional";
    
    str Union = "Union";
    
    str Callable = "Callable";
    
    str TypeAlias = "TypeAlias";
    
    str TypeVar(const str& name) {
        return name;
    }
    
}  // namespace pytra::std::typing
