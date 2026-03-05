// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/toolchain/compiler/east_parts/core.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/compiler/east_parts/core.h"


namespace pytra::compiler::east_parts::core {

    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* Compatibility shim for EAST parser core.

Canonical implementation moved to ``toolchain.ir.core``.
 */
    }
    
    namespace {
        struct __pytra_module_initializer {
            __pytra_module_initializer() { __pytra_module_init(); }
        };
        static const __pytra_module_initializer __pytra_module_initializer_instance{};
    }  // namespace
    
}  // namespace pytra::compiler::east_parts::core
