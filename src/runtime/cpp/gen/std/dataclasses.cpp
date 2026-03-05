// AUTO-GENERATED FILE. DO NOT EDIT.
// source: src/pytra/std/dataclasses.py
// generated-by: src/backends/cpp/cli.py
#include "runtime/cpp/core/built_in/py_runtime.h"

#include "runtime/cpp/gen/std/dataclasses.h"

#include "runtime/cpp/core/std/dataclasses-impl.h"
#include "runtime/cpp/gen/std/typing.h"

namespace pytra::std::dataclasses {

    object dataclass(const object& _cls, bool init = true, bool repr = true, bool eq = true) {
        /* `@dataclass` の最小互換入口。実装本体は dataclasses_impl 側。 */
        return make_object(pytra::std::dataclasses_impl::dataclass(_cls, init, repr, eq));
    }
    
    static void __pytra_module_init() {
        static bool __initialized = false;
        if (__initialized) return;
        __initialized = true;
        /* pytra.std.dataclasses: thin wrapper over dataclasses_impl. */
    }
    
    namespace {
        struct __pytra_module_initializer {
            __pytra_module_initializer() { __pytra_module_init(); }
        };
        static const __pytra_module_initializer __pytra_module_initializer_instance{};
    }  // namespace
    
}  // namespace pytra::std::dataclasses
