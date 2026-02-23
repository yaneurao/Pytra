// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/traceback.py
// generated-by: src/py2cpp.py

#include "runtime/cpp/pytra/built_in/py_runtime.h"

#include "pytra/std/traceback.h"


namespace pytra::std::traceback {

    /* pytra.std.traceback compatibility shim. */
    
    
    list<str> _last_exc_text_box = list<str>{""};
    
    str format_exc() {
        /* Return last captured traceback text.

    Current minimal implementation returns an empty string when unavailable.
     */
        return py_at(_last_exc_text_box, py_to_int64(0));
    }
    
    void _set_last_exc_text(const str& text) {
        /* Runtime hook: update stored traceback string. */
        _last_exc_text_box[0] = text;
    }
    
    list<str> __all__ = list<str>{"format_exc"};
    
}  // namespace pytra::std::traceback
