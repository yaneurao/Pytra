// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/traceback.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/traceback.h"


namespace pytra::std::traceback {

    list<str> _last_exc_text_box;
    list<str> __all__;
    
    str format_exc() {
        /* Return last captured traceback text.

    Current minimal implementation returns an empty string when unavailable.
     */
        return py_at(_last_exc_text_box, py_to<int64>(0));
    }
    
    void _set_last_exc_text(const str& text) {
        /* Runtime hook: update stored traceback string. */
        py_set_at(_last_exc_text_box, 0, make_object(text));
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* pytra.std.traceback compatibility shim. */
        _last_exc_text_box = list<str>{""};
        __all__ = list<str>{"format_exc"};
    }
    
    namespace {
        struct __pytra_module_initializer {
            __pytra_module_initializer() { __pytra_module_init(); }
        };
        static const __pytra_module_initializer __pytra_module_initializer_instance{};
    }  // namespace
    
}  // namespace pytra::std::traceback
