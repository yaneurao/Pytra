// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/typing.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/typing.h"


namespace pytra::std::typing {

    str Any;
    str List;
    str Set;
    str Dict;
    str Tuple;
    str Iterable;
    str Sequence;
    str Mapping;
    str Optional;
    str Union;
    str Callable;
    str TypeAlias;
    
    str TypeVar(const str& name) {
        return name;
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* Minimal typing shim for selfhost-friendly imports.

This module is intentionally small and runtime-light. It provides names used in
type annotations so core modules avoid direct stdlib `typing` imports.
 */
        Any = "Any";
        List = "List";
        Set = "Set";
        Dict = "Dict";
        Tuple = "Tuple";
        Iterable = "Iterable";
        Sequence = "Sequence";
        Mapping = "Mapping";
        Optional = "Optional";
        Union = "Union";
        Callable = "Callable";
        TypeAlias = "TypeAlias";
    }
    
    namespace {
        struct __pytra_module_initializer {
            __pytra_module_initializer() { __pytra_module_init(); }
        };
        static const __pytra_module_initializer __pytra_module_initializer_instance{};
    }  // namespace
    
}  // namespace pytra::std::typing
